#!/usr/bin/env python3
"""
Test script to demonstrate tree configuration control in federated learning.
"""

import subprocess
import time
import os

def test_tree_configuration(trees_per_client=50):
    """Test federated learning with specific number of trees per client."""
    
    print(f"🌳 Testing Federated Learning with {trees_per_client} trees per client")
    print("=" * 70)
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Start server with reduced tree limit for testing
    print("🖥️ Starting server...")
    env = os.environ.copy()
    env["ICP_CLIENT_IDENTITY_NAME"] = "fl_server"
    env["ICP_NETWORK"] = "local"
    env["ICP_CANISTER_ID"] = "uxrrr-q7777-77774-qaaaq-cai"
    
    server_log = open("logs/test_server.log", "w")
    server_process = subprocess.Popen(
        ["uv", "run", "python", "server/server.py", "--rounds", "2", "--max-trees", "200"],
        stdout=server_log,
        stderr=subprocess.STDOUT,
        text=True,
        env=env
    )
    
    time.sleep(3)  # Wait for server to start
    
    if server_process.poll() is not None:
        print("❌ Server failed to start")
        server_log.close()
        return
    
    print("✅ Server started successfully")
    
    # Start 2 clients with custom tree configuration
    client_processes = []
    client_logs = []
    
    for client_num in [1, 2]:
        print(f"👤 Starting client {client_num} with {trees_per_client} trees...")
        
        client_env = env.copy()
        client_env["ICP_CLIENT_IDENTITY_NAME"] = f"fl_client_{client_num}"
        client_env["CLIENT_NAME"] = f"Test Provider {client_num}"
        client_env["CLIENT_ORGANIZATION"] = f"Test Hospital {client_num}"
        
        client_log = open(f"logs/test_client_{client_num}.log", "w")
        client_process = subprocess.Popen(
            ["uv", "run", "python", "client/client.py", 
             "--dataset", f"dataset/clients/client{client_num}_data.csv",
             "--trees", str(trees_per_client)],
            stdout=client_log,
            stderr=subprocess.STDOUT,
            text=True,
            env=client_env
        )
        
        client_processes.append(client_process)
        client_logs.append(client_log)
        time.sleep(1)
    
    print(f"✅ Started 2 clients with {trees_per_client} trees each")
    print(f"📊 Expected total trees per round: {2 * trees_per_client}")
    
    # Monitor progress
    print("\n⏳ Monitoring training progress...")
    start_time = time.time()
    
    while True:
        if server_process.poll() is not None:
            print("\n🏁 Training completed!")
            break
        
        elapsed = int(time.time() - start_time)
        running_clients = sum(1 for p in client_processes if p.poll() is None)
        print(f"\r   ⏱️  Elapsed: {elapsed}s | Server: Running | Clients: {running_clients}/2 running", 
              end="", flush=True)
        
        time.sleep(5)
    
    # Cleanup
    server_log.close()
    for log in client_logs:
        log.close()
    
    for process in client_processes:
        if process.poll() is None:
            process.terminate()
            process.wait()
    
    print(f"\n📋 Test completed! Check logs/test_*.log for details")
    print(f"🌳 Configuration: {trees_per_client} trees per client")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test tree configuration in federated learning")
    parser.add_argument("--trees", type=int, default=50,
                        help="Number of trees per client (default: 50)")
    
    args = parser.parse_args()
    test_tree_configuration(args.trees)
