#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced federated learning system with:
1. Configurable minimum client requirements
2. Client retry logic with server waiting
"""

import subprocess
import time
import os
import sys
from typing import List, Tuple


def start_server_with_min_clients(rounds: int = 2, min_clients: int = 2, port: int = 8080) -> subprocess.Popen:
    """
    Start the federated learning server with minimum client requirements.
    
    Args:
        rounds: Number of federated learning rounds
        min_clients: Minimum number of clients required
        port: Server port
        
    Returns:
        Server process
    """
    print(f"🚀 Starting server with minimum {min_clients} clients requirement...")
    
    # Create server log file
    os.makedirs("logs", exist_ok=True)
    server_log = open("logs/enhanced_server.log", "w")
    
    server_process = subprocess.Popen(
        ["uv", "run", "python", "server/server.py", 
         "--rounds", str(rounds), 
         "--min-clients", str(min_clients),
         "--port", str(port)],
        stdout=server_log,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    print(f"✅ Server started (PID: {server_process.pid})")
    print(f"   📝 Server logs: logs/enhanced_server.log")
    print(f"   ⚙️  Configuration: {rounds} rounds, min {min_clients} clients, port {port}")
    
    return server_process, server_log


def start_client_with_retry(client_id: int, dataset: str, max_wait_time: int = 120, 
                           retry_interval: int = 3, port: int = 8080) -> subprocess.Popen:
    """
    Start a client with retry logic.
    
    Args:
        client_id: Client identifier
        dataset: Path to client dataset
        max_wait_time: Maximum time to wait for server
        retry_interval: Initial retry interval
        port: Server port
        
    Returns:
        Client process
    """
    print(f"👤 Starting client {client_id} with retry logic...")
    
    # Set server address environment variable
    env = os.environ.copy()
    env["SERVER_ADDRESS"] = f"127.0.0.1:{port}"
    
    # Create client log file
    client_log = open(f"logs/enhanced_client_{client_id}.log", "w")
    
    client_process = subprocess.Popen(
        ["uv", "run", "python", "client/client.py", 
         "--dataset", dataset,
         "--max-wait-time", str(max_wait_time),
         "--retry-interval", str(retry_interval)],
        stdout=client_log,
        stderr=subprocess.STDOUT,
        text=True,
        env=env
    )
    
    print(f"✅ Client {client_id} started (PID: {client_process.pid})")
    print(f"   📝 Client logs: logs/enhanced_client_{client_id}.log")
    print(f"   📊 Dataset: {dataset}")
    print(f"   ⏱️  Max wait: {max_wait_time}s, retry interval: {retry_interval}s")
    
    return client_process, client_log


def test_scenario_1_clients_before_server():
    """
    Test Scenario 1: Start clients before server to test retry logic.
    """
    print("\n" + "="*80)
    print("🧪 TEST SCENARIO 1: Clients Start Before Server")
    print("="*80)
    print("This tests the client retry logic when server is not yet available.")
    print()
    
    processes = []
    logs = []
    
    try:
        # Start clients first (server not running yet)
        print("📋 Step 1: Starting clients before server...")
        
        client_configs = [
            (1, "dataset/clients/client1_data.csv"),
            (2, "dataset/clients/client2_data.csv"),
        ]
        
        for client_id, dataset in client_configs:
            client_process, client_log = start_client_with_retry(
                client_id, dataset, max_wait_time=60, retry_interval=3
            )
            processes.append(client_process)
            logs.append(client_log)
            time.sleep(2)  # Small delay between clients
        
        print(f"\n📋 Step 2: Waiting 10 seconds to let clients attempt connections...")
        time.sleep(10)
        
        # Now start the server
        print("📋 Step 3: Starting server (clients should connect automatically)...")
        server_process, server_log = start_server_with_min_clients(
            rounds=1, min_clients=2, port=8080
        )
        processes.append(server_process)
        logs.append(server_log)
        
        print("\n📋 Step 4: Monitoring federated learning progress...")
        print("   (This may take a few minutes)")
        
        # Wait for server to complete
        server_process.wait()
        
        print("\n✅ Scenario 1 completed!")
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    finally:
        # Clean up processes
        print("\n🧹 Cleaning up processes...")
        for process in processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        # Close log files
        for log in logs:
            log.close()


def test_scenario_2_server_first():
    """
    Test Scenario 2: Start server first, then clients (traditional approach).
    """
    print("\n" + "="*80)
    print("🧪 TEST SCENARIO 2: Server First, Then Clients")
    print("="*80)
    print("This tests the traditional approach with enhanced minimum client settings.")
    print()
    
    processes = []
    logs = []
    
    try:
        # Start server first
        print("📋 Step 1: Starting server with minimum 3 clients requirement...")
        server_process, server_log = start_server_with_min_clients(
            rounds=1, min_clients=3, port=8081
        )
        processes.append(server_process)
        logs.append(server_log)
        
        print("\n📋 Step 2: Waiting 5 seconds for server to initialize...")
        time.sleep(5)
        
        # Start clients
        print("📋 Step 3: Starting clients one by one...")
        
        client_configs = [
            (1, "dataset/clients/client1_data.csv"),
            (2, "dataset/clients/client2_data.csv"),
            (3, "dataset/clients/client3_data.csv"),
        ]
        
        for client_id, dataset in client_configs:
            client_process, client_log = start_client_with_retry(
                client_id, dataset, max_wait_time=30, retry_interval=2, port=8081
            )
            processes.append(client_process)
            logs.append(client_log)
            time.sleep(3)  # Delay between clients
        
        print("\n📋 Step 4: Monitoring federated learning progress...")
        print("   (Training should start once all 3 clients connect)")
        
        # Wait for server to complete
        server_process.wait()
        
        print("\n✅ Scenario 2 completed!")
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    finally:
        # Clean up processes
        print("\n🧹 Cleaning up processes...")
        for process in processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        # Close log files
        for log in logs:
            log.close()


def main():
    """Main function to run the enhanced federated learning tests."""
    print("🔬 Enhanced Federated Learning System Tests")
    print("=" * 80)
    print("Testing new features:")
    print("  • Configurable minimum client requirements")
    print("  • Client retry logic with exponential backoff")
    print("  • Server waiting capability")
    print()
    
    # Check if datasets exist
    required_datasets = [
        "dataset/clients/client1_data.csv",
        "dataset/clients/client2_data.csv", 
        "dataset/clients/client3_data.csv"
    ]
    
    missing_datasets = [d for d in required_datasets if not os.path.exists(d)]
    if missing_datasets:
        print("❌ Missing required datasets:")
        for dataset in missing_datasets:
            print(f"   • {dataset}")
        print("\nPlease ensure client datasets are available before running tests.")
        return 1
    
    try:
        # Run test scenarios
        test_scenario_1_clients_before_server()
        
        print("\n" + "⏳" * 20)
        print("Waiting 10 seconds between scenarios...")
        time.sleep(10)
        
        test_scenario_2_server_first()
        
        print("\n" + "="*80)
        print("🎉 All test scenarios completed!")
        print("="*80)
        print("📁 Check the logs/ directory for detailed execution logs:")
        print("   • logs/enhanced_server.log")
        print("   • logs/enhanced_client_*.log")
        print("="*80)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
