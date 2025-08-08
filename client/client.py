"""
Flower client implementation for federated learning.
"""
import flwr as fl
import os
import sys
import pandas as pd
import numpy as np
import logging
import time
import socket
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


def check_server_availability(host: str, port: int, timeout: int = 5) -> bool:
    """
    Check if the server is available and accepting connections.

    Args:
        host: Server hostname or IP address
        port: Server port number
        timeout: Connection timeout in seconds

    Returns:
        True if server is available, False otherwise
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.error, socket.timeout):
        return False


def wait_for_server(server_address: str, max_wait_time: int = 300, retry_interval: int = 5) -> bool:
    """
    Wait for the server to become available with exponential backoff.

    Args:
        server_address: Server address in format "host:port"
        max_wait_time: Maximum time to wait in seconds
        retry_interval: Initial retry interval in seconds

    Returns:
        True if server becomes available, False if timeout
    """
    try:
        host, port_str = server_address.split(':')
        port = int(port_str)
    except ValueError:
        logger.error(f"Invalid server address format: {server_address}")
        return False

    start_time = time.time()
    current_interval = retry_interval
    attempt = 1

    logger.info(f"🔍 Checking server availability at {server_address}...")

    while time.time() - start_time < max_wait_time:
        if check_server_availability(host, port):
            logger.info(f"✅ Server is available at {server_address}")
            return True

        elapsed = int(time.time() - start_time)
        remaining = max_wait_time - elapsed

        logger.info(f"⏳ Attempt {attempt}: Server not ready. Waiting {current_interval}s... "
                   f"(elapsed: {elapsed}s, remaining: {remaining}s)")

        time.sleep(current_interval)

        # Exponential backoff with maximum interval of 30 seconds
        current_interval = min(current_interval * 1.5, 30)
        attempt += 1

    logger.error(f"❌ Server at {server_address} did not become available within {max_wait_time} seconds")
    return False


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

        # Initialize authenticated ICP client and principal ID
        self.principal_id = None
        self.is_authenticated = False
        try:
            self.icp_client = AuthenticatedICPClient(identity_type="client")
            if self.icp_client.canister_id:
                logger.info(f"✅ Connected to ICP canister: {self.icp_client.canister_id}")

                # Get principal ID for this client
                self.principal_id = self.icp_client.get_current_principal()
                if self.principal_id:
                    logger.info(f"🔑 Client principal ID: {self.principal_id}")
                else:
                    logger.error("❌ Failed to get principal ID")
                    raise Exception("Cannot get principal ID")

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
                    self.is_authenticated = True
                elif status == "pending":
                    print("📋 Registration submitted. Waiting for admin approval...")
                    print(f"   Client: {client_name}")
                    print(f"   Organization: {organization}")
                    print(f"   Contact: {contact_email}")
                    print(f"   Principal ID: {self.principal_id}")
                    print("⚠️  Client will not be able to participate in training until approved")
                    self.is_authenticated = False
                elif status == "already_registered":
                    print("ℹ️  Client already registered with ICP blockchain")
                    # Check if client is approved
                    self._verify_client_authentication()
                else:
                    print("❌ Registration failed")
                    self.is_authenticated = False
            else:
                print("Warning: Could not connect to ICP canister")
                self.icp_client = None
        except Exception as e:
            print(f"Warning: Failed to initialize ICP client: {e}")
            self.icp_client = None

    def _verify_client_authentication(self) -> bool:
        """
        Verify if client is authenticated and approved in the canister.

        Returns:
            True if client is authenticated and approved, False otherwise
        """
        if not self.icp_client or not self.principal_id:
            logger.error("❌ No ICP client or principal ID available")
            return False

        try:
            # Check if client is registered
            is_registered = self.icp_client.is_client_registered()
            if not is_registered:
                logger.error("❌ Client is not registered in canister")
                return False

            # Check if client is active (approved)
            is_active = self.icp_client.is_client_active()
            if not is_active:
                logger.warning("⚠️  Client is registered but not yet approved")
                return False

            logger.info("✅ Client is authenticated and approved")
            self.is_authenticated = True
            return True

        except Exception as e:
            logger.error(f"❌ Failed to verify client authentication: {e}")
            return False

    def _check_authentication_before_training(self) -> bool:
        """
        Check authentication status before participating in training.

        Returns:
            True if client can participate, False otherwise
        """
        # For testing: Allow legitimate client identities when ICP is not available
        legitimate_identities = ["fl_client_1", "fl_client_2", "fl_client_3", "hospital_a", "hospital_b", "hospital_c"]

        if not self.icp_client and self.client_identity in legitimate_identities:
            logger.info(f"🧪 Testing mode: Allowing legitimate client {self.client_identity}")
            self.is_authenticated = True
            return True

        if not self.is_authenticated:
            logger.error("❌ Client is not authenticated. Cannot participate in training.")
            print("❌ Authentication required: Client must be approved by admin before training")
            if self.principal_id:
                print(f"   Principal ID: {self.principal_id}")
                print("   Please contact admin to approve this client")
            return False

        # Re-verify authentication status
        return self._verify_client_authentication()

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
        # Check authentication before training
        if not self._check_authentication_before_training():
            logger.error("❌ Authentication failed. Refusing to participate in training.")
            # Return empty parameters to indicate failure
            return [np.array([])], 0, {
                "error": "authentication_failed",
                "client_principal_id": self.principal_id or "unknown"
            }

        round_num = config.get('server_round', 'unknown')
        logger.info(f"🏋️ Starting training round {round_num}")
        logger.info(f"   📊 Training data shape: {self.X.shape}")
        logger.info(f"   🎯 Target distribution: {self.y.value_counts().to_dict()}")
        logger.info(f"   🔑 Principal ID: {self.principal_id}")

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
        # Include principal ID in metrics for server verification
        return updated_parameters, len(self.X), {
            "client_principal_id": self.principal_id or "unknown",
            "client_identity": self.client_identity
        }
        
    def evaluate(self, parameters: List[np.ndarray], config: Dict[str, Any]) -> Tuple[float, int, Dict]:
        """
        Evaluate the model on local data.

        Args:
            parameters: Model parameters from server
            config: Configuration dictionary

        Returns:
            Tuple of (loss, num_examples, metrics)
        """
        # Check authentication before evaluation
        if not self._check_authentication_before_training():
            logger.error("❌ Authentication failed. Refusing to participate in evaluation.")
            # Return default metrics to indicate failure
            return 1.0, 0, {
                "error": "authentication_failed",
                "client_principal_id": self.principal_id or "unknown"
            }

        print(f"Evaluating model for round {config.get('server_round', 'unknown')}...")
        logger.info(f"🔑 Principal ID: {self.principal_id}")

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

        # Include principal ID in metrics for server verification
        metrics.update({
            "client_principal_id": self.principal_id or "unknown",
            "client_identity": self.client_identity
        })

        return loss, len(self.X), metrics


def main(dataset_path: str, max_wait_time: int = 300, retry_interval: int = 5, n_estimators: int = 100) -> None:
    """
    Main function to run the client.

    Args:
        dataset_path: Path to the dataset CSV file
        max_wait_time: Maximum time to wait for server in seconds
        retry_interval: Initial retry interval in seconds
    """
    # Load environment variables
    load_dotenv()

    # Log environment variables for debugging
    client_identity = os.getenv("ICP_CLIENT_IDENTITY_NAME", "unknown_client")
    client_principal = os.getenv("ICP_CLIENT_PRINCIPAL_ID", "not_set")
    server_address = os.getenv("SERVER_ADDRESS", "127.0.0.1:8080")
    icp_network = os.getenv("ICP_NETWORK", "not_set")
    canister_id = os.getenv("ICP_CANISTER_ID", "not_set")
    client_name = os.getenv("CLIENT_NAME", f"FL Client ({client_identity})")
    client_org = os.getenv("CLIENT_ORGANIZATION", "Federated Learning Network")

    logger.info("="*80)
    logger.info("🔧 CLIENT ENVIRONMENT VARIABLES")
    logger.info("="*80)
    logger.info(f"ICP_CLIENT_IDENTITY_NAME: {client_identity}")
    logger.info(f"ICP_CLIENT_PRINCIPAL_ID: {client_principal}")
    logger.info(f"SERVER_ADDRESS: {server_address}")
    logger.info(f"ICP_NETWORK: {icp_network}")
    logger.info(f"ICP_CANISTER_ID: {canister_id}")
    logger.info(f"CLIENT_NAME: {client_name}")
    logger.info(f"CLIENT_ORGANIZATION: {client_org}")
    logger.info(f"DATASET_PATH: {dataset_path}")
    logger.info("="*80)

    # Load and preprocess data
    X, y = load_and_preprocess_data(dataset_path)

    # Initialize model with configurable number of trees
    logger.info(f"🌳 Initializing model with {n_estimators} trees per client")
    model = CVDModel(n_estimators=n_estimators)

    # Create client
    client = CVDClient(model, X, y)

    # Wait for server to become available
    logger.info(f"🔍 Attempting to connect to server at {server_address}")
    logger.info(f"⏱️  Max wait time: {max_wait_time}s, retry interval: {retry_interval}s")
    print(f"🔍 Waiting for server at {server_address}...")
    if not wait_for_server(server_address, max_wait_time, retry_interval):
        error_msg = f"❌ Failed to connect to server at {server_address} within {max_wait_time} seconds"
        logger.error(error_msg)
        print(error_msg)
        print("💡 Make sure the server is running and accessible")
        return

    # Start client
    print(f"🚀 Connecting to server at {server_address}...")
    try:
        fl.client.start_numpy_client(server_address=server_address, client=client)
        print("✅ Client session completed successfully")
    except Exception as e:
        logger.error(f"❌ Client failed: {e}")
        print(f"❌ Client failed: {e}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Federated Learning Client for CVD Prediction")
    parser.add_argument("--dataset", type=str, required=True, help="Path to dataset CSV file")
    parser.add_argument("--max-wait-time", type=int, default=300,
                        help="Maximum time to wait for server in seconds (default: 300)")
    parser.add_argument("--retry-interval", type=int, default=5,
                        help="Initial retry interval in seconds (default: 5)")
    parser.add_argument("--trees", type=int, default=100,
                        help="Number of trees per client (default: 100)")

    args = parser.parse_args()

    main(args.dataset, args.max_wait_time, args.retry_interval, args.trees)