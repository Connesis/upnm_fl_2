#!/usr/bin/env python3
"""
Test script for federated learning with proper identity management.
Tests the system with fl_client_1, fl_client_2, fl_client_3, and fl_server identities.
"""

import subprocess
import time
import os
import sys

def check_identity_exists(identity_name):
    """Check if a dfx identity exists."""
    try:
        result = subprocess.run(
            ["dfx", "identity", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        return identity_name in result.stdout
    except subprocess.CalledProcessError:
        return False

def create_identity_if_missing(identity_name):
    """Create a dfx identity if it doesn't exist."""
    if check_identity_exists(identity_name):
        print(f"✅ Identity {identity_name} already exists")
        return True
    
    print(f"🔧 Creating identity {identity_name}...")
    try:
        subprocess.run(
            ["dfx", "identity", "new", identity_name, "--storage-mode", "password-protected"],
            check=True,
            input="\n",  # Press enter for password prompt
            text=True
        )
        print(f"✅ Identity {identity_name} created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create identity {identity_name}: {e}")
        return False

def get_principal_id(identity_name):
    """Get the principal ID for an identity."""
    try:
        # Switch to the identity
        subprocess.run(["dfx", "identity", "use", identity_name], check=True, capture_output=True)
        
        # Get principal ID
        result = subprocess.run(
            ["dfx", "identity", "get-principal"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def setup_test_identities():
    """Set up all required identities for testing."""
    print("🔧 Setting up test identities...")
    
    identities = ["fl_server", "fl_client_1", "fl_client_2", "fl_client_3"]
    principals = {}
    
    for identity in identities:
        if create_identity_if_missing(identity):
            principal = get_principal_id(identity)
            if principal:
                principals[identity] = principal
                print(f"   📋 {identity}: {principal}")
            else:
                print(f"   ❌ Failed to get principal for {identity}")
                return None
        else:
            print(f"   ❌ Failed to create {identity}")
            return None
    
    return principals

def test_identity_switching():
    """Test switching between identities."""
    print("\n🔄 Testing identity switching...")
    
    identities = ["fl_server", "fl_client_1", "fl_client_2", "fl_client_3"]
    
    for identity in identities:
        try:
            subprocess.run(["dfx", "identity", "use", identity], check=True, capture_output=True)
            
            # Verify the switch worked
            result = subprocess.run(
                ["dfx", "identity", "whoami"],
                capture_output=True,
                text=True,
                check=True
            )
            
            current_identity = result.stdout.strip()
            if current_identity == identity:
                print(f"   ✅ Successfully switched to {identity}")
            else:
                print(f"   ❌ Failed to switch to {identity} (current: {current_identity})")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Error switching to {identity}: {e}")
            return False
    
    return True

def run_federated_learning_test():
    """Run the federated learning test with proper identities."""
    print("\n🚀 Running federated learning test with identity management...")
    
    # Check if datasets exist
    datasets = [
        "dataset/clients/client1_data.csv",
        "dataset/clients/client2_data.csv", 
        "dataset/clients/client3_data.csv"
    ]
    
    missing_datasets = [d for d in datasets if not os.path.exists(d)]
    if missing_datasets:
        print("❌ Missing datasets:")
        for dataset in missing_datasets:
            print(f"   • {dataset}")
        print("Please create client datasets first.")
        return False
    
    # Use the modified run_federated_learning.py script
    try:
        print("   🔄 Starting federated learning with identity management...")
        result = subprocess.run(
            ["uv", "run", "python", "run_federated_learning.py"],
            timeout=300,  # 5 minute timeout
            check=True
        )
        print("   ✅ Federated learning test completed successfully!")
        return True
        
    except subprocess.TimeoutExpired:
        print("   ⏰ Test timed out after 5 minutes")
        return False
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Federated learning test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 Identity Management Test Suite")
    print("=" * 60)
    
    # Step 1: Set up identities
    principals = setup_test_identities()
    if not principals:
        print("❌ Failed to set up identities")
        return 1
    
    # Step 2: Test identity switching
    if not test_identity_switching():
        print("❌ Identity switching test failed")
        return 1
    
    # Step 3: Run federated learning test
    if not run_federated_learning_test():
        print("❌ Federated learning test failed")
        return 1
    
    print("\n" + "=" * 60)
    print("🎉 All identity management tests passed!")
    print("\nIdentity Summary:")
    for identity, principal in principals.items():
        print(f"   • {identity}: {principal}")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
