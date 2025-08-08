#!/usr/bin/env python3
"""
Test script to demonstrate client authentication system.
"""

import subprocess
import time
import os
import sys

def print_banner():
    """Print test banner."""
    print("\n" + "="*80)
    print("🔐 TESTING CLIENT AUTHENTICATION SYSTEM")
    print("="*80)

def test_unauthenticated_client():
    """Test what happens when an unauthenticated client tries to connect."""
    print("\n🧪 Test 1: Unauthenticated Client Connection")
    print("-" * 50)
    
    # Start server
    print("🖥️ Starting server...")
    env = os.environ.copy()
    env["ICP_CLIENT_IDENTITY_NAME"] = "fl_server"
    env["ICP_NETWORK"] = "local"
    env["ICP_CANISTER_ID"] = "uxrrr-q7777-77774-qaaaq-cai"
    
    server_log = open("logs/auth_test_server.log", "w")
    server_process = subprocess.Popen(
        ["uv", "run", "python", "server/server.py", "--rounds", "1", "--max-trees", "200"],
        stdout=server_log,
        stderr=subprocess.STDOUT,
        text=True,
        env=env
    )
    
    time.sleep(3)  # Wait for server to start
    
    if server_process.poll() is not None:
        print("❌ Server failed to start")
        server_log.close()
        return False
    
    print("✅ Server started successfully")
    
    # Start unauthenticated client (using a fake identity)
    print("👤 Starting unauthenticated client...")
    
    client_env = env.copy()
    client_env["ICP_CLIENT_IDENTITY_NAME"] = "fake_client"  # Not approved
    client_env["CLIENT_NAME"] = "Unauthorized Client"
    client_env["CLIENT_ORGANIZATION"] = "Fake Organization"
    
    client_log = open("logs/auth_test_client.log", "w")
    client_process = subprocess.Popen(
        ["uv", "run", "python", "client/client.py", 
         "--dataset", "dataset/clients/client1_data.csv",
         "--trees", "25"],
        stdout=client_log,
        stderr=subprocess.STDOUT,
        text=True,
        env=client_env
    )
    
    # Monitor for 30 seconds
    print("⏳ Monitoring authentication behavior...")
    start_time = time.time()
    
    while time.time() - start_time < 30:
        if server_process.poll() is not None:
            print("🏁 Server completed")
            break
        
        if client_process.poll() is not None:
            print("🏁 Client completed")
            break
        
        elapsed = int(time.time() - start_time)
        print(f"\r   ⏱️  Elapsed: {elapsed}s", end="", flush=True)
        time.sleep(1)
    
    # Cleanup
    server_log.close()
    client_log.close()
    
    if server_process.poll() is None:
        server_process.terminate()
        server_process.wait()
    
    if client_process.poll() is None:
        client_process.terminate()
        client_process.wait()
    
    print("\n📋 Test completed. Check logs/auth_test_*.log for details")
    return True

def test_client_registration():
    """Test client registration process."""
    print("\n🧪 Test 2: Client Registration Process")
    print("-" * 50)
    
    print("👤 Testing client registration...")
    
    # Create a test client with specific identity
    env = os.environ.copy()
    env["ICP_CLIENT_IDENTITY_NAME"] = "test_client_auth"
    env["CLIENT_NAME"] = "Test Authentication Client"
    env["CLIENT_ORGANIZATION"] = "Test Auth Organization"
    env["CLIENT_LOCATION"] = "Test City, Test Country"
    env["CLIENT_CONTACT_EMAIL"] = "test-auth@example.com"
    
    # Run a quick client registration test
    client_log = open("logs/registration_test.log", "w")
    client_process = subprocess.Popen(
        ["uv", "run", "python", "-c", """
import sys
import os
sys.path.append('.')
from client.client import CVDClient
from client.utils.model import CVDModel
from client.utils.data_preprocessing import load_and_preprocess_data

# Load test data
X, y = load_and_preprocess_data('dataset/clients/client1_data.csv')

# Create model and client (this will trigger registration)
model = CVDModel(n_estimators=25)
client = CVDClient(model, X, y)

print(f"Registration completed. Principal ID: {client.principal_id}")
print(f"Authentication status: {client.is_authenticated}")
"""],
        stdout=client_log,
        stderr=subprocess.STDOUT,
        text=True,
        env=env
    )
    
    client_process.wait()
    client_log.close()
    
    print("✅ Registration test completed")
    print("📋 Check logs/registration_test.log for details")
    
    return True

def show_authentication_status():
    """Show current authentication status."""
    print("\n📊 Current Authentication Status")
    print("-" * 50)
    
    try:
        # Try to list pending clients
        result = subprocess.run(
            ["uv", "run", "python", "manage_client_auth.py", "list-pending"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("📋 Pending Clients:")
            print(result.stdout)
        else:
            print("❌ Failed to list pending clients")
            print(result.stderr)
        
        # Try to list active clients
        result = subprocess.run(
            ["uv", "run", "python", "manage_client_auth.py", "list-active"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("👥 Active Clients:")
            print(result.stdout)
        else:
            print("❌ Failed to list active clients")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Error checking authentication status: {e}")
        return False
    
    return True

def main():
    """Main test function."""
    print_banner()
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    print("\n🎯 This script tests the client authentication system:")
    print("   1. Tests unauthenticated client behavior")
    print("   2. Tests client registration process")
    print("   3. Shows current authentication status")
    
    # Test 1: Unauthenticated client
    if not test_unauthenticated_client():
        print("❌ Test 1 failed")
        return 1
    
    # Test 2: Client registration
    if not test_client_registration():
        print("❌ Test 2 failed")
        return 1
    
    # Show status
    if not show_authentication_status():
        print("❌ Status check failed")
        return 1
    
    print("\n" + "="*80)
    print("🎉 AUTHENTICATION SYSTEM TESTS COMPLETED")
    print("="*80)
    print("\n📋 Next Steps:")
    print("1. Check log files in logs/ directory")
    print("2. Use 'python manage_client_auth.py interactive' to approve clients")
    print("3. Run federated learning with approved clients")
    print("="*80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
