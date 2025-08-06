"""
Flower client implementation for federated learning.
"""
import flwr as fl
import os
import sys
import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, Any, List
from dotenv import load_dotenv

from utils.data_preprocessing import load_and_preprocess_data
from utils.model import CVDModel

# Add ICP client
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


class CVDClient(fl.client.NumPyClient):
    """Flower client for cardiovascular disease prediction with ICP integration."""

    def __init__(self, model: CVDModel, X: pd.DataFrame, y: pd.Series):
        """
        Initialize the client with model and data.

        Args:
            model: CVDModel instance
            X: Features DataFrame
            y: Target Series
        """
        self.model = model
        self.X = X
        self.y = y

        # Get client identity from environment
        self.client_identity = os.getenv("ICP_CLIENT_IDENTITY_NAME", "unknown_client")
        logger.info(f"🔗 Initializing client with identity: {self.client_identity}")

        # Initialize authenticated ICP client
        try:
            self.icp_client = AuthenticatedICPClient(identity_type="client")
            if self.icp_client.canister_id:
                logger.info(f"✅ Connected to ICP canister: {self.icp_client.canister_id}")

                # Get client metadata from environment
                client_name = os.getenv("CLIENT_NAME", f"FL Client ({self.client_identity})")
                organization = os.getenv("CLIENT_ORGANIZATION", "Federated Learning Network")
                location = os.getenv("CLIENT_LOCATION", "Unknown Location")
                contact_email = os.getenv("CLIENT_CONTACT_EMAIL", "unknown@example.com")

                logger.info(f"📋 Client metadata: {client_name} from {organization}")

                # Register client with ICP (will be in pending status)
                logger.info("🔄 Registering with ICP blockchain...")
                status = self.icp_client.register_client_with_metadata(
                    client_name=client_name,
                    organization=organization,
                    location=location,
                    contact_email=contact_email
                )

                if status == "success":
                    print("✅ Successfully registered and approved with ICP blockchain")
                elif status == "pending":
                    print("📋 Registration submitted. Waiting for admin approval...")
                    print(f"   Client: {client_name}")
                    print(f"   Organization: {organization}")
                    print(f"   Contact: {contact_email}")
                elif status == "already_registered":
                    print("ℹ️  Client already registered with ICP blockchain")
                else:
                    print("❌ Registration failed")
            else:
                print("Warning: Could not connect to ICP canister")
                self.icp_client = None
        except Exception as e:
            print(f"Warning: Failed to initialize ICP client: {e}")
            self.icp_client = None
        
    def get_parameters(self, config: Dict[str, Any]) -> List[np.ndarray]:
        """
        Get model parameters for federated learning.

        Args:
            config: Configuration dictionary

        Returns:
            Model parameters as list of numpy arrays
        """
        parameters_array = self.model.get_federated_parameters()

        # Return parameters as list containing just the array
        return [parameters_array]
        
    def fit(self, parameters: List[np.ndarray], config: Dict[str, Any]) -> Tuple[List[np.ndarray], int, Dict]:
        """
        Train the model on local data.

        Args:
            parameters: Model parameters from server
            config: Configuration dictionary

        Returns:
            Tuple of (parameters, num_examples, metrics)
        """
        round_num = config.get('server_round', 'unknown')
        logger.info(f"🏋️ Starting training round {round_num}")
        logger.info(f"   📊 Training data shape: {self.X.shape}")
        logger.info(f"   🎯 Target distribution: {self.y.value_counts().to_dict()}")

        # Set parameters if provided (not first round)
        if len(parameters) >= 1 and len(parameters[0]) > 0:
            print("Setting global model parameters...")
            self.model.set_federated_parameters(parameters[0])

        # Train on local data
        print(f"Training on {len(self.X)} local samples...")
        self.model.train(self.X, self.y)

        # Get updated parameters
        updated_parameters = self.get_parameters(config)

        print("Local training completed.")
        return updated_parameters, len(self.X), {}
        
    def evaluate(self, parameters: List[np.ndarray], config: Dict[str, Any]) -> Tuple[float, int, Dict]:
        """
        Evaluate the model on local data.

        Args:
            parameters: Model parameters from server
            config: Configuration dictionary

        Returns:
            Tuple of (loss, num_examples, metrics)
        """
        print(f"Evaluating model for round {config.get('server_round', 'unknown')}...")

        # Set parameters if provided
        if len(parameters) >= 1 and len(parameters[0]) > 0:
            self.model.set_federated_parameters(parameters[0])

        # Evaluate the model
        if self.model.is_trained():
            metrics = self.model.evaluate(self.X, self.y)
            loss = 1 - metrics['accuracy']
            print(f"Evaluation completed. Accuracy: {metrics['accuracy']:.4f}")
        else:
            # Model not trained yet
            metrics = {'accuracy': 0.0}
            loss = 1.0
            print("Model not trained yet, returning default metrics.")

        return loss, len(self.X), metrics


def main(dataset_path: str) -> None:
    """
    Main function to run the client.
    
    Args:
        dataset_path: Path to the dataset CSV file
    """
    # Load environment variables
    load_dotenv()
    
    # Load and preprocess data
    X, y = load_and_preprocess_data(dataset_path)
    
    # Initialize model
    model = CVDModel()
    
    # Create client
    client = CVDClient(model, X, y)
    
    # Get server address from environment or use default
    server_address = os.getenv("SERVER_ADDRESS", "127.0.0.1:8080")
    
    # Start client
    print(f"Connecting to server at {server_address}...")
    fl.client.start_numpy_client(server_address=server_address, client=client)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Federated Learning Client for CVD Prediction")
    parser.add_argument("--dataset", type=str, required=True, help="Path to dataset CSV file")
    
    args = parser.parse_args()
    
    main(args.dataset)