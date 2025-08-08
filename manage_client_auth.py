#!/usr/bin/env python3
"""
Client authentication management script for federated learning.
Allows admin to approve/reject client registrations.
"""

import sys
import os
import argparse
from typing import List, Dict, Any

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from icp_auth_client import AuthenticatedICPClient, get_admin_client

def print_banner():
    """Print the management banner."""
    print("\n" + "="*80)
    print("🔐 FEDERATED LEARNING CLIENT AUTHENTICATION MANAGER")
    print("="*80)

def list_pending_clients():
    """List all pending client registrations."""
    print("\n📋 Listing pending client registrations...")
    
    try:
        admin_client = get_admin_client()
        if not admin_client:
            print("❌ Failed to initialize admin client")
            return False
        
        # Get pending clients
        pending_clients = admin_client.get_pending_clients()
        
        if not pending_clients:
            print("✅ No pending client registrations")
            return True
        
        print(f"\n📊 Found {len(pending_clients)} pending client(s):")
        print("-" * 80)
        
        for i, client in enumerate(pending_clients, 1):
            print(f"\n{i}. Client Registration:")
            print(f"   🔑 Principal ID: {client.id}")
            print(f"   👤 Name: {client.client_name or 'Not provided'}")
            print(f"   🏥 Organization: {client.organization or 'Not provided'}")
            print(f"   📍 Location: {client.location or 'Not provided'}")
            print(f"   📧 Contact: {client.contact_email or 'Not provided'}")
            print(f"   📅 Registered: {client.registered_at}")
        
        print("-" * 80)
        return True
        
    except Exception as e:
        print(f"❌ Error listing pending clients: {e}")
        return False

def approve_client(principal_id: str):
    """Approve a client registration."""
    print(f"\n✅ Approving client: {principal_id}")
    
    try:
        admin_client = get_admin_client()
        if not admin_client:
            print("❌ Failed to initialize admin client")
            return False
        
        success = admin_client.approve_client(principal_id)
        
        if success:
            print(f"✅ Successfully approved client: {principal_id}")
            print("   Client can now participate in federated learning")
            return True
        else:
            print(f"❌ Failed to approve client: {principal_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error approving client: {e}")
        return False

def reject_client(principal_id: str):
    """Reject a client registration."""
    print(f"\n❌ Rejecting client: {principal_id}")
    
    try:
        admin_client = get_admin_client()
        if not admin_client:
            print("❌ Failed to initialize admin client")
            return False
        
        success = admin_client.reject_client(principal_id)
        
        if success:
            print(f"✅ Successfully rejected client: {principal_id}")
            return True
        else:
            print(f"❌ Failed to reject client: {principal_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error rejecting client: {e}")
        return False

def list_active_clients():
    """List all active (approved) clients."""
    print("\n👥 Listing active clients...")
    
    try:
        admin_client = get_admin_client()
        if not admin_client:
            print("❌ Failed to initialize admin client")
            return False
        
        # Get active clients
        active_clients = admin_client.get_active_clients()
        
        if not active_clients:
            print("ℹ️  No active clients found")
            return True
        
        print(f"\n📊 Found {len(active_clients)} active client(s):")
        print("-" * 80)
        
        for i, client in enumerate(active_clients, 1):
            print(f"\n{i}. Active Client:")
            print(f"   🔑 Principal ID: {client.id}")
            print(f"   📅 Registered: {client.registered_at}")
            print(f"   🏃 Last Active: {client.last_active}")
            print(f"   🔄 Rounds Participated: {client.total_rounds_participated}")
            print(f"   📊 Samples Contributed: {client.total_samples_contributed}")
        
        print("-" * 80)
        return True
        
    except Exception as e:
        print(f"❌ Error listing active clients: {e}")
        return False

def interactive_approval():
    """Interactive client approval process."""
    print("\n🔄 Starting interactive client approval process...")
    
    # List pending clients
    if not list_pending_clients():
        return False
    
    try:
        admin_client = get_admin_client()
        pending_clients = admin_client.get_pending_clients()
        
        if not pending_clients:
            print("✅ No pending clients to approve")
            return True
        
        print("\n🎯 Interactive Approval Process:")
        print("   Enter 'a' to approve, 'r' to reject, 's' to skip, 'q' to quit")
        
        for client in pending_clients:
            print(f"\n📋 Client: {client.client_name or 'Unknown'}")
            print(f"   🔑 Principal ID: {client.id}")
            print(f"   🏥 Organization: {client.organization or 'Not provided'}")
            print(f"   📧 Contact: {client.contact_email or 'Not provided'}")
            
            while True:
                choice = input("\n   Decision [a/r/s/q]: ").lower().strip()
                
                if choice == 'a':
                    approve_client(client.id)
                    break
                elif choice == 'r':
                    reject_client(client.id)
                    break
                elif choice == 's':
                    print("   ⏭️  Skipped")
                    break
                elif choice == 'q':
                    print("   🚪 Exiting approval process")
                    return True
                else:
                    print("   ❌ Invalid choice. Please enter 'a', 'r', 's', or 'q'")
        
        print("\n✅ Interactive approval process completed")
        return True
        
    except Exception as e:
        print(f"❌ Error in interactive approval: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Manage client authentication for federated learning")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List pending clients
    subparsers.add_parser('list-pending', help='List pending client registrations')
    
    # List active clients
    subparsers.add_parser('list-active', help='List active (approved) clients')
    
    # Approve client
    approve_parser = subparsers.add_parser('approve', help='Approve a client registration')
    approve_parser.add_argument('principal_id', help='Principal ID of client to approve')
    
    # Reject client
    reject_parser = subparsers.add_parser('reject', help='Reject a client registration')
    reject_parser.add_argument('principal_id', help='Principal ID of client to reject')
    
    # Interactive approval
    subparsers.add_parser('interactive', help='Interactive client approval process')
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.command == 'list-pending':
        success = list_pending_clients()
    elif args.command == 'list-active':
        success = list_active_clients()
    elif args.command == 'approve':
        success = approve_client(args.principal_id)
    elif args.command == 'reject':
        success = reject_client(args.principal_id)
    elif args.command == 'interactive':
        success = interactive_approval()
    else:
        parser.print_help()
        success = False
    
    print("\n" + "="*80)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
