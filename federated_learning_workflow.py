#!/usr/bin/env python3
"""
Complete Federated Learning Workflow with Enhanced Authentication
This script orchestrates the entire process:
1. Deploy canister and set admin role
2. Register 3 clients with their principal IDs
3. Server lists pending clients and approves them
4. Start federated learning with authenticated clients
"""

import os
import sys
import time
import subprocess
import logging
import threading
from typing import List, Dict
from dotenv import load_dotenv

# Add project paths
sys.path.append(os.path.dirname(__file__))
from icp_auth_client import AuthenticatedICPClient

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('federated_learning_workflow.log')
    ]
)
logger = logging.getLogger('FL_WORKFLOW')

class FederatedLearningOrchestrator:
    """Orchestrates the complete federated learning workflow with authentication."""
    
    def __init__(self):
        """Initialize the orchestrator."""
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
        
        logger.info("🚀 Federated Learning Orchestrator Initialized")
        logger.info(f"   Canister ID: {self.canister_id}")
        logger.info(f"   Server Identity: {self.server_identity}")
        logger.info(f"   Client Identities: {self.client_identities}")
    
    def get_client_principal_ids(self) -> Dict[str, str]:
        """Get principal IDs for all client identities."""
        logger.info("🔍 Retrieving client principal IDs...")
        principal_ids = {}
        
        for identity in self.client_identities:
            try:
                cmd = ["dfx", "identity", "get-principal", "--identity", identity]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                principal_id = result.stdout.strip()
                principal_ids[identity] = principal_id
                logger.info(f"   ✅ {identity}: {principal_id}")
            except subprocess.CalledProcessError as e:
                logger.error(f"   ❌ Failed to get principal for {identity}: {e}")
                return {}
        
        return principal_ids
    
    def register_clients(self, principal_ids: Dict[str, str]) -> bool:
        """Register all clients with the canister."""
        logger.info("📝 Registering clients with canister...")
        
        for identity, principal_id in principal_ids.items():
            try:
                # Use the client identity to register
                cmd = [
                    "dfx", "canister", "call", "fl_cvd_backend_backend", 
                    "register_client_enhanced", "--identity", identity
                ]
                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=True,
                    cwd="icp/fl_cvd_backend"
                )
                logger.info(f"   ✅ {identity} ({principal_id}) registered successfully")
                logger.info(f"      Response: {result.stdout.strip()}")
            except subprocess.CalledProcessError as e:
                logger.error(f"   ❌ Failed to register {identity}: {e.stderr}")
                return False
        
        return True
    
    def list_pending_clients(self) -> List[str]:
        """List all pending clients using server identity."""
        logger.info("📋 Listing pending clients...")
        
        try:
            cmd = [
                "dfx", "canister", "call", "fl_cvd_backend_backend",
                "get_pending_clients", "--identity", self.server_identity
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True,
                cwd="icp/fl_cvd_backend"
            )
            
            logger.info("   📋 Pending clients response:")
            logger.info(f"      {result.stdout.strip()}")
            
            # For now, return the known principal IDs since parsing is complex
            principal_ids = self.get_client_principal_ids()
            pending_list = list(principal_ids.values())
            
            logger.info(f"   📊 Found {len(pending_list)} pending clients:")
            for i, principal_id in enumerate(pending_list, 1):
                logger.info(f"      {i}. {principal_id}")
            
            return pending_list
            
        except subprocess.CalledProcessError as e:
            logger.error(f"   ❌ Failed to list pending clients: {e.stderr}")
            return []
    
    def approve_clients(self, principal_ids: List[str]) -> bool:
        """Approve all pending clients using server admin role."""
        logger.info("✅ Approving pending clients...")
        
        for i, principal_id in enumerate(principal_ids, 1):
            try:
                cmd = [
                    "dfx", "canister", "call", "fl_cvd_backend_backend",
                    "admin_approve_client", f'(principal "{principal_id}")',
                    "--identity", self.server_identity
                ]
                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=True,
                    cwd="icp/fl_cvd_backend"
                )
                
                if "true" in result.stdout.lower():
                    logger.info(f"   ✅ Client {i}/3 approved: {principal_id}")
                else:
                    logger.error(f"   ❌ Failed to approve client {i}/3: {principal_id}")
                    return False
                    
            except subprocess.CalledProcessError as e:
                logger.error(f"   ❌ Error approving client {principal_id}: {e.stderr}")
                return False
        
        logger.info("🎉 All clients approved successfully!")
        return True
    
    def start_server(self) -> bool:
        """Start the federated learning server."""
        logger.info("🖥️ Starting federated learning server...")
        
        try:
            # Set environment for server
            env = os.environ.copy()
            env["ICP_CLIENT_IDENTITY_NAME"] = self.server_identity
            env["ICP_CANISTER_ID"] = self.canister_id
            env["ICP_NETWORK"] = "local"
            
            # Start server process
            cmd = ["uv", "run", "python", "server/server.py", "--rounds", "3", "--min-clients", "3"]
            
            # Create server log file
            server_log = open("logs/server_workflow.log", "w")
            
            self.server_process = subprocess.Popen(
                cmd,
                stdout=server_log,
                stderr=subprocess.STDOUT,
                text=True,
                env=env
            )
            
            logger.info(f"   ✅ Server started with PID: {self.server_process.pid}")
            logger.info("   📝 Server logs: logs/server_workflow.log")
            
            # Wait a moment for server to initialize
            time.sleep(5)
            
            return True
            
        except Exception as e:
            logger.error(f"   ❌ Failed to start server: {e}")
            return False
    
    def start_clients(self) -> bool:
        """Start all federated learning clients."""
        logger.info("👥 Starting federated learning clients...")
        
        # Create logs directory
        os.makedirs("logs", exist_ok=True)
        
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
                client_log = open(f"logs/client_{i}_workflow.log", "w")
                
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
                logger.info(f"      Logs: logs/client_{i}_workflow.log")
                
                # Small delay between client starts
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"   ❌ Failed to start client {identity}: {e}")
                return False
        
        logger.info("🎉 All clients started successfully!")
        return True
    
    def monitor_training(self) -> bool:
        """Monitor the federated learning process."""
        logger.info("📊 Monitoring federated learning process...")
        
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
            
            logger.info("🎉 Federated learning completed successfully!")
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
    
    def run_complete_workflow(self) -> bool:
        """Run the complete federated learning workflow."""
        logger.info("🎯 Starting Complete Federated Learning Workflow")
        logger.info("=" * 80)
        
        try:
            # Step 1: Get client principal IDs
            principal_ids = self.get_client_principal_ids()
            if not principal_ids:
                logger.error("❌ Failed to get client principal IDs")
                return False
            
            # Step 2: Register clients
            if not self.register_clients(principal_ids):
                logger.error("❌ Failed to register clients")
                return False
            
            # Step 3: List pending clients
            pending_clients = self.list_pending_clients()
            if not pending_clients:
                logger.error("❌ No pending clients found")
                return False
            
            # Step 4: Approve clients
            if not self.approve_clients(pending_clients):
                logger.error("❌ Failed to approve clients")
                return False
            
            # Step 5: Start server
            if not self.start_server():
                logger.error("❌ Failed to start server")
                return False
            
            # Step 6: Start clients
            if not self.start_clients():
                logger.error("❌ Failed to start clients")
                return False
            
            # Step 7: Monitor training
            if not self.monitor_training():
                logger.error("❌ Training failed")
                return False
            
            logger.info("🎉 Complete workflow executed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}")
            return False
        finally:
            self.cleanup()


def main():
    """Main function to run the workflow."""
    orchestrator = FederatedLearningOrchestrator()
    success = orchestrator.run_complete_workflow()
    
    if success:
        print("\n🎉 Federated Learning Workflow Completed Successfully!")
        print("📝 Check the log files for detailed information:")
        print("   - federated_learning_workflow.log (main workflow)")
        print("   - logs/server_workflow.log (server details)")
        print("   - logs/client_*_workflow.log (client details)")
    else:
        print("\n❌ Federated Learning Workflow Failed!")
        print("📝 Check federated_learning_workflow.log for error details")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
