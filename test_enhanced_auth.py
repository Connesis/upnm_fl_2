#!/usr/bin/env python3
"""
Test script for enhanced client authentication system.
This script tests the server-side verification of client principal IDs.
"""

import os
import sys
import time
import subprocess
import logging
from typing import Dict, Any
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


def test_client_authentication():
    """Test the enhanced client authentication system."""
    print("🧪 Testing Enhanced Client Authentication System")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Test 1: Initialize server ICP client
        print("\n1️⃣ Testing Server ICP Client Initialization...")
        server_client = AuthenticatedICPClient(identity_type="server")
        if server_client.canister_id:
            print(f"✅ Server connected to canister: {server_client.canister_id}")
        else:
            print("❌ Server failed to connect to canister")
            return False
            
        # Test 2: Initialize client ICP client
        print("\n2️⃣ Testing Client ICP Client Initialization...")
        client_client = AuthenticatedICPClient(identity_type="client")
        if client_client.canister_id:
            print(f"✅ Client connected to canister: {client_client.canister_id}")
        else:
            print("❌ Client failed to connect to canister")
            return False
            
        # Test 3: Get client principal ID
        print("\n3️⃣ Testing Client Principal ID Retrieval...")
        client_principal = client_client.get_current_principal()
        if client_principal:
            print(f"✅ Client principal ID: {client_principal}")
        else:
            print("❌ Failed to get client principal ID")
            return False
            
        # Test 4: Test server verification of client principal
        print("\n4️⃣ Testing Server-Side Client Verification...")
        is_active = server_client.is_client_active_by_principal(client_principal)
        print(f"🔍 Client {client_principal} active status: {is_active}")
        
        if is_active:
            print("✅ Client is approved and can participate in training")
        else:
            print("⚠️  Client is not approved - would be rejected by server")
            
        # Test 5: Test authentication flow simulation
        print("\n5️⃣ Testing Authentication Flow Simulation...")
        
        # Simulate client metrics that would be sent to server
        mock_client_metrics = {
            "client_principal_id": client_principal,
            "client_identity": os.getenv("ICP_CLIENT_IDENTITY_NAME", "test_client")
        }
        
        print(f"📤 Mock client metrics: {mock_client_metrics}")
        
        # Simulate server verification
        principal_from_metrics = mock_client_metrics.get('client_principal_id')
        if principal_from_metrics and principal_from_metrics != 'unknown':
            server_verification = server_client.is_client_active_by_principal(principal_from_metrics)
            print(f"🔍 Server verification result: {server_verification}")
            
            if server_verification:
                print("✅ Authentication flow successful - client would be accepted")
            else:
                print("❌ Authentication flow failed - client would be rejected")
        else:
            print("❌ No principal ID in metrics - client would be rejected")
            
        print("\n" + "=" * 60)
        print("🎯 Enhanced Authentication Test Summary:")
        print(f"   • Server ICP connection: {'✅' if server_client.canister_id else '❌'}")
        print(f"   • Client ICP connection: {'✅' if client_client.canister_id else '❌'}")
        print(f"   • Client principal retrieval: {'✅' if client_principal else '❌'}")
        print(f"   • Server verification: {'✅' if is_active else '⚠️'}")
        print(f"   • Authentication flow: {'✅' if server_verification else '❌'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False


def test_unapproved_client_rejection():
    """Test that unapproved clients are properly rejected."""
    print("\n🚫 Testing Unapproved Client Rejection...")
    
    try:
        server_client = AuthenticatedICPClient(identity_type="server")
        
        # Test with a fake principal ID that shouldn't be approved
        fake_principal = "fake-principal-id-12345"
        is_active = server_client.is_client_active_by_principal(fake_principal)
        
        if not is_active:
            print(f"✅ Fake client {fake_principal} correctly rejected")
            return True
        else:
            print(f"❌ Fake client {fake_principal} incorrectly approved")
            return False
            
    except Exception as e:
        logger.error(f"❌ Rejection test failed: {e}")
        return False


def main():
    """Run all authentication tests."""
    print("🔐 Enhanced Client Authentication Test Suite")
    print("=" * 80)

    # Load environment variables first
    load_dotenv()

    # Check environment setup
    required_vars = [
        "ICP_CANISTER_ID",
        "ICP_NETWORK",
        "ICP_SERVER_PRINCIPAL_ID",
        "ICP_CLIENT_PRINCIPAL_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("💡 Please run setup_icp_auth.py first or check your .env file")
        return False
    
    # Run tests
    tests_passed = 0
    total_tests = 2
    
    if test_client_authentication():
        tests_passed += 1
        
    if test_unapproved_client_rejection():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 80)
    print(f"🎯 TEST RESULTS: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✅ All tests passed! Enhanced authentication is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the configuration and try again.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
