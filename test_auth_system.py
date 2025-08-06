#!/usr/bin/env python3
"""
Test script for the ICP federated learning authentication system.
"""
import os
import sys
import time
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from icp_auth_client import get_admin_client, get_server_client, get_client


def test_admin_functions():
    """Test admin functionality."""
    print("🔧 Testing Admin Functions...")
    
    try:
        admin_client = get_admin_client()
        
        # Test admin initialization
        print("  Testing admin initialization...")
        result = admin_client.init_admin()
        print(f"    Init admin: {'✅ Success' if result else '⚠️  Already initialized or failed'}")
        
        # Test getting admin principal
        admin_principal = admin_client.get_admin_principal()
        print(f"    Admin principal: {admin_principal}")
        
        # Test current principal
        current_principal = admin_client.get_current_principal()
        print(f"    Current principal: {current_principal}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Admin test failed: {e}")
        return False


def test_client_registration():
    """Test client registration workflow."""
    print("\n👥 Testing Client Registration...")
    
    try:
        client = get_client()
        
        # Test client registration
        print("  Testing client registration...")
        status = client.register_client_with_metadata(
            client_name="Test Client",
            organization="Test Hospital",
            location="Test City",
            contact_email="test@example.com"
        )
        print(f"    Registration status: {status}")
        
        # Test getting current principal
        current_principal = client.get_current_principal()
        print(f"    Client principal: {current_principal}")
        
        return current_principal
        
    except Exception as e:
        print(f"    ❌ Client registration test failed: {e}")
        return None


def test_admin_approval(client_principal):
    """Test admin approval workflow."""
    print("\n✅ Testing Admin Approval...")
    
    if not client_principal:
        print("    ⚠️  No client principal to test approval")
        return False
    
    try:
        admin_client = get_admin_client()
        
        # Test listing pending clients
        print("  Testing pending clients list...")
        pending_clients = admin_client.get_pending_clients()
        print(f"    Pending clients: {len(pending_clients)}")
        
        # Test client approval
        print(f"  Testing client approval for: {client_principal}")
        result = admin_client.admin_approve_client(client_principal)
        print(f"    Approval result: {'✅ Success' if result else '❌ Failed'}")
        
        return result
        
    except Exception as e:
        print(f"    ❌ Admin approval test failed: {e}")
        return False


def test_server_setup():
    """Test server role setup."""
    print("\n🖥️ Testing Server Setup...")
    
    try:
        admin_client = get_admin_client()
        server_client = get_server_client()
        
        # Get server principal
        server_principal = server_client.get_current_principal()
        print(f"    Server principal: {server_principal}")
        
        if server_principal:
            # Test server role setup
            print("  Testing server role setup...")
            result = admin_client.admin_set_server(server_principal)
            print(f"    Server setup result: {'✅ Success' if result else '❌ Failed'}")
            return result
        else:
            print("    ⚠️  Could not get server principal")
            return False
        
    except Exception as e:
        print(f"    ❌ Server setup test failed: {e}")
        return False


def test_system_status():
    """Test system status functions."""
    print("\n📊 Testing System Status...")
    
    try:
        client = get_client()
        
        # Test system stats
        print("  Testing system statistics...")
        stats = client.get_system_stats()
        if stats:
            print(f"    Total clients: {stats.total_clients}")
            print(f"    Active clients: {stats.active_clients}")
            print(f"    Total rounds: {stats.total_rounds}")
            print(f"    Completed rounds: {stats.completed_rounds}")
            return True
        else:
            print("    ⚠️  Could not get system stats")
            return False
        
    except Exception as e:
        print(f"    ❌ System status test failed: {e}")
        return False


def test_connection():
    """Test basic connection to ICP canister."""
    print("🔗 Testing ICP Connection...")
    
    try:
        client = get_client()
        
        if client.canister_id:
            print(f"    ✅ Connected to canister: {client.canister_id}")
            return True
        else:
            print("    ❌ Could not connect to canister")
            return False
        
    except Exception as e:
        print(f"    ❌ Connection test failed: {e}")
        return False


def main():
    """Run all authentication system tests."""
    print("🧪 ICP Federated Learning Authentication System Tests")
    print("=" * 70)
    
    # Load environment variables
    load_dotenv()
    
    # Check if environment is configured
    if not os.getenv("ICP_ADMIN_PRINCIPAL_ID"):
        print("❌ Environment not configured. Please run setup_icp_auth.py first")
        return 1
    
    # Test results
    results = []
    
    # Test 1: Basic connection
    results.append(("Connection", test_connection()))
    
    # Test 2: Admin functions
    results.append(("Admin Functions", test_admin_functions()))
    
    # Test 3: Client registration
    client_principal = test_client_registration()
    results.append(("Client Registration", client_principal is not None))
    
    # Test 4: Admin approval
    if client_principal:
        results.append(("Admin Approval", test_admin_approval(client_principal)))
    
    # Test 5: Server setup
    results.append(("Server Setup", test_server_setup()))
    
    # Test 6: System status
    results.append(("System Status", test_system_status()))
    
    # Print results summary
    print("\n" + "=" * 70)
    print("📋 Test Results Summary:")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name:<20} {status}")
        if result:
            passed += 1
    
    print("=" * 70)
    print(f"📊 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Authentication system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
