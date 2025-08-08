#!/usr/bin/env python3
"""
Debug script to test server authentication verification.
"""

import os
import sys
from dotenv import load_dotenv

# Add project paths
sys.path.append(os.path.dirname(__file__))
from icp_auth_client import AuthenticatedICPClient

def test_server_verification():
    """Test server's ability to verify client authentication."""
    load_dotenv()
    
    print("🔍 Testing Server Authentication Verification")
    print("=" * 60)
    
    # Test with server identity
    print("\n1️⃣ Testing with fl_server identity:")
    try:
        os.environ["ICP_CLIENT_IDENTITY_NAME"] = "fl_server"
        server_client = AuthenticatedICPClient(identity_type="server")
        # Override the identity name to use fl_server
        server_client.identity_name = "fl_server"
        
        if server_client.canister_id:
            print(f"✅ Server connected to canister: {server_client.canister_id}")
            
            # Test verifying each client
            client_principals = [
                "xoqpj-5c7wg-idyjk-i5ply-fetwi-salbi-c5z2t-5nt7k-6xojd-uic3u-3ae",  # fl_client_1
                "eaxhv-xeqvm-eypy2-y7tmi-hunii-5y6ux-dvq7j-x6k3w-bcb7j-dwwmy-iae",  # fl_client_2
                "it3pk-ql7f2-ohobl-eqmpy-k45ny-dflvw-olipk-t35ye-pd3bx-lj2dp-fae"   # fl_client_3
            ]
            
            for i, principal_id in enumerate(client_principals, 1):
                print(f"\n   Testing client {i}: {principal_id}")
                try:
                    is_active = server_client.is_client_active_by_principal(principal_id)
                    print(f"   Result: {'✅ ACTIVE' if is_active else '❌ NOT ACTIVE'}")
                except Exception as e:
                    print(f"   Error: {e}")
        else:
            print("❌ Server failed to connect to canister")
            
    except Exception as e:
        print(f"❌ Server test failed: {e}")
    
    # Test with client identity for comparison
    print("\n2️⃣ Testing with fl_client_1 identity for comparison:")
    try:
        os.environ["ICP_CLIENT_IDENTITY_NAME"] = "fl_client_1"
        client_client = AuthenticatedICPClient(identity_type="client")
        
        if client_client.canister_id:
            print(f"✅ Client connected to canister: {client_client.canister_id}")
            
            principal_id = "xoqpj-5c7wg-idyjk-i5ply-fetwi-salbi-c5z2t-5nt7k-6xojd-uic3u-3ae"
            print(f"   Testing own principal: {principal_id}")
            
            is_registered = client_client.is_client_registered(principal_id)
            is_active = client_client.is_client_active(principal_id)
            
            print(f"   Registered: {'✅' if is_registered else '❌'}")
            print(f"   Active: {'✅' if is_active else '❌'}")
        else:
            print("❌ Client failed to connect to canister")
            
    except Exception as e:
        print(f"❌ Client test failed: {e}")

if __name__ == "__main__":
    test_server_verification()
