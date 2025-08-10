#!/usr/bin/env python3
"""
ICP Mainnet Deployment Script
Deploy federated learning canister to ICP mainnet and run training.
"""

import os
import sys
import time
import subprocess
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mainnet_deployment.log')
    ]
)
logger = logging.getLogger('MAINNET_DEPLOY')

class MainnetDeploymentManager:
    """Manages deployment to ICP mainnet and training execution."""
    
    def __init__(self):
        """Initialize the deployment manager."""
        load_dotenv()
        self.network = "ic"  # Mainnet network
        self.server_identity = "fl_server"
        self.client_identities = ["fl_client_1", "fl_client_2", "fl_client_3"]
        self.client_datasets = [
            "dataset/clients/client1_data.csv",
            "dataset/clients/client2_data.csv", 
            "dataset/clients/client3_data.csv"
        ]
        self.canister_id = None
        
        logger.info("🌐 Mainnet Deployment Manager Initialized")
        logger.info(f"   Network: {self.network}")
        logger.info(f"   Server Identity: {self.server_identity}")
        logger.info(f"   Client Identities: {self.client_identities}")
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met for mainnet deployment."""
        logger.info("🔍 Checking mainnet deployment prerequisites...")
        
        try:
            # Check dfx version
            result = subprocess.run(["dfx", "--version"], capture_output=True, text=True, check=True)
            logger.info(f"   ✅ dfx version: {result.stdout.strip()}")
            
            # Check if identities exist
            for identity in [self.server_identity] + self.client_identities:
                try:
                    result = subprocess.run([
                        "dfx", "identity", "get-principal", "--identity", identity
                    ], capture_output=True, text=True, check=True)
                    logger.info(f"   ✅ Identity {identity}: {result.stdout.strip()}")
                except subprocess.CalledProcessError:
                    logger.error(f"   ❌ Identity {identity} not found")
                    logger.info(f"   💡 Create with: dfx identity new {identity}")
                    return False
            
            # Check wallet balance (cycles)
            try:
                result = subprocess.run([
                    "dfx", "wallet", "balance", "--network", self.network, "--identity", self.server_identity
                ], capture_output=True, text=True, check=True)
                logger.info(f"   💰 Wallet balance: {result.stdout.strip()}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"   ⚠️  Could not check wallet balance: {e}")
                logger.info("   💡 You may need to set up a cycles wallet")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"   ❌ Prerequisites check failed: {e}")
            return False
    
    def deploy_canister_to_mainnet(self) -> bool:
        """Deploy the canister to ICP mainnet."""
        logger.info("🚀 Deploying canister to ICP mainnet...")
        
        try:
            # Deploy to mainnet
            result = subprocess.run([
                "dfx", "deploy", "fl_cvd_backend_backend", 
                "--network", self.network, 
                "--identity", self.server_identity,
                "--with-cycles", "1000000000000"  # 1T cycles
            ], capture_output=True, text=True, check=True, 
               cwd="icp/fl_cvd_backend", timeout=300)
            
            # Extract canister ID from output
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if "canister ID" in line.lower():
                    # Extract canister ID (mainnet IDs are different format)
                    parts = line.split()
                    for part in parts:
                        if len(part) > 20 and "-" in part:
                            self.canister_id = part
                            break
            
            if not self.canister_id:
                # Try to get canister ID from dfx.json or other sources
                logger.warning("Could not extract canister ID from deployment output")
                return False
            
            logger.info(f"✅ Canister deployed to mainnet: {self.canister_id}")
            logger.info(f"🌐 Mainnet URL: https://{self.canister_id}.ic0.app")
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Mainnet deployment timed out")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to deploy to mainnet: {e}")
            logger.error(f"   stdout: {e.stdout}")
            logger.error(f"   stderr: {e.stderr}")
            return False
    
    def setup_mainnet_canister(self) -> bool:
        """Set up the canister on mainnet (admin, register clients, approve)."""
        logger.info("⚙️ Setting up canister on mainnet...")
        
        try:
            # Set admin
            logger.info("   👑 Setting admin role...")
            result = subprocess.run([
                "dfx", "canister", "call", "fl_cvd_backend_backend", 
                "init_admin", "--network", self.network, "--identity", self.server_identity
            ], capture_output=True, text=True, check=True, 
               cwd="icp/fl_cvd_backend", timeout=60)
            
            logger.info(f"   ✅ Admin set: {result.stdout.strip()}")
            
            # Register clients
            principal_ids = {}
            for identity in self.client_identities:
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
                    "register_client_enhanced", "--network", self.network, "--identity", identity
                ], capture_output=True, text=True, check=True,
                   cwd="icp/fl_cvd_backend", timeout=60)
                
                logger.info(f"   ✅ {identity} registered")
            
            # Approve clients
            for identity, principal_id in principal_ids.items():
                result = subprocess.run([
                    "dfx", "canister", "call", "fl_cvd_backend_backend",
                    "admin_approve_client", f'(principal "{principal_id}")',
                    "--network", self.network, "--identity", self.server_identity
                ], capture_output=True, text=True, check=True,
                   cwd="icp/fl_cvd_backend", timeout=60)
                
                logger.info(f"   ✅ {identity} approved")
            
            logger.info("✅ Mainnet canister setup completed")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to setup canister: {e}")
            return False
    
    def run_mainnet_training(self) -> bool:
        """Run federated learning training using mainnet canister."""
        logger.info("🏋️ Running federated learning training on mainnet...")
        
        try:
            # Create logs directory
            os.makedirs("logs/mainnet", exist_ok=True)
            
            # Set environment for mainnet
            env = os.environ.copy()
            env["ICP_CLIENT_IDENTITY_NAME"] = self.server_identity
            env["ICP_CANISTER_ID"] = self.canister_id
            env["ICP_NETWORK"] = self.network  # Use mainnet
            
            # Start server (2 rounds for demonstration)
            logger.info("   🖥️ Starting mainnet server...")
            server_cmd = ["uv", "run", "python", "server/server.py", "--rounds", "2", "--min-clients", "3"]
            
            with open("logs/mainnet/server.log", "w") as server_log:
                server_process = subprocess.Popen(
                    server_cmd, stdout=server_log, stderr=subprocess.STDOUT,
                    text=True, env=env
                )
            
            logger.info(f"   ✅ Mainnet server started with PID: {server_process.pid}")
            time.sleep(10)  # Wait longer for mainnet initialization
            
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
                
                with open(f"logs/mainnet/client_{i}.log", "w") as client_log:
                    client_process = subprocess.Popen(
                        client_cmd, stdout=client_log, stderr=subprocess.STDOUT,
                        text=True, env=client_env
                    )
                
                client_processes.append(client_process)
                logger.info(f"   ✅ Mainnet client {i}/3 started: {identity}")
                time.sleep(5)  # Longer delay for mainnet
            
            # Wait for training to complete (longer timeout for mainnet)
            logger.info("   ⏳ Waiting for mainnet training to complete...")
            server_process.wait(timeout=600)  # 10 minutes timeout for mainnet
            
            # Wait for clients
            for i, client_process in enumerate(client_processes, 1):
                try:
                    client_process.wait(timeout=120)
                    logger.info(f"   ✅ Mainnet client {i}/3 completed")
                except subprocess.TimeoutExpired:
                    logger.warning(f"   ⚠️ Client {i}/3 timed out, terminating...")
                    client_process.terminate()
            
            logger.info("🎉 Mainnet training completed successfully!")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Mainnet training timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Mainnet training failed: {e}")
            return False
    
    def query_mainnet_metadata(self) -> bool:
        """Query training metadata from mainnet canister."""
        logger.info("🔍 Querying training metadata from mainnet...")
        
        try:
            # Query training history
            logger.info("   📋 Querying mainnet training history...")
            history_result = subprocess.run([
                "dfx", "canister", "call", "fl_cvd_backend_backend",
                "get_training_history", "--network", self.network, "--identity", self.server_identity
            ], capture_output=True, text=True, check=True,
               cwd="icp/fl_cvd_backend", timeout=60)
            
            logger.info("✅ MAINNET TRAINING HISTORY:")
            logger.info(f"   {history_result.stdout.strip()}")
            
            # Query model metadata
            metadata_result = subprocess.run([
                "dfx", "canister", "call", "fl_cvd_backend_backend",
                "get_all_model_metadata", "--network", self.network, "--identity", self.server_identity
            ], capture_output=True, text=True, check=True,
               cwd="icp/fl_cvd_backend", timeout=60)
            
            logger.info("✅ MAINNET MODEL METADATA:")
            logger.info(f"   {metadata_result.stdout.strip()}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to query mainnet metadata: {e}")
            return False
    
    def run_complete_mainnet_deployment(self) -> bool:
        """Run the complete mainnet deployment workflow."""
        logger.info("🌐 STARTING COMPLETE MAINNET DEPLOYMENT")
        logger.info("=" * 80)
        
        steps = [
            ("Check Prerequisites", self.check_prerequisites),
            ("Deploy to Mainnet", self.deploy_canister_to_mainnet),
            ("Setup Canister", self.setup_mainnet_canister),
            ("Run Training", self.run_mainnet_training),
            ("Query Metadata", self.query_mainnet_metadata)
        ]
        
        for i, (step_name, step_func) in enumerate(steps, 1):
            logger.info(f"\n{'='*20} STEP {i}: {step_name.upper()} {'='*20}")
            
            if not step_func():
                logger.error(f"❌ Step {i} failed: {step_name}")
                return False
            
            logger.info(f"✅ Step {i} completed: {step_name}")
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 COMPLETE MAINNET DEPLOYMENT FINISHED SUCCESSFULLY!")
        logger.info(f"🌐 Canister ID: {self.canister_id}")
        logger.info(f"🔗 Mainnet URL: https://{self.canister_id}.ic0.app")
        logger.info("=" * 80)
        return True


def main():
    """Main function to run mainnet deployment."""
    print("🌐 ICP Mainnet Deployment for Federated Learning")
    print("=" * 60)
    print("⚠️  WARNING: This will deploy to ICP mainnet and consume cycles!")
    print("💰 Make sure you have sufficient ICP tokens/cycles for deployment")
    print("🔐 Ensure all identities are properly set up for mainnet")
    print()
    
    response = input("Do you want to proceed with mainnet deployment? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Deployment cancelled by user")
        return 1
    
    deployment = MainnetDeploymentManager()
    success = deployment.run_complete_mainnet_deployment()
    
    if success:
        print("\n🎉 Mainnet Deployment Completed Successfully!")
        print("📝 Check mainnet_deployment.log for detailed logs")
        print("📁 Check logs/mainnet/ for training logs")
        print(f"🌐 Your canister is live on mainnet: {deployment.canister_id}")
    else:
        print("\n❌ Mainnet Deployment Failed!")
        print("📝 Check mainnet_deployment.log for error details")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
