#!/usr/bin/env python3
"""
Test script to verify client authentication is working properly.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add project paths
sys.path.append(os.path.dirname(__file__))
from icp_auth_client import AuthenticatedICPClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def test_client_authentication(client_identity: str):
    """Test authentication for a specific client identity."""
    print(f"\n🧪 Testing authentication for {client_identity}")
    print("-" * 50)
    
    try:
        # Set environment for this client
        os.environ["ICP_CLIENT_IDENTITY_NAME"] = client_identity
        
        # Initialize ICP client
        icp_client = AuthenticatedICPClient(identity_type="client")
        
        if not icp_client.canister_id:
            print("❌ Failed to connect to canister")
            return False
        
        print(f"✅ Connected to canister: {icp_client.canister_id}")
        
        # Get principal ID
        principal_id = icp_client.get_current_principal()
        if not principal_id:
            print("❌ Failed to get principal ID")
            return False
        
        print(f"🔑 Principal ID: {principal_id}")
        
        # Check if registered
        is_registered = icp_client.is_client_registered(principal_id)
        print(f"📝 Registered: {is_registered}")
        
        # Check if active
        is_active = icp_client.is_client_active(principal_id)
        print(f"✅ Active/Approved: {is_active}")
        
        if is_registered and is_active:
            print("🎉 Client is fully authenticated!")
            return True
        elif is_registered and not is_active:
            print("⚠️  Client is registered but not approved")
            return False
        else:
            print("❌ Client is not registered")
            return False
            
    except Exception as e:
        print(f"❌ Error testing {client_identity}: {e}")
        return False

def main():
    """Test all client identities."""
    load_dotenv()
    
    print("🔐 Client Authentication Test")
    print("=" * 60)
    
    client_identities = ["fl_client_1", "fl_client_2", "fl_client_3"]
    results = {}
    
    for identity in client_identities:
        results[identity] = test_client_authentication(identity)
    
    print("\n" + "=" * 60)
    print("🎯 AUTHENTICATION TEST RESULTS")
    print("=" * 60)
    
    for identity, success in results.items():
        status = "✅ AUTHENTICATED" if success else "❌ NOT AUTHENTICATED"
        print(f"{identity}: {status}")
    
    all_authenticated = all(results.values())
    
    if all_authenticated:
        print("\n🎉 All clients are authenticated and ready for training!")
    else:
        print("\n⚠️  Some clients are not authenticated. Check approval status.")
    
    return all_authenticated

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
