#!/usr/bin/env python3
"""
Complete Federated Learning Workflow Setup
This script handles the entire process from clean ICP setup to training completion.
"""

import os
import sys
import time
import subprocess
import logging
from typing import List, Dict
from dotenv import load_dotenv

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('complete_workflow.log')
    ]
)
logger = logging.getLogger('COMPLETE_WORKFLOW')

class CompleteWorkflowManager:
    """Manages the complete federated learning workflow from setup to completion."""
    
    def __init__(self):
        """Initialize the workflow manager."""
        load_dotenv()
        self.server_identity = "fl_server"
        self.client_identities = ["fl_client_1", "fl_client_2", "fl_client_3"]
        self.client_datasets = [
            "dataset/clients/client1_data.csv",
            "dataset/clients/client2_data.csv", 
            "dataset/clients/client3_data.csv"
        ]
        self.canister_id = None
        
        logger.info("🚀 Complete Workflow Manager Initialized")
        logger.info(f"   Server Identity: {self.server_identity}")
        logger.info(f"   Client Identities: {self.client_identities}")
    
    def step_1_clean_and_start_localnet(self) -> bool:
        """Step 1: Clean and start ICP local network."""
        logger.info("🧹 STEP 1: Cleaning and starting ICP local network...")
        
        try:
            # Stop any existing dfx processes
            logger.info("   Stopping existing dfx processes...")
            subprocess.run(["dfx", "stop"], capture_output=True, check=False)
            time.sleep(2)
            
            # Clean dfx state
            logger.info("   Cleaning dfx state...")
            subprocess.run(["dfx", "start", "--clean", "--background"], 
                         capture_output=True, check=True, timeout=60)
            
            logger.info("✅ ICP local network started with clean state")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("❌ dfx start timed out")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to start dfx: {e}")
            return False
    
    def step_2_deploy_canister(self) -> bool:
        """Step 2: Deploy the canister with fl_server identity."""
        logger.info("📦 STEP 2: Deploying canister with fl_server identity...")
        
        try:
            # Deploy canister
            result = subprocess.run([
                "dfx", "deploy", "fl_cvd_backend_backend", "--identity", self.server_identity
            ], capture_output=True, text=True, check=True, 
               cwd="icp/fl_cvd_backend", timeout=120)
            
            # Extract canister ID from output
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if "canister ID" in line and "uxrrr" in line:
                    # Extract canister ID
                    parts = line.split()
                    for part in parts:
                        if "uxrrr" in part:
                            self.canister_id = part
                            break
            
            if not self.canister_id:
                self.canister_id = "uxrrr-q7777-77774-qaaaq-cai"  # Default from previous deployments
            
            logger.info(f"✅ Canister deployed successfully: {self.canister_id}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Canister deployment timed out")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to deploy canister: {e}")
            return False
    
    def step_3_set_admin(self) -> bool:
        """Step 3: Set fl_server as admin."""
        logger.info("👑 STEP 3: Setting fl_server as admin...")
        
        try:
            result = subprocess.run([
                "dfx", "canister", "call", "fl_cvd_backend_backend", 
                "init_admin", "--identity", self.server_identity
            ], capture_output=True, text=True, check=True, 
               cwd="icp/fl_cvd_backend", timeout=30)
            
            logger.info(f"✅ Admin role set for {self.server_identity}")
            logger.info(f"   Response: {result.stdout.strip()}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to set admin: {e}")
            return False
    
    def step_4_register_clients(self) -> Dict[str, str]:
        """Step 4: Register 3 clients and get their principal IDs."""
        logger.info("📝 STEP 4: Registering 3 clients...")
        
        principal_ids = {}
        
        for identity in self.client_identities:
            try:
                # Get principal ID
                result = subprocess.run([
                    "dfx", "identity", "get-principal", "--identity", identity
                ], capture_output=True, text=True, check=True)
                
                principal_id = result.stdout.strip()
                principal_ids[identity] = principal_id
                
                logger.info(f"   📋 {identity}: {principal_id}")
                
                # Register client
                register_result = subprocess.run([
                    "dfx", "canister", "call", "fl_cvd_backend_backend",
                    "register_client_enhanced", "--identity", identity
                ], capture_output=True, text=True, check=True,
                   cwd="icp/fl_cvd_backend", timeout=30)
                
                logger.info(f"   ✅ {identity} registered successfully")
                
            except subprocess.CalledProcessError as e:
                logger.error(f"   ❌ Failed to register {identity}: {e}")
                return {}
        
        logger.info(f"✅ All {len(principal_ids)} clients registered")
        return principal_ids
    
    def step_5_approve_clients(self, principal_ids: Dict[str, str]) -> bool:
        """Step 5: Server approves all clients."""
        logger.info("✅ STEP 5: Server approving all clients...")
        
        for identity, principal_id in principal_ids.items():
            try:
                result = subprocess.run([
                    "dfx", "canister", "call", "fl_cvd_backend_backend",
                    "admin_approve_client", f'(principal "{principal_id}")',
                    "--identity", self.server_identity
                ], capture_output=True, text=True, check=True,
                   cwd="icp/fl_cvd_backend", timeout=30)
                
                if "true" in result.stdout.lower():
                    logger.info(f"   ✅ {identity} approved: {principal_id[:8]}...")
                else:
                    logger.error(f"   ❌ Failed to approve {identity}")
                    return False
                    
            except subprocess.CalledProcessError as e:
                logger.error(f"   ❌ Error approving {identity}: {e}")
                return False
        
        logger.info("✅ All clients approved successfully")
        return True
    
    def step_6_run_training(self) -> bool:
        """Step 6: Run federated learning training."""
        logger.info("🏋️ STEP 6: Running federated learning training...")
        
        try:
            # Create logs directory
            os.makedirs("logs", exist_ok=True)
            
            # Set environment for server
            env = os.environ.copy()
            env["ICP_CLIENT_IDENTITY_NAME"] = self.server_identity
            env["ICP_CANISTER_ID"] = self.canister_id
            env["ICP_NETWORK"] = "local"
            
            # Start server (2 rounds for demonstration)
            logger.info("   🖥️ Starting server...")
            server_cmd = ["uv", "run", "python", "server/server.py", "--rounds", "2", "--min-clients", "3"]
            
            with open("logs/workflow_server.log", "w") as server_log:
                server_process = subprocess.Popen(
                    server_cmd, stdout=server_log, stderr=subprocess.STDOUT,
                    text=True, env=env
                )
            
            logger.info(f"   ✅ Server started with PID: {server_process.pid}")
            time.sleep(5)  # Wait for server to initialize
            
            # Start clients
            client_processes = []
            for i, (identity, dataset) in enumerate(zip(self.client_identities, self.client_datasets), 1):
                client_env = env.copy()
                client_env["ICP_CLIENT_IDENTITY_NAME"] = identity
                client_env["CLIENT_NAME"] = f"Healthcare Provider {i}"
                client_env["CLIENT_ORGANIZATION"] = f"Hospital {i}"
                client_env["CLIENT_LOCATION"] = f"City {i}, Country"
                
                client_cmd = ["uv", "run", "python", "client/client.py", 
                             "--dataset", dataset, "--trees", "30"]
                
                with open(f"logs/workflow_client_{i}.log", "w") as client_log:
                    client_process = subprocess.Popen(
                        client_cmd, stdout=client_log, stderr=subprocess.STDOUT,
                        text=True, env=client_env
                    )
                
                client_processes.append(client_process)
                logger.info(f"   ✅ Client {i}/3 started: {identity}")
                time.sleep(2)
            
            # Wait for training to complete
            logger.info("   ⏳ Waiting for training to complete...")
            server_process.wait(timeout=300)  # 5 minutes timeout
            
            # Wait for clients
            for i, client_process in enumerate(client_processes, 1):
                client_process.wait(timeout=60)
                logger.info(f"   ✅ Client {i}/3 completed")
            
            logger.info("✅ Training completed successfully")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Training timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Training failed: {e}")
            return False
    
    def step_7_query_metadata(self) -> bool:
        """Step 7: Query training history and metadata using CLI."""
        logger.info("🔍 STEP 7: Querying training history and metadata...")
        
        try:
            # Query training history
            logger.info("   📋 Querying training history...")
            history_result = subprocess.run([
                "dfx", "canister", "call", "fl_cvd_backend_backend",
                "get_training_history", "--identity", self.server_identity
            ], capture_output=True, text=True, check=True,
               cwd="icp/fl_cvd_backend", timeout=30)
            
            logger.info("✅ TRAINING HISTORY:")
            logger.info(f"   {history_result.stdout.strip()}")
            
            # Query all model metadata
            logger.info("   📊 Querying all model metadata...")
            metadata_result = subprocess.run([
                "dfx", "canister", "call", "fl_cvd_backend_backend",
                "get_all_model_metadata", "--identity", self.server_identity
            ], capture_output=True, text=True, check=True,
               cwd="icp/fl_cvd_backend", timeout=30)
            
            logger.info("✅ ALL MODEL METADATA:")
            logger.info(f"   {metadata_result.stdout.strip()}")
            
            # Query specific round metadata
            for round_id in [1, 2]:
                logger.info(f"   🎯 Querying round {round_id} metadata...")
                round_result = subprocess.run([
                    "dfx", "canister", "call", "fl_cvd_backend_backend",
                    "get_training_round_metadata", f"({round_id})",
                    "--identity", self.server_identity
                ], capture_output=True, text=True, check=True,
                   cwd="icp/fl_cvd_backend", timeout=30)
                
                logger.info(f"✅ ROUND {round_id} METADATA:")
                logger.info(f"   {round_result.stdout.strip()}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to query metadata: {e}")
            return False
    
    def run_complete_workflow(self) -> bool:
        """Run the complete workflow from start to finish."""
        logger.info("🎯 STARTING COMPLETE FEDERATED LEARNING WORKFLOW")
        logger.info("=" * 80)
        
        steps = [
            ("Clean and Start LocalNet", self.step_1_clean_and_start_localnet),
            ("Deploy Canister", self.step_2_deploy_canister),
            ("Set Admin Role", self.step_3_set_admin),
            ("Register Clients", self.step_4_register_clients),
            ("Approve Clients", None),  # Special handling
            ("Run Training", self.step_6_run_training),
            ("Query Metadata", self.step_7_query_metadata)
        ]
        
        principal_ids = {}
        
        for i, (step_name, step_func) in enumerate(steps, 1):
            logger.info(f"\n{'='*20} STEP {i}: {step_name.upper()} {'='*20}")
            
            if step_name == "Register Clients":
                principal_ids = step_func()
                if not principal_ids:
                    logger.error(f"❌ Step {i} failed: {step_name}")
                    return False
            elif step_name == "Approve Clients":
                if not self.step_5_approve_clients(principal_ids):
                    logger.error(f"❌ Step {i} failed: {step_name}")
                    return False
            else:
                if not step_func():
                    logger.error(f"❌ Step {i} failed: {step_name}")
                    return False
            
            logger.info(f"✅ Step {i} completed: {step_name}")
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 COMPLETE WORKFLOW FINISHED SUCCESSFULLY!")
        logger.info("=" * 80)
        return True


def main():
    """Main function to run the complete workflow."""
    workflow = CompleteWorkflowManager()
    success = workflow.run_complete_workflow()
    
    if success:
        print("\n🎉 Complete Federated Learning Workflow Completed Successfully!")
        print("📝 Check complete_workflow.log for detailed logs")
        print("📁 Check logs/ directory for server and client logs")
        print("\n🔍 CLI Commands to Query Metadata:")
        print("   # Query training history")
        print("   dfx canister call fl_cvd_backend_backend get_training_history --identity fl_server")
        print("   # Query all model metadata")
        print("   dfx canister call fl_cvd_backend_backend get_all_model_metadata --identity fl_server")
        print("   # Query specific round")
        print("   dfx canister call fl_cvd_backend_backend get_training_round_metadata '(1)' --identity fl_server")
    else:
        print("\n❌ Complete Workflow Failed!")
        print("📝 Check complete_workflow.log for error details")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
