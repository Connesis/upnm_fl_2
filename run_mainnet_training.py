#!/usr/bin/env python3
"""
Run Federated Learning Training on ICP Mainnet
Execute federated learning with 3 clients using the mainnet canister.
"""

import os
import sys
import time
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def run_mainnet_training():
    """Run federated learning training on mainnet."""
    logger.info("🌐 Starting Federated Learning Training on ICP Mainnet")
    
    # Configuration
    canister_id = "wstch-aqaaa-aaaao-a4osq-cai"
    server_identity = "fl_server"
    client_identities = ["fl_client_1", "fl_client_2", "fl_client_3"]
    client_datasets = [
        "dataset/clients/client1_data.csv",
        "dataset/clients/client2_data.csv", 
        "dataset/clients/client3_data.csv"
    ]
    
    # Create logs directory
    os.makedirs("logs/mainnet", exist_ok=True)
    
    try:
        # Set environment for mainnet
        env = os.environ.copy()
        env["ICP_CLIENT_IDENTITY_NAME"] = server_identity
        env["ICP_CANISTER_ID"] = canister_id
        env["ICP_NETWORK"] = "ic"  # Mainnet network
        
        # Start server (2 rounds for mainnet demo)
        logger.info("🖥️ Starting mainnet federated learning server...")
        server_cmd = ["uv", "run", "python", "server/server.py", "--rounds", "2", "--min-clients", "3"]
        
        with open("logs/mainnet/server.log", "w") as server_log:
            server_process = subprocess.Popen(
                server_cmd, stdout=server_log, stderr=subprocess.STDOUT,
                text=True, env=env, cwd="/Users/francishor/Projects/upnm_fl_2"
            )
        
        logger.info(f"   ✅ Mainnet server started with PID: {server_process.pid}")
        time.sleep(15)  # Wait longer for mainnet initialization
        
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
            
            with open(f"logs/mainnet/client_{i}.log", "w") as client_log:
                client_process = subprocess.Popen(
                    client_cmd, stdout=client_log, stderr=subprocess.STDOUT,
                    text=True, env=client_env, cwd="/Users/francishor/Projects/upnm_fl_2"
                )
            
            client_processes.append(client_process)
            logger.info(f"   ✅ Mainnet client {i}/3 started: {identity}")
            time.sleep(8)  # Longer delay for mainnet
        
        # Wait for training to complete (longer timeout for mainnet)
        logger.info("   ⏳ Waiting for mainnet training to complete...")
        logger.info("   🌐 This may take longer due to mainnet latency...")
        
        server_process.wait(timeout=900)  # 15 minutes timeout for mainnet
        
        # Wait for clients
        for i, client_process in enumerate(client_processes, 1):
            try:
                client_process.wait(timeout=180)  # 3 minutes per client
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

def main():
    """Main function."""
    print("🌐 ICP Mainnet Federated Learning Training")
    print("=" * 60)
    print("🆔 Canister ID: wstch-aqaaa-aaaao-a4osq-cai")
    print("🔗 Candid UI: https://a4gq6-oaaaa-aaaab-qaa4q-cai.raw.icp0.io/?id=wstch-aqaaa-aaaao-a4osq-cai")
    print()
    
    success = run_mainnet_training()
    
    if success:
        print("\n🎉 Mainnet Training Completed Successfully!")
        print("📝 Check logs/mainnet/ for detailed logs")
        print("🔍 Query metadata using mainnet CLI commands")
    else:
        print("\n❌ Mainnet Training Failed!")
        print("📝 Check logs/mainnet/ for error details")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
