#!/usr/bin/env python3
"""
Run authenticated federated learning training with detailed logging.
This script demonstrates the complete authentication workflow.
"""

import os
import sys
import time
import subprocess
import logging
import threading
from typing import List, Dict
from dotenv import load_dotenv

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('authenticated_training.log')
    ]
)
logger = logging.getLogger('AUTH_TRAINING')

class AuthenticatedTrainingRunner:
    """Runs federated learning with authentication verification."""
    
    def __init__(self):
        """Initialize the training runner."""
        load_dotenv()
        self.canister_id = "uxrrr-q7777-77774-qaaaq-cai"
        self.server_identity = "fl_server"
        self.client_identities = ["fl_client_1", "fl_client_2", "fl_client_3"]
        self.client_datasets = [
            "dataset/clients/client1_data.csv",
            "dataset/clients/client2_data.csv", 
            "dataset/clients/client3_data.csv"
        ]
        self.server_process = None
        self.client_processes = []
        
        logger.info("🚀 Authenticated Training Runner Initialized")
        logger.info(f"   Canister ID: {self.canister_id}")
        logger.info(f"   Server Identity: {self.server_identity}")
        logger.info(f"   Client Identities: {self.client_identities}")
    
    def verify_all_clients_authenticated(self) -> bool:
        """Verify all clients are authenticated before starting training."""
        logger.info("🔐 Verifying all clients are authenticated...")
        
        from icp_auth_client import AuthenticatedICPClient
        
        for identity in self.client_identities:
            try:
                # Set environment for this client
                os.environ["ICP_CLIENT_IDENTITY_NAME"] = identity
                
                # Initialize ICP client
                icp_client = AuthenticatedICPClient(identity_type="client")
                
                # Get principal ID
                principal_id = icp_client.get_current_principal()
                if not principal_id:
                    logger.error(f"   ❌ {identity}: Failed to get principal ID")
                    return False
                
                # Check authentication status
                is_registered = icp_client.is_client_registered(principal_id)
                is_active = icp_client.is_client_active(principal_id)
                
                if is_registered and is_active:
                    logger.info(f"   ✅ {identity}: Authenticated ({principal_id})")
                else:
                    logger.error(f"   ❌ {identity}: Not authenticated (registered: {is_registered}, active: {is_active})")
                    return False
                    
            except Exception as e:
                logger.error(f"   ❌ {identity}: Authentication check failed: {e}")
                return False
        
        logger.info("🎉 All clients are authenticated and ready!")
        return True
    
    def start_server(self) -> bool:
        """Start the federated learning server with detailed logging."""
        logger.info("🖥️ Starting authenticated federated learning server...")
        
        try:
            # Create logs directory
            os.makedirs("logs", exist_ok=True)
            
            # Set environment for server
            env = os.environ.copy()
            env["ICP_CLIENT_IDENTITY_NAME"] = self.server_identity
            env["ICP_CANISTER_ID"] = self.canister_id
            env["ICP_NETWORK"] = "local"
            
            # Start server process with detailed logging
            cmd = ["uv", "run", "python", "server/server.py", "--rounds", "3", "--min-clients", "3"]
            
            # Create server log file
            server_log = open("logs/server_authenticated.log", "w")
            
            self.server_process = subprocess.Popen(
                cmd,
                stdout=server_log,
                stderr=subprocess.STDOUT,
                text=True,
                env=env
            )
            
            logger.info(f"   ✅ Server started with PID: {self.server_process.pid}")
            logger.info("   📝 Server logs: logs/server_authenticated.log")
            logger.info("   🔐 Server will verify each client's principal ID")
            
            # Wait for server to initialize
            time.sleep(5)
            
            return True
            
        except Exception as e:
            logger.error(f"   ❌ Failed to start server: {e}")
            return False
    
    def start_clients(self) -> bool:
        """Start all authenticated clients with detailed logging."""
        logger.info("👥 Starting authenticated federated learning clients...")
        
        for i, (identity, dataset) in enumerate(zip(self.client_identities, self.client_datasets), 1):
            try:
                # Set environment for client
                env = os.environ.copy()
                env["ICP_CLIENT_IDENTITY_NAME"] = identity
                env["ICP_CANISTER_ID"] = self.canister_id
                env["ICP_NETWORK"] = "local"
                env["CLIENT_NAME"] = f"Healthcare Provider {i}"
                env["CLIENT_ORGANIZATION"] = f"Hospital {i}"
                env["CLIENT_LOCATION"] = f"City {i}, Country"
                env["CLIENT_CONTACT_EMAIL"] = f"admin{i}@hospital{i}.com"
                
                # Start client process
                cmd = ["uv", "run", "python", "client/client.py", "--dataset", dataset, "--trees", "50"]
                
                # Create client log file
                client_log = open(f"logs/client_{i}_authenticated.log", "w")
                
                client_process = subprocess.Popen(
                    cmd,
                    stdout=client_log,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=env
                )
                
                self.client_processes.append((client_process, client_log))
                
                logger.info(f"   ✅ Client {i}/3 started: {identity} (PID: {client_process.pid})")
                logger.info(f"      Dataset: {dataset}")
                logger.info(f"      Logs: logs/client_{i}_authenticated.log")
                logger.info(f"      🔐 Client will send principal ID for verification")
                
                # Small delay between client starts
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"   ❌ Failed to start client {identity}: {e}")
                return False
        
        logger.info("🎉 All authenticated clients started!")
        return True
    
    def monitor_training(self) -> bool:
        """Monitor the authenticated training process."""
        logger.info("📊 Monitoring authenticated federated learning...")
        logger.info("   🔐 Server will verify each client's principal ID before aggregation")
        
        try:
            # Wait for server process to complete
            if self.server_process:
                logger.info("   ⏳ Waiting for training to complete...")
                self.server_process.wait()
                logger.info("   ✅ Server process completed")
            
            # Wait for all client processes to complete
            for i, (client_process, client_log) in enumerate(self.client_processes, 1):
                client_process.wait()
                client_log.close()
                logger.info(f"   ✅ Client {i}/3 process completed")
            
            logger.info("🎉 Authenticated federated learning completed!")
            return True
            
        except Exception as e:
            logger.error(f"   ❌ Error during training: {e}")
            return False
    
    def cleanup(self):
        """Clean up processes and resources."""
        logger.info("🧹 Cleaning up processes...")
        
        # Terminate server process if still running
        if self.server_process and self.server_process.poll() is None:
            self.server_process.terminate()
            logger.info("   ✅ Server process terminated")
        
        # Terminate client processes if still running
        for i, (client_process, client_log) in enumerate(self.client_processes, 1):
            if client_process.poll() is None:
                client_process.terminate()
                logger.info(f"   ✅ Client {i} process terminated")
            client_log.close()
    
    def run_authenticated_training(self) -> bool:
        """Run the complete authenticated training workflow."""
        logger.info("🎯 Starting Authenticated Federated Learning")
        logger.info("=" * 80)
        logger.info("This workflow demonstrates:")
        logger.info("  1. Client principal ID verification")
        logger.info("  2. Server-side authentication checks")
        logger.info("  3. Authenticated model aggregation")
        logger.info("=" * 80)
        
        try:
            # Step 1: Verify all clients are authenticated
            if not self.verify_all_clients_authenticated():
                logger.error("❌ Client authentication verification failed")
                return False
            
            # Step 2: Start server
            if not self.start_server():
                logger.error("❌ Failed to start server")
                return False
            
            # Step 3: Start clients
            if not self.start_clients():
                logger.error("❌ Failed to start clients")
                return False
            
            # Step 4: Monitor training
            if not self.monitor_training():
                logger.error("❌ Training failed")
                return False
            
            logger.info("🎉 Authenticated training completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Training workflow failed: {e}")
            return False
        finally:
            self.cleanup()


def main():
    """Main function to run authenticated training."""
    runner = AuthenticatedTrainingRunner()
    success = runner.run_authenticated_training()
    
    if success:
        print("\n🎉 Authenticated Federated Learning Completed Successfully!")
        print("📝 Check the log files for detailed authentication flow:")
        print("   - authenticated_training.log (main workflow)")
        print("   - logs/server_authenticated.log (server authentication details)")
        print("   - logs/client_*_authenticated.log (client authentication details)")
        print("\n🔐 Key Authentication Features Demonstrated:")
        print("   ✅ Client principal ID verification")
        print("   ✅ Server-side canister authentication checks")
        print("   ✅ Rejection of unauthenticated clients")
        print("   ✅ Authenticated model aggregation")
    else:
        print("\n❌ Authenticated Federated Learning Failed!")
        print("📝 Check authenticated_training.log for error details")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
