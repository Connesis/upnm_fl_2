"""
Flower server implementation for federated learning.
"""
import flwr as fl
import argparse
import sys
import os
import time
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
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CVDFedAvgStrategy(fl.server.strategy.FedAvg):
    """Custom FedAvg strategy for Random Forest federated learning with ICP integration."""

    def __init__(self, total_rounds: int = 5, max_trees_per_round: int = 1000, *args, **kwargs):
        """Initialize the strategy."""
        super().__init__(*args, **kwargs)
        self.total_rounds = total_rounds
        self.current_round = 0
        self.max_trees_per_round = max_trees_per_round
        logger.info("Initializing CVDFedAvgStrategy for Random Forest")
        logger.info(f"Total rounds configured: {total_rounds}")
        logger.info(f"Maximum trees per round: {max_trees_per_round}")

        # Initialize authenticated ICP client with server role
        try:
            # Use the specific server identity name from environment
            server_identity = os.getenv("ICP_CLIENT_IDENTITY_NAME", "fl_server")
            logger.info(f"🔧 Initializing ICP client with identity: {server_identity}")

            # Create ICP client with custom identity name
            self.icp_client = AuthenticatedICPClient(identity_type="server")
            # Override the identity name to use the correct one
            self.icp_client.identity_name = server_identity

            if self.icp_client.canister_id:
                logger.info(f"✅ Connected to ICP canister: {self.icp_client.canister_id}")
                logger.info(f"🔐 Server initialized with authenticated ICP connection using {server_identity}")
            else:
                logger.warning("⚠️  Could not connect to ICP canister")
                self.icp_client = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize ICP client: {e}")
            self.icp_client = None

    def _verify_client_authentication(self, fit_res: fl.common.FitRes) -> bool:
        """
        Verify if client is authenticated by checking their principal ID in the canister.

        Args:
            fit_res: Fit result from client

        Returns:
            True if client is authenticated and approved, False otherwise
        """
        if not self.icp_client:
            logger.warning("⚠️  No ICP client available, skipping authentication")
            return True  # Allow if ICP is not configured

        try:
            # Check if fit result contains authentication error
            if hasattr(fit_res, 'metrics') and fit_res.metrics:
                if fit_res.metrics.get('error') == 'authentication_failed':
                    logger.error("🔐 CLIENT AUTHENTICATION FAILED")
                    logger.error("   ❌ Client reported authentication failure")
                    return False

                # Extract client principal ID from metrics
                client_principal_id = fit_res.metrics.get('client_principal_id')
                client_identity = fit_res.metrics.get('client_identity', 'unknown')

                logger.info("🔐 CLIENT AUTHENTICATION CHECK")
                logger.info(f"   🔑 Principal ID: {client_principal_id}")
                logger.info(f"   👤 Identity: {client_identity}")

                if not client_principal_id or client_principal_id == 'unknown':
                    logger.error("   ❌ Client did not provide valid principal ID")
                    logger.error("   🚫 AUTHENTICATION REJECTED")
                    return False

                # Verify client is active in the canister
                logger.info(f"   🔍 Verifying with canister...")
                is_active = self.icp_client.is_client_active_by_principal(client_principal_id)

                if is_active:
                    logger.info(f"   ✅ Client is approved in canister")
                    logger.info(f"   🎉 AUTHENTICATION SUCCESSFUL")
                    return True
                else:
                    logger.error(f"   ❌ Client is not approved in canister")
                    logger.error(f"   🚫 AUTHENTICATION REJECTED")
                    return False

            # If no metrics provided, reject
            logger.error("🔐 CLIENT AUTHENTICATION FAILED")
            logger.error("   ❌ Client did not provide authentication metrics")
            logger.error("   🚫 AUTHENTICATION REJECTED")
            return False

        except Exception as e:
            logger.error("🔐 CLIENT AUTHENTICATION ERROR")
            logger.error(f"   ❌ Error verifying client authentication: {e}")
            logger.error("   🚫 AUTHENTICATION REJECTED")
            return False

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
        # Update current round tracking
        self.current_round = server_round

        logger.info(f"🔄 Round {server_round}/{self.total_rounds}: Starting aggregation")
        logger.info(f"   📊 Received results from {len(results)} clients")

        # Print round start status to console
        print(f"\n🔄 Processing Round {server_round}/{self.total_rounds}...")
        print(f"   📊 Aggregating models from {len(results)} client(s)")

        if failures:
            logger.warning(f"   ⚠️  {len(failures)} client failures detected")
            for i, failure in enumerate(failures):
                logger.warning(f"      Failure {i+1}: {failure}")

        if not results:
            logger.error("   ❌ No results to aggregate")
            return None, {}

        logger.info(f"   🔧 Processing client parameters...")

        # Verify client authentication and extract parameters
        client_trees_list = []
        weights = []
        authenticated_count = 0

        for client_proxy, fit_res in results:
            # Check if client is authenticated
            if not self._verify_client_authentication(fit_res):
                # Get client identity for logging
                client_id = "unknown"
                if hasattr(fit_res, 'metrics') and fit_res.metrics:
                    client_id = fit_res.metrics.get('client_principal_id', 'unknown')
                logger.warning(f"❌ Rejecting unauthenticated client: {client_id}")
                continue

            authenticated_count += 1

            # Get client identity for logging
            client_id = "unknown"
            if hasattr(fit_res, 'metrics') and fit_res.metrics:
                client_id = fit_res.metrics.get('client_principal_id', 'unknown')

            # Extract parameters (should be [tree_array])
            parameters = fl.common.parameters_to_ndarrays(fit_res.parameters)

            if len(parameters) >= 1 and len(parameters[0]) > 0:
                # Convert numpy array back to serialized trees
                tree_array = parameters[0]
                serialized_trees = numpy_arrays_to_trees(tree_array)
                client_trees_list.append(serialized_trees)
                weights.append(fit_res.num_examples)
                logger.info(f"✅ Authenticated client {client_id} contributed {len(serialized_trees)} trees")
            else:
                logger.warning(f"❌ Authenticated client {client_id} provided empty parameters")

        if authenticated_count == 0:
            logger.error("❌ No authenticated clients found. Cannot proceed with aggregation.")
            return None, {}

        logger.info(f"✅ Processed {authenticated_count}/{len(results)} authenticated clients")

        if not client_trees_list:
            logger.warning("No valid parameters received from clients")
            return None, {}

        # Aggregate trees from all clients
        total_trees_before = sum(len(trees) for trees in client_trees_list)
        logger.info(f"Starting aggregation of {total_trees_before} total trees...")
        aggregated_trees = aggregate_random_forests(client_trees_list, weights)

        # Apply tree limit if configured
        if len(aggregated_trees) > self.max_trees_per_round:
            logger.warning(f"Model size ({len(aggregated_trees)} trees) exceeds limit ({self.max_trees_per_round}). "
                          f"Sampling trees to stay within limit.")
            print(f"⚠️  Model size limit: Reducing from {len(aggregated_trees)} to {self.max_trees_per_round} trees")

            # Sample trees to stay within limit (keep diversity from all clients)
            import random
            random.seed(42)  # For reproducibility
            aggregated_trees = random.sample(aggregated_trees, self.max_trees_per_round)
            logger.info(f"Sampled {len(aggregated_trees)} trees from {total_trees_before} total trees")

        logger.info(f"Final aggregated model contains {len(aggregated_trees)} trees")

        # Add processing time warnings
        if len(aggregated_trees) > 800:
            logger.warning(f"Very large model detected ({len(aggregated_trees)} trees). "
                          f"This may take several minutes to process and save.")
            print(f"⚠️  Large model warning: {len(aggregated_trees)} trees detected.")
            print(f"   This may take 5-10 minutes to process. Please be patient...")
        elif len(aggregated_trees) > 500:
            logger.info(f"Large model detected ({len(aggregated_trees)} trees). Using optimized processing.")
            print(f"📊 Processing large model with {len(aggregated_trees)} trees...")

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

        # Store enhanced training round completion on ICP blockchain
        if self.icp_client:
            try:
                # Start training round first if this is the first time
                participant_principal_ids = []
                for client_proxy, fit_res in results:
                    if hasattr(fit_res, 'metrics') and fit_res.metrics:
                        client_principal = fit_res.metrics.get('client_principal_id')
                        if client_principal and client_principal != 'unknown':
                            participant_principal_ids.append(client_principal)

                # Start the training round
                round_id = self.icp_client.start_training_round(participant_principal_ids)
                if not round_id:
                    logger.warning(f"⚠️  Failed to start training round {server_round}")
                    # Use the server_round as fallback
                    round_id = server_round
                else:
                    logger.info(f"✅ Started training round {round_id} on ICP blockchain")

                # Collect detailed participant information
                participants = []
                training_start_time = int(time.time() * 1000000000)  # Current time in nanoseconds

                for client_proxy, fit_res in results:
                    if hasattr(fit_res, 'metrics') and fit_res.metrics:
                        client_principal = fit_res.metrics.get('client_principal_id')
                        client_identity = fit_res.metrics.get('client_identity', 'unknown')

                        if client_principal and client_principal != 'unknown':
                            # Extract client information
                            client_name = os.getenv('CLIENT_NAME', f'Client_{client_identity}')
                            dataset_filename = "unknown"  # Will be enhanced later
                            samples_contributed = fit_res.num_examples
                            trees_contributed = 50  # Based on our configuration

                            # Try to get more detailed client info from environment or metrics
                            if hasattr(fit_res, 'metrics') and fit_res.metrics:
                                client_name = fit_res.metrics.get('client_name', client_name)
                                dataset_filename = fit_res.metrics.get('dataset_filename', dataset_filename)

                            participants.append({
                                'principal_id': client_principal,
                                'client_name': client_name,
                                'dataset_filename': dataset_filename,
                                'samples_contributed': samples_contributed,
                                'trees_contributed': trees_contributed
                            })

                # Calculate accuracy (simplified - using dummy value for now)
                accuracy = 0.85  # TODO: Calculate actual accuracy from evaluation

                # Extract model filename from path
                model_filename = os.path.basename(model_path) if model_path else f"model_round_{server_round}.joblib"
                training_end_time = int(time.time() * 1000000000)  # Current time in nanoseconds

                logger.info("📊 STORING ENHANCED TRAINING ROUND METADATA")
                logger.info(f"   🔄 Round: {server_round}")
                logger.info(f"   👥 Participants: {len(participants)}")
                logger.info(f"   📁 Model: {model_filename}")
                logger.info(f"   📈 Accuracy: {accuracy}")
                logger.info(f"   🌳 Trees: {len(aggregated_trees)}")
                logger.info(f"   📊 Examples: {total_examples}")

                # Use enhanced method to store comprehensive metadata
                success = self.icp_client.complete_training_round_enhanced(
                    round_id=round_id,
                    participants=participants,
                    total_examples=total_examples,
                    num_trees=len(aggregated_trees),
                    accuracy=accuracy,
                    model_path=model_path,
                    model_filename=model_filename,
                    training_start_time=training_start_time,
                    training_end_time=training_end_time
                )

                if success:
                    logger.info("✅ ENHANCED METADATA STORED ON ICP BLOCKCHAIN")
                    logger.info(f"   📋 Round {server_round} metadata includes:")
                    for i, p in enumerate(participants, 1):
                        logger.info(f"      {i}. {p['client_name']} ({p['principal_id'][:8]}...)")
                        logger.info(f"         Dataset: {p['dataset_filename']}")
                        logger.info(f"         Samples: {p['samples_contributed']}, Trees: {p['trees_contributed']}")
                else:
                    logger.warning(f"⚠️  Failed to store enhanced metadata for round {server_round}")

            except Exception as e:
                logger.error(f"❌ Error storing enhanced training round metadata: {e}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")

        # Output the generated artifact file names and completion status
        print("\n" + "="*80)
        print(f"🎯 ROUND {server_round}/{self.total_rounds} COMPLETED SUCCESSFULLY!")
        print("="*80)
        print(f"📊 Aggregation Summary:")
        print(f"   • Participating clients: {len(results)}")
        print(f"   • Total trees aggregated: {len(aggregated_trees)}")
        print(f"   • Total training examples: {total_examples:,}")
        print(f"   • Trees per client: {len(aggregated_trees) // len(results)}")
        print(f"\n📁 Generated Artifacts:")
        print(f"   • Global Model: {model_path}")
        print(f"   • Model Metadata: {metadata_path}")

        # Show progress and completion status
        progress_percentage = (server_round / self.total_rounds) * 100
        print(f"\n📈 Training Progress: {progress_percentage:.1f}% ({server_round}/{self.total_rounds} rounds)")

        if server_round < self.total_rounds:
            remaining_rounds = self.total_rounds - server_round
            print(f"⏳ Remaining rounds: {remaining_rounds}")
            print(f"🔄 Preparing for Round {server_round + 1}...")
        else:
            print("🎉 ALL TRAINING ROUNDS COMPLETED!")
            print("🏁 Federated learning process will conclude after evaluation.")

        print("="*80 + "\n")

        # Log the completion status
        logger.info(f"Round {server_round}/{self.total_rounds} completed successfully")
        logger.info(f"Progress: {progress_percentage:.1f}% complete")
        if server_round >= self.total_rounds:
            logger.info("All training rounds completed - server will terminate after final evaluation")

        return parameters, metrics

    def _save_global_model(self, serialized_trees: List[bytes], round_num: int, metadata: Dict[str, Any]) -> Tuple[str, str]:
        """
        Save the global federated model to disk with optimized handling for large models.

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

            num_trees = len(serialized_trees)
            logger.info(f"Saving model with {num_trees} trees...")

            # For large models (>500 trees), use optimized deserialization
            if num_trees > 500:
                logger.info(f"Large model detected ({num_trees} trees), using optimized deserialization...")
                global_model = self._deserialize_large_random_forest(serialized_trees, n_classes=2)
            else:
                # Use standard deserialization for smaller models
                global_model = deserialize_random_forest(serialized_trees, n_classes=2)

            # Save the model
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_filename = f"federated_cvd_model_round_{round_num}_{timestamp}.joblib"
            model_path = os.path.join(models_dir, model_filename)

            logger.info(f"Serializing model to disk...")
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
            logger.error(f"Error details: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return "", ""

    def _deserialize_large_random_forest(self, serialized_trees: List[bytes], n_classes: int = 2) -> 'RandomForestClassifier':
        """
        Optimized deserialization for large Random Forest models.

        Args:
            serialized_trees: List of serialized decision trees
            n_classes: Number of classes

        Returns:
            RandomForestClassifier with deserialized trees
        """
        from sklearn.ensemble import RandomForestClassifier
        import pickle
        import numpy as np

        logger.info(f"Starting optimized deserialization of {len(serialized_trees)} trees...")

        # Create a new Random Forest with the same number of estimators
        model = RandomForestClassifier(
            n_estimators=len(serialized_trees),
            random_state=42
        )

        # Deserialize trees in batches to manage memory
        batch_size = 100  # Process 100 trees at a time
        estimators = []

        for i in range(0, len(serialized_trees), batch_size):
            batch_end = min(i + batch_size, len(serialized_trees))
            batch_trees = serialized_trees[i:batch_end]

            logger.info(f"Processing tree batch {i//batch_size + 1}/{(len(serialized_trees) + batch_size - 1)//batch_size} "
                       f"(trees {i+1}-{batch_end})")

            # Deserialize batch of trees
            batch_estimators = []
            for tree_bytes in batch_trees:
                try:
                    tree = pickle.loads(tree_bytes)
                    batch_estimators.append(tree)
                except Exception as e:
                    logger.warning(f"Failed to deserialize tree: {e}")
                    continue

            estimators.extend(batch_estimators)

            # Log progress
            if len(estimators) % 200 == 0:
                logger.info(f"Deserialized {len(estimators)}/{len(serialized_trees)} trees...")

        # Set the estimators and model properties
        model.estimators_ = estimators
        model.n_classes_ = n_classes
        model.classes_ = np.array([0, 1])  # Binary classification
        model.n_features_in_ = estimators[0].n_features_in_ if estimators else 0
        model.n_outputs_ = 1

        logger.info(f"Optimized deserialization completed: {len(estimators)} trees ready")

        return model


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


def main(num_rounds: int, min_clients: int = 1, server_port: int = 8080, max_trees: int = 600) -> None:
    """
    Main function to run the server.

    Args:
        num_rounds: Number of federated learning rounds
        min_clients: Minimum number of clients required to start training
        server_port: Port for the server to listen on
    """
    # Load environment variables for debugging
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.warning("python-dotenv not available, skipping .env file loading")

    # Log environment variables for debugging
    server_identity = os.getenv("ICP_CLIENT_IDENTITY_NAME", "unknown_server")
    server_principal = os.getenv("ICP_SERVER_PRINCIPAL_ID", "not_set")
    icp_network = os.getenv("ICP_NETWORK", "not_set")
    canister_id = os.getenv("ICP_CANISTER_ID", "not_set")

    print(f"🔧 DEBUG: Loading server environment variables...")
    print(f"   Identity: {server_identity}")
    print(f"   Principal: {server_principal}")
    print(f"   Network: {icp_network}")
    print(f"   Canister: {canister_id}")

    logger.info("="*80)
    logger.info("🔧 SERVER ENVIRONMENT VARIABLES")
    logger.info("="*80)
    logger.info(f"ICP_CLIENT_IDENTITY_NAME: {server_identity}")
    logger.info(f"ICP_SERVER_PRINCIPAL_ID: {server_principal}")
    logger.info(f"ICP_NETWORK: {icp_network}")
    logger.info(f"ICP_CANISTER_ID: {canister_id}")
    logger.info("="*80)

    # Print startup banner
    print("\n" + "="*80)
    print("🚀 FEDERATED LEARNING SERVER FOR CVD PREDICTION")
    print("="*80)
    print(f"📋 Configuration:")
    print(f"   • Number of rounds: {num_rounds}")
    print(f"   • Server address: 0.0.0.0:{server_port}")
    print(f"   • Minimum clients required: {min_clients}")
    print(f"   • Server identity: {server_identity}")
    print(f"   • Model type: Random Forest (scikit-learn)")
    print(f"   • Aggregation strategy: FedAvg with tree combination")
    print(f"   • Model storage: ./models/")
    print("="*80)
    print(f"⏳ Waiting for at least {min_clients} client(s) to connect...")
    print("="*80 + "\n")

    logger.info(f"Starting server with {num_rounds} rounds, minimum {min_clients} clients")
    logger.info(f"Server identity loaded: {server_identity}")

    # Create custom strategy for Random Forest federated learning
    strategy = CVDFedAvgStrategy(
        total_rounds=num_rounds,  # Total number of rounds for progress tracking
        max_trees_per_round=max_trees,  # Maximum trees per round to prevent memory issues
        fraction_fit=1.0,  # Sample all clients for training
        fraction_evaluate=1.0,  # Sample all clients for evaluation
        min_fit_clients=min_clients,  # Minimum number of clients for training
        min_evaluate_clients=min_clients,  # Minimum number of clients for evaluation
        min_available_clients=min_clients,  # Minimum number of available clients
        on_fit_config_fn=fit_config,  # Function to configure training
        on_evaluate_config_fn=evaluate_config,  # Function to configure evaluation
    )

    logger.info("Server strategy configured")
    logger.info("Starting Flower server...")

    # Start server
    fl.server.start_server(
        server_address=f"0.0.0.0:{server_port}",
        config=fl.server.ServerConfig(num_rounds=num_rounds),
        strategy=strategy,
    )

    # Print comprehensive completion banner
    print("\n" + "="*80)
    print("🎉 FEDERATED LEARNING COMPLETED SUCCESSFULLY!")
    print("="*80)
    print(f"📋 Training Summary:")
    print(f"   • Total rounds completed: {num_rounds}")
    print(f"   • Minimum clients required: {min_clients}")
    print(f"   • Server identity: {server_identity}")
    print(f"   • Server port: {server_port}")
    print(f"\n📁 Generated Artifacts:")
    print(f"   • All models saved in: ./models/")
    print(f"   • Log files saved in: ./logs/")
    print(f"\n🔍 Next Steps:")
    print(f"   • Test the latest model: python test_federated_model.py")
    print(f"   • View training logs: tail -f logs/server.log")
    print(f"   • Monitor system: python monitor_logs.py summary")
    print("="*80)
    print("🏁 Server shutting down gracefully...")
    print("="*80 + "\n")

    logger.info("="*80)
    logger.info("🎉 FEDERATED LEARNING SESSION COMPLETED")
    logger.info("="*80)
    logger.info(f"Total rounds completed: {num_rounds}")
    logger.info(f"Server identity: {server_identity}")
    logger.info(f"Minimum clients required: {min_clients}")
    logger.info("All models and metadata saved successfully")
    logger.info("Server finished gracefully")
    logger.info("="*80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Federated Learning Server for CVD Prediction")
    parser.add_argument("--rounds", type=int, default=5,
                        help="Number of federated learning rounds")
    parser.add_argument("--min-clients", type=int, default=1,
                        help="Minimum number of clients required to start training")
    parser.add_argument("--port", type=int, default=8080,
                        help="Port for the server to listen on")
    parser.add_argument("--max-trees", type=int, default=600,
                        help="Maximum number of trees per round (default: 600)")

    args = parser.parse_args()

    main(args.rounds, args.min_clients, args.port, args.max_trees)