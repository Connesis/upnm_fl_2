#!/usr/bin/env python3
"""
Remote Mainnet Client
Standalone client for interacting with the federated learning canister on mainnet
from any machine with dfx installed.
"""

import os
import sys
import subprocess
import json
import argparse
from typing import Optional, Dict, Any

class RemoteMainnetClient:
    """Client for interacting with mainnet canister from remote machines."""
    
    def __init__(self, canister_id: str = "wstch-aqaaa-aaaao-a4osq-cai", 
                 identity: str = "default", network: str = "ic"):
        """
        Initialize remote mainnet client.
        
        Args:
            canister_id: The mainnet canister ID
            identity: dfx identity to use
            network: Network (should be 'ic' for mainnet)
        """
        self.canister_id = canister_id
        self.identity = identity
        self.network = network
        
        print(f"🌐 Remote Mainnet Client Initialized")
        print(f"   Canister ID: {self.canister_id}")
        print(f"   Identity: {self.identity}")
        print(f"   Network: {self.network}")
    
    def call_canister(self, method: str, args: str = "") -> Optional[str]:
        """
        Call a canister method directly using canister ID.
        
        Args:
            method: Method name to call
            args: Arguments for the method
            
        Returns:
            Raw output from canister call
        """
        cmd = [
            "dfx", "canister", "call", 
            self.canister_id, method,
            "--network", self.network,
            "--identity", self.identity
        ]
        
        if args:
            cmd.append(args)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"❌ Error calling {method}: {e.stderr}")
            return None
    
    def get_system_stats(self) -> None:
        """Get system statistics from mainnet canister."""
        print("📊 Querying System Statistics...")
        result = self.call_canister("get_system_stats")
        if result:
            print("✅ System Stats:")
            print(result)
        else:
            print("❌ Failed to get system stats")
    
    def get_training_history(self) -> None:
        """Get training history from mainnet canister."""
        print("📋 Querying Training History...")
        result = self.call_canister("get_training_history")
        if result:
            print("✅ Training History:")
            print(result)
        else:
            print("❌ Failed to get training history")
    
    def get_training_round_metadata(self, round_id: int) -> None:
        """Get metadata for specific training round."""
        print(f"🔍 Querying Round {round_id} Metadata...")
        result = self.call_canister("get_training_round_metadata", f"({round_id})")
        if result:
            print(f"✅ Round {round_id} Metadata:")
            print(result)
        else:
            print(f"❌ Failed to get round {round_id} metadata")
    
    def register_client(self) -> None:
        """Register this client with the mainnet canister."""
        print("📝 Registering Client...")
        result = self.call_canister("register_client_enhanced")
        if result:
            print("✅ Client Registration Result:")
            print(result)
        else:
            print("❌ Failed to register client")
    
    def get_client_status(self) -> None:
        """Get status of this client."""
        print("👤 Querying Client Status...")
        # First get principal ID
        try:
            principal_result = subprocess.run([
                "dfx", "identity", "get-principal", "--identity", self.identity
            ], capture_output=True, text=True, check=True)
            
            principal_id = principal_result.stdout.strip()
            print(f"   Principal ID: {principal_id}")
            
            # Query client status
            result = self.call_canister("get_client_info", f'(principal "{principal_id}")')
            if result:
                print("✅ Client Status:")
                print(result)
            else:
                print("❌ Failed to get client status")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to get principal ID: {e}")
    
    def list_available_methods(self) -> None:
        """List available methods (informational)."""
        print("🔧 Available Methods:")
        methods = [
            "get_system_stats - Get overall system statistics",
            "get_training_history - Get complete training history", 
            "get_training_round_metadata(round_id) - Get specific round metadata",
            "register_client_enhanced - Register as a new client",
            "get_client_info(principal_id) - Get client information",
            "get_all_model_metadata - Get all model metadata",
            "admin_approve_client(principal_id) - Approve client (admin only)",
            "init_admin - Initialize admin role (admin only)"
        ]
        
        for method in methods:
            print(f"   • {method}")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Remote client for mainnet federated learning canister",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get system stats with default identity
  python remote_mainnet_client.py --action stats
  
  # Get training history with specific identity
  python remote_mainnet_client.py --action history --identity fl_client_1
  
  # Register as client
  python remote_mainnet_client.py --action register --identity fl_client_2
  
  # Get specific round metadata
  python remote_mainnet_client.py --action round --round-id 1
  
  # Get client status
  python remote_mainnet_client.py --action client-status --identity fl_client_1
        """
    )
    
    parser.add_argument("--canister-id", default="wstch-aqaaa-aaaao-a4osq-cai",
                       help="Mainnet canister ID")
    parser.add_argument("--identity", default="default",
                       help="dfx identity to use")
    parser.add_argument("--network", default="ic",
                       help="Network (ic for mainnet)")
    parser.add_argument("--action", required=True,
                       choices=["stats", "history", "round", "register", "client-status", "methods"],
                       help="Action to perform")
    parser.add_argument("--round-id", type=int,
                       help="Round ID for round metadata query")
    
    args = parser.parse_args()
    
    print("🌐 Remote Mainnet Federated Learning Client")
    print("=" * 60)
    
    client = RemoteMainnetClient(
        canister_id=args.canister_id,
        identity=args.identity,
        network=args.network
    )
    
    print()
    
    if args.action == "stats":
        client.get_system_stats()
    elif args.action == "history":
        client.get_training_history()
    elif args.action == "round":
        if args.round_id is None:
            print("❌ --round-id required for round metadata query")
            return 1
        client.get_training_round_metadata(args.round_id)
    elif args.action == "register":
        client.register_client()
    elif args.action == "client-status":
        client.get_client_status()
    elif args.action == "methods":
        client.list_available_methods()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
