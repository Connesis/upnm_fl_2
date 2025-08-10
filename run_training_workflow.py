#!/usr/bin/env python3
"""
Run the federated learning training workflow with enhanced metadata.
"""

import os
import sys
import time
import subprocess
import logging
from typing import List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def run_training_workflow():
    """Run the complete training workflow."""
    logger.info("🚀 Starting Federated Learning Training Workflow")
    
    # Configuration
    canister_id = "uxrrr-q7777-77774-qaaaq-cai"
    server_identity = "fl_server"
    client_identities = ["fl_client_1", "fl_client_2", "fl_client_3"]
    client_datasets = [
        "dataset/clients/client1_data.csv",
        "dataset/clients/client2_data.csv", 
        "dataset/clients/client3_data.csv"
    ]
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    try:
        # Set environment for server
        env = os.environ.copy()
        env["ICP_CLIENT_IDENTITY_NAME"] = server_identity
        env["ICP_CANISTER_ID"] = canister_id
        env["ICP_NETWORK"] = "local"
        
        # Start server (2 rounds for demonstration)
        logger.info("🖥️ Starting federated learning server...")
        server_cmd = ["uv", "run", "python", "server/server.py", "--rounds", "2", "--min-clients", "3"]
        
        with open("logs/training_server.log", "w") as server_log:
            server_process = subprocess.Popen(
                server_cmd, stdout=server_log, stderr=subprocess.STDOUT,
                text=True, env=env, cwd="/Users/francishor/Projects/upnm_fl_2"
            )
        
        logger.info(f"   ✅ Server started with PID: {server_process.pid}")
        time.sleep(8)  # Wait for server to initialize
        
        # Start clients
        client_processes = []
        for i, (identity, dataset) in enumerate(zip(client_identities, client_datasets), 1):
            client_env = env.copy()
            client_env["ICP_CLIENT_IDENTITY_NAME"] = identity
            client_env["CLIENT_NAME"] = f"Healthcare Provider {i}"
            client_env["CLIENT_ORGANIZATION"] = f"Hospital {i}"
            client_env["CLIENT_LOCATION"] = f"City {i}, Country"
            
            client_cmd = ["uv", "run", "python", "client/client.py", 
                         "--dataset", dataset, "--trees", "30"]
            
            with open(f"logs/training_client_{i}.log", "w") as client_log:
                client_process = subprocess.Popen(
                    client_cmd, stdout=client_log, stderr=subprocess.STDOUT,
                    text=True, env=client_env, cwd="/Users/francishor/Projects/upnm_fl_2"
                )
            
            client_processes.append(client_process)
            logger.info(f"   ✅ Client {i}/3 started: {identity}")
            time.sleep(3)
        
        # Wait for training to complete
        logger.info("   ⏳ Waiting for training to complete...")
        server_process.wait(timeout=300)  # 5 minutes timeout
        
        # Wait for clients
        for i, client_process in enumerate(client_processes, 1):
            try:
                client_process.wait(timeout=60)
                logger.info(f"   ✅ Client {i}/3 completed")
            except subprocess.TimeoutExpired:
                logger.warning(f"   ⚠️ Client {i}/3 timed out, terminating...")
                client_process.terminate()
        
        logger.info("🎉 Training completed successfully!")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("❌ Training timed out")
        return False
    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        return False

if __name__ == "__main__":
    success = run_training_workflow()
    if success:
        print("\n✅ Training workflow completed!")
        print("📝 Check logs/training_*.log for detailed logs")
    else:
        print("\n❌ Training workflow failed!")
    sys.exit(0 if success else 1)
