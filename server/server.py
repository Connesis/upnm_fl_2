"""
Flower server implementation for federated learning.
"""
import flwr as fl
import argparse
import sys
import os
import joblib
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional
from collections import OrderedDict
import numpy as np
import logging

# Add the client utils to the path so we can import federated utilities
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'client'))
from utils.federated_utils import (
    aggregate_random_forests,
    numpy_arrays_to_trees,
    trees_to_numpy_arrays,
    deserialize_random_forest
)

# Add the ICP client
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from icp_auth_client import AuthenticatedICPClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CVDFedAvgStrategy(fl.server.strategy.FedAvg):
    """Custom FedAvg strategy for Random Forest federated learning with ICP integration."""

    def __init__(self, *args, **kwargs):
        """Initialize the strategy."""
        super().__init__(*args, **kwargs)
        logger.info("Initializing CVDFedAvgStrategy for Random Forest")

        # Initialize authenticated ICP client with server role
        try:
            self.icp_client = AuthenticatedICPClient(identity_type="server")
            if self.icp_client.canister_id:
                logger.info(f"Connected to ICP canister: {self.icp_client.canister_id}")
                logger.info("Server initialized with authenticated ICP connection")
            else:
                logger.warning("Could not connect to ICP canister")
                self.icp_client = None
        except Exception as e:
            logger.error(f"Failed to initialize ICP client: {e}")
            self.icp_client = None

    def aggregate_fit(
        self,
        server_round: int,
        results: List[Tuple[fl.server.client_proxy.ClientProxy, fl.common.FitRes]],
        failures: List[Tuple[fl.server.client_proxy.ClientProxy, fl.common.FitRes] | BaseException],
    ) -> Tuple[Optional[fl.common.Parameters], Dict[str, fl.common.Scalar]]:
        """
        Aggregate fit results using Random Forest tree combination.

        Args:
            server_round: Current server round
            results: List of fit results from clients
            failures: List of failures

        Returns:
            Aggregated parameters and metrics
        """
        if not results:
            return None, {}

        logger.info(f"Aggregating fit results from {len(results)} clients in round {server_round}")

        # Extract parameters and weights
        client_trees_list = []
        weights = []

        for client_proxy, fit_res in results:
            # Extract parameters (should be [tree_array])
            parameters = fl.common.parameters_to_ndarrays(fit_res.parameters)

            if len(parameters) >= 1 and len(parameters[0]) > 0:
                # Convert numpy array back to serialized trees
                tree_array = parameters[0]
                serialized_trees = numpy_arrays_to_trees(tree_array)
                client_trees_list.append(serialized_trees)
                weights.append(fit_res.num_examples)
                logger.info(f"Client contributed {len(serialized_trees)} trees")
            else:
                logger.warning(f"Client {client_proxy} provided empty parameters")

        if not client_trees_list:
            logger.warning("No valid parameters received from clients")
            return None, {}

        # Aggregate trees from all clients
        aggregated_trees = aggregate_random_forests(client_trees_list, weights)
        logger.info(f"Aggregated model contains {len(aggregated_trees)} trees")

        # Convert back to numpy array format
        aggregated_tree_array = trees_to_numpy_arrays(aggregated_trees)

        # Package parameters
        aggregated_parameters = [aggregated_tree_array]

        # Convert to Flower parameters format
        parameters = fl.common.ndarrays_to_parameters(aggregated_parameters)

        # Aggregate metrics
        total_examples = sum(weights)
        metrics = {
            'num_clients': len(results),
            'total_examples': total_examples,
            'num_trees': len(aggregated_trees)
        }

        logger.info(f"Aggregation completed: {len(aggregated_trees)} trees from {len(results)} clients")

        # Save the aggregated model
        metadata = {
            'n_estimators': len(aggregated_trees),
            'n_classes': 2,
            'n_features': 12,  # Based on our preprocessing
            'classes': [0, 1],
            'total_examples': total_examples,
            'num_clients': len(client_trees_list)
        }
        model_path, metadata_path = self._save_global_model(aggregated_trees, server_round, metadata)

        # Store training round completion on ICP blockchain
        if self.icp_client:
            try:
                # Get participant IDs (simplified - using dummy IDs for now)
                participant_ids = [f"client_{i}" for i in range(len(results))]

                # Calculate accuracy (simplified - using dummy value for now)
                accuracy = 0.85  # TODO: Calculate actual accuracy from evaluation

                success = self.icp_client.complete_training_round(
                    round_id=server_round,
                    participants=participant_ids,
                    total_examples=total_examples,
                    num_trees=len(aggregated_trees),
                    accuracy=accuracy,
                    model_path=model_path
                )

                if success:
                    logger.info(f"Training round {server_round} metadata stored on ICP blockchain")
                else:
                    logger.warning(f"Failed to store training round {server_round} metadata on ICP")

            except Exception as e:
                logger.error(f"Error storing training round metadata on ICP: {e}")

        # Output the generated artifact file names
        print("\n" + "="*80)
        print(f"🎯 ROUND {server_round} COMPLETED SUCCESSFULLY!")
        print("="*80)
        print(f"📊 Aggregation Summary:")
        print(f"   • Participating clients: {len(results)}")
        print(f"   • Total trees aggregated: {len(aggregated_trees)}")
        print(f"   • Total training examples: {total_examples:,}")
        print(f"   • Trees per client: {len(aggregated_trees) // len(results)}")
        print(f"\n📁 Generated Artifacts:")
        print(f"   • Global Model: {model_path}")
        print(f"   • Model Metadata: {metadata_path}")
        print("="*80 + "\n")

        return parameters, metrics

    def _save_global_model(self, serialized_trees: List[bytes], round_num: int, metadata: Dict[str, Any]) -> Tuple[str, str]:
        """
        Save the global federated model to disk.

        Args:
            serialized_trees: List of serialized decision trees
            round_num: Current round number
            metadata: Model metadata

        Returns:
            Tuple of (model_path, metadata_path)
        """
        try:
            # Create models directory if it doesn't exist
            models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
            os.makedirs(models_dir, exist_ok=True)

            # Reconstruct the Random Forest model
            global_model = deserialize_random_forest(serialized_trees, n_classes=2)

            # Save the model
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_filename = f"federated_cvd_model_round_{round_num}_{timestamp}.joblib"
            model_path = os.path.join(models_dir, model_filename)

            joblib.dump(global_model, model_path)

            # Save metadata
            metadata_filename = f"federated_cvd_metadata_round_{round_num}_{timestamp}.joblib"
            metadata_path = os.path.join(models_dir, metadata_filename)
            joblib.dump(metadata, metadata_path)

            logger.info(f"Global model saved to {model_path}")
            logger.info(f"Model metadata saved to {metadata_path}")

            return model_path, metadata_path

        except Exception as e:
            logger.error(f"Failed to save global model: {e}")
            return "", ""


def fit_config(server_round: int) -> Dict[str, Any]:
    """
    Return training configuration dict for each round.
    
    Args:
        server_round: Current server round
        
    Returns:
        Configuration dictionary
    """
    logger.info(f"Configuring fit for round {server_round}")
    config = {
        "server_round": server_round,
        "local_epochs": 1,
    }
    return config


def evaluate_config(server_round: int) -> Dict[str, Any]:
    """
    Return evaluation configuration dict for each round.
    
    Args:
        server_round: Current server round
        
    Returns:
        Configuration dictionary
    """
    logger.info(f"Configuring evaluation for round {server_round}")
    config = {
        "server_round": server_round,
    }
    return config


def main(num_rounds: int) -> None:
    """
    Main function to run the server.

    Args:
        num_rounds: Number of federated learning rounds
    """
    # Print startup banner
    print("\n" + "="*80)
    print("🚀 FEDERATED LEARNING SERVER FOR CVD PREDICTION")
    print("="*80)
    print(f"📋 Configuration:")
    print(f"   • Number of rounds: {num_rounds}")
    print(f"   • Server address: 0.0.0.0:8080")
    print(f"   • Model type: Random Forest (scikit-learn)")
    print(f"   • Aggregation strategy: FedAvg with tree combination")
    print(f"   • Model storage: ./models/")
    print("="*80)
    print("⏳ Waiting for clients to connect...")
    print("="*80 + "\n")

    logger.info(f"Starting server with {num_rounds} rounds")

    # Create custom strategy for Random Forest federated learning
    strategy = CVDFedAvgStrategy(
        fraction_fit=1.0,  # Sample all clients for training
        fraction_evaluate=1.0,  # Sample all clients for evaluation
        min_fit_clients=1,  # Minimum number of clients for training
        min_evaluate_clients=1,  # Minimum number of clients for evaluation
        min_available_clients=1,  # Minimum number of available clients
        on_fit_config_fn=fit_config,  # Function to configure training
        on_evaluate_config_fn=evaluate_config,  # Function to configure evaluation
    )

    logger.info("Server strategy configured")
    logger.info("Starting Flower server...")

    # Start server
    fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=fl.server.ServerConfig(num_rounds=num_rounds),
        strategy=strategy,
    )

    # Print completion banner
    print("\n" + "="*80)
    print("✅ FEDERATED LEARNING COMPLETED SUCCESSFULLY!")
    print("="*80)
    print("📁 All generated models and metadata are saved in the './models/' directory")
    print("🔍 Use 'test_federated_model.py' to test the latest federated model")
    print("="*80 + "\n")

    logger.info("Server finished")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Federated Learning Server for CVD Prediction")
    parser.add_argument("--rounds", type=int, default=5, help="Number of federated learning rounds")
    
    args = parser.parse_args()
    
    main(args.rounds)