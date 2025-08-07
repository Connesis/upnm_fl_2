#!/usr/bin/env python3
"""
Test script to verify correct identity loading for server and clients.
This script tests that:
- Server loads fl_server identity
- Client 1 loads fl_client_1 identity  
- Client 2 loads fl_client_2 identity
- Client 3 loads fl_client_3 identity
"""

import subprocess
import time
import os
import sys
from typing import List, Tuple


def test_server_identity():
    """Test that server loads fl_server identity correctly."""
    print("🧪 Testing Server Identity Loading...")
    
    # Set server environment
    env = os.environ.copy()
    env["ICP_CLIENT_IDENTITY_NAME"] = "fl_server"
    env["ICP_NETWORK"] = "local"
    env["ICP_CANISTER_ID"] = "test-canister-id"
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Start server with identity
    server_log = open("logs/test_server_identity.log", "w")
    
    print("   🚀 Starting server with fl_server identity...")
    server_process = subprocess.Popen(
        ["uv", "run", "python", "server/server.py", "--rounds", "1", "--min-clients", "1"],
        stdout=server_log,
        stderr=subprocess.STDOUT,
        text=True,
        env=env
    )
    
    # Wait for server to initialize
    time.sleep(5)
    
    # Check if server is running
    if server_process.poll() is None:
        print("   ✅ Server started successfully")
        
        # Read log file to verify identity
        server_log.close()
        with open("logs/test_server_identity.log", "r") as f:
            log_content = f.read()
            
        if "ICP_CLIENT_IDENTITY_NAME: fl_server" in log_content:
            print("   ✅ Server identity loaded correctly: fl_server")
            identity_verified = True
        else:
            print("   ❌ Server identity not found in logs")
            identity_verified = False
            
        # Terminate server
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
            
        return identity_verified
    else:
        print("   ❌ Server failed to start")
        server_log.close()
        return False


def test_client_identity(client_num: int, expected_identity: str):
    """Test that client loads the correct identity."""
    print(f"🧪 Testing Client {client_num} Identity Loading...")
    
    # Set client environment
    env = os.environ.copy()
    env["ICP_CLIENT_IDENTITY_NAME"] = expected_identity
    env["SERVER_ADDRESS"] = "127.0.0.1:8080"  # Non-existent server for quick test
    env["CLIENT_NAME"] = f"Test Client {client_num}"
    env["CLIENT_ORGANIZATION"] = f"Test Hospital {client_num}"
    
    # Start client with identity (it will fail to connect, but we just want to check identity loading)
    client_log = open(f"logs/test_client_{client_num}_identity.log", "w")
    
    print(f"   🚀 Starting client {client_num} with {expected_identity} identity...")
    client_process = subprocess.Popen(
        ["uv", "run", "python", "client/client.py", 
         "--dataset", f"dataset/clients/client{client_num}_data.csv",
         "--max-wait-time", "10",  # Short wait time for quick test
         "--retry-interval", "2"],
        stdout=client_log,
        stderr=subprocess.STDOUT,
        text=True,
        env=env
    )
    
    # Wait for client to initialize and attempt connection
    time.sleep(8)
    
    # Terminate client (it won't be able to connect anyway)
    client_process.terminate()
    try:
        client_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        client_process.kill()
    
    # Check log file for identity
    client_log.close()
    with open(f"logs/test_client_{client_num}_identity.log", "r") as f:
        log_content = f.read()
    
    if f"ICP_CLIENT_IDENTITY_NAME: {expected_identity}" in log_content:
        print(f"   ✅ Client {client_num} identity loaded correctly: {expected_identity}")
        return True
    else:
        print(f"   ❌ Client {client_num} identity not found in logs")
        print(f"   📝 Expected: {expected_identity}")
        return False


def test_federated_learning_with_identities():
    """Test a complete federated learning session with proper identities."""
    print("🧪 Testing Complete Federated Learning with Identities...")
    
    processes = []
    logs = []
    
    try:
        # Start server with fl_server identity
        print("   📋 Step 1: Starting server with fl_server identity...")
        env = os.environ.copy()
        env["ICP_CLIENT_IDENTITY_NAME"] = "fl_server"
        
        server_log = open("logs/test_fl_server.log", "w")
        server_process = subprocess.Popen(
            ["uv", "run", "python", "server/server.py", "--rounds", "1", "--min-clients", "2"],
            stdout=server_log,
            stderr=subprocess.STDOUT,
            text=True,
            env=env
        )
        processes.append(server_process)
        logs.append(server_log)
        
        # Wait for server to start
        time.sleep(5)
        
        # Start clients with specific identities
        client_configs = [
            (1, "fl_client_1", "dataset/clients/client1_data.csv"),
            (2, "fl_client_2", "dataset/clients/client2_data.csv"),
        ]
        
        for client_num, identity, dataset in client_configs:
            print(f"   📋 Step {client_num + 1}: Starting client {client_num} with {identity} identity...")
            
            env = os.environ.copy()
            env["ICP_CLIENT_IDENTITY_NAME"] = identity
            env["SERVER_ADDRESS"] = "127.0.0.1:8080"
            env["CLIENT_NAME"] = f"Test Client {client_num}"
            
            client_log = open(f"logs/test_fl_client_{client_num}.log", "w")
            client_process = subprocess.Popen(
                ["uv", "run", "python", "client/client.py", 
                 "--dataset", dataset,
                 "--max-wait-time", "60"],
                stdout=client_log,
                stderr=subprocess.STDOUT,
                text=True,
                env=env
            )
            processes.append(client_process)
            logs.append(client_log)
            
            time.sleep(3)  # Delay between clients
        
        print("   📋 Step 4: Waiting for federated learning to complete...")
        
        # Wait for server to complete
        server_process.wait(timeout=120)
        
        print("   ✅ Federated learning completed successfully!")
        
        # Verify identities in log files
        identity_results = []
        
        # Check server identity
        with open("logs/test_fl_server.log", "r") as f:
            server_log_content = f.read()
        server_identity_ok = "ICP_CLIENT_IDENTITY_NAME: fl_server" in server_log_content
        identity_results.append(("Server", "fl_server", server_identity_ok))
        
        # Check client identities
        for client_num, expected_identity, _ in client_configs:
            with open(f"logs/test_fl_client_{client_num}.log", "r") as f:
                client_log_content = f.read()
            client_identity_ok = f"ICP_CLIENT_IDENTITY_NAME: {expected_identity}" in client_log_content
            identity_results.append((f"Client {client_num}", expected_identity, client_identity_ok))
        
        return identity_results
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return []
    finally:
        # Clean up processes
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
    """Main function to run identity loading tests."""
    print("🔬 Identity Loading Tests for Federated Learning System")
    print("=" * 80)
    print("Testing that server and clients load correct identities from environment variables")
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
        # Test 1: Server identity loading
        server_identity_ok = test_server_identity()
        
        print()
        
        # Test 2: Individual client identity loading
        client_identity_results = []
        client_configs = [
            (1, "fl_client_1"),
            (2, "fl_client_2"),
            (3, "fl_client_3"),
        ]
        
        for client_num, expected_identity in client_configs:
            result = test_client_identity(client_num, expected_identity)
            client_identity_results.append((client_num, expected_identity, result))
            print()
        
        # Test 3: Complete federated learning with identities
        print("🧪 Running complete federated learning test...")
        fl_identity_results = test_federated_learning_with_identities()
        
        # Summary
        print("\n" + "="*80)
        print("📋 IDENTITY LOADING TEST RESULTS")
        print("="*80)
        
        print(f"🖥️  Server Identity Test: {'✅ PASS' if server_identity_ok else '❌ FAIL'}")
        
        print("\n👥 Client Identity Tests:")
        for client_num, expected_identity, result in client_identity_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   Client {client_num} ({expected_identity}): {status}")
        
        if fl_identity_results:
            print("\n🔄 Federated Learning Identity Tests:")
            for component, identity, result in fl_identity_results:
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"   {component} ({identity}): {status}")
        
        # Overall result
        all_passed = (server_identity_ok and 
                     all(result for _, _, result in client_identity_results) and
                     all(result for _, _, result in fl_identity_results))
        
        print("\n" + "="*80)
        if all_passed:
            print("🎉 ALL IDENTITY TESTS PASSED!")
            print("✅ Server and clients are correctly loading identities from environment variables")
        else:
            print("❌ SOME IDENTITY TESTS FAILED!")
            print("⚠️  Check the log files in logs/ directory for detailed debugging information")
        
        print("="*80)
        print("\n📁 Log files created for debugging:")
        print("   • logs/test_server_identity.log")
        print("   • logs/test_client_*_identity.log")
        print("   • logs/test_fl_*.log")
        
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
