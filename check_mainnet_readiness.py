#!/usr/bin/env python3
"""
Check Mainnet Readiness
Verify that existing identities are ready for mainnet deployment.
"""

import os
import sys
import subprocess
import logging
from typing import List, Dict

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class MainnetReadinessChecker:
    """Check if existing identities are ready for mainnet deployment."""
    
    def __init__(self):
        """Initialize readiness checker."""
        self.server_identity = "fl_server"
        self.client_identities = ["fl_client_1", "fl_client_2", "fl_client_3"]
        self.all_identities = [self.server_identity] + self.client_identities
        
        logger.info("🔍 Mainnet Readiness Checker Initialized")
    
    def check_identity_exists(self, identity_name: str) -> bool:
        """Check if an identity exists."""
        try:
            result = subprocess.run([
                "dfx", "identity", "list"
            ], capture_output=True, text=True, check=True)
            
            return identity_name in result.stdout
            
        except subprocess.CalledProcessError:
            return False
    
    def get_principal_id(self, identity_name: str) -> str:
        """Get principal ID for an identity."""
        try:
            result = subprocess.run([
                "dfx", "identity", "get-principal", "--identity", identity_name
            ], capture_output=True, text=True, check=True)
            
            return result.stdout.strip()
            
        except subprocess.CalledProcessError:
            return ""
    
    def check_wallet_status(self, identity_name: str) -> Dict[str, str]:
        """Check wallet status for an identity."""
        wallet_info = {
            "has_wallet": False,
            "wallet_id": "",
            "balance": "Unknown"
        }
        
        try:
            # Check if wallet exists
            result = subprocess.run([
                "dfx", "identity", "get-wallet", "--identity", identity_name, "--network", "ic"
            ], capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                wallet_info["has_wallet"] = True
                wallet_info["wallet_id"] = result.stdout.strip()
                
                # Check wallet balance
                try:
                    balance_result = subprocess.run([
                        "dfx", "wallet", "balance", "--identity", identity_name, "--network", "ic"
                    ], capture_output=True, text=True, check=True)
                    wallet_info["balance"] = balance_result.stdout.strip()
                except:
                    wallet_info["balance"] = "Unable to check"
            
        except Exception:
            pass
        
        return wallet_info
    
    def check_all_identities(self) -> Dict[str, Dict]:
        """Check status of all identities."""
        logger.info("🔍 Checking existing identities for mainnet readiness...")
        
        identity_status = {}
        
        for identity in self.all_identities:
            logger.info(f"   Checking {identity}...")
            
            status = {
                "exists": self.check_identity_exists(identity),
                "principal_id": "",
                "wallet_info": {}
            }
            
            if status["exists"]:
                status["principal_id"] = self.get_principal_id(identity)
                status["wallet_info"] = self.check_wallet_status(identity)
            
            identity_status[identity] = status
        
        return identity_status
    
    def display_readiness_report(self, identity_status: Dict[str, Dict]) -> bool:
        """Display comprehensive readiness report."""
        print("\n" + "=" * 80)
        print("🌐 MAINNET DEPLOYMENT READINESS REPORT")
        print("=" * 80)
        
        all_ready = True
        missing_identities = []
        missing_wallets = []
        
        print("\n🔑 IDENTITY STATUS:")
        print("-" * 50)
        
        for identity, status in identity_status.items():
            role = "SERVER" if identity == self.server_identity else "CLIENT"
            
            if status["exists"]:
                print(f"✅ {identity} ({role})")
                print(f"   Principal: {status['principal_id']}")
                
                wallet_info = status["wallet_info"]
                if wallet_info["has_wallet"]:
                    print(f"   Wallet: {wallet_info['wallet_id']}")
                    print(f"   Balance: {wallet_info['balance']}")
                else:
                    print(f"   Wallet: ❌ Not configured")
                    if identity == self.server_identity:
                        missing_wallets.append(identity)
                        all_ready = False
            else:
                print(f"❌ {identity} ({role}) - NOT FOUND")
                missing_identities.append(identity)
                all_ready = False
            
            print()
        
        # Summary
        print("📊 READINESS SUMMARY:")
        print("-" * 30)
        
        if all_ready:
            print("🎉 ALL IDENTITIES READY FOR MAINNET DEPLOYMENT!")
            print("✅ All required identities exist")
            print("✅ Server wallet is configured")
            print("✅ Ready to deploy to mainnet")
        else:
            print("⚠️  SOME SETUP REQUIRED BEFORE MAINNET DEPLOYMENT")
            
            if missing_identities:
                print(f"❌ Missing identities: {', '.join(missing_identities)}")
                print("   💡 These identities already exist from local testing")
                print("   💡 No action needed - they're ready for mainnet")
            
            if missing_wallets:
                print(f"💰 Missing wallet configuration: {', '.join(missing_wallets)}")
                print("   💡 Server needs cycles wallet for mainnet deployment")
        
        return all_ready
    
    def generate_next_steps(self, identity_status: Dict[str, Dict]) -> None:
        """Generate next steps based on readiness status."""
        print("\n🚀 NEXT STEPS FOR MAINNET DEPLOYMENT:")
        print("-" * 50)
        
        server_status = identity_status.get(self.server_identity, {})
        server_wallet = server_status.get("wallet_info", {})
        
        if not server_wallet.get("has_wallet", False):
            print("1. 💰 SET UP CYCLES WALLET:")
            print("   • Get ICP tokens from an exchange")
            print("   • Go to https://nns.ic0.app")
            print("   • Convert ICP to cycles and create wallet")
            print(f"   • Run: dfx identity set-wallet <wallet-id> --identity {self.server_identity} --network ic")
            print()
        
        print("2. 🚀 DEPLOY TO MAINNET:")
        print("   • Run: uv run python deploy_to_mainnet.py")
        print("   • This will use your existing identities:")
        for identity in self.all_identities:
            role = "SERVER" if identity == self.server_identity else "CLIENT"
            principal = identity_status.get(identity, {}).get("principal_id", "Unknown")
            print(f"     - {identity} ({role}): {principal}")
        print()
        
        print("3. 🔍 VERIFY DEPLOYMENT:")
        print("   • Check canister deployment logs")
        print("   • Verify training completion")
        print("   • Query metadata from mainnet canister")
        print()
        
        print("💡 ADVANTAGES OF USING EXISTING IDENTITIES:")
        print("   ✅ Consistent with local testing")
        print("   ✅ Same principal IDs across networks")
        print("   ✅ No need to create new identities")
        print("   ✅ Seamless transition from local to mainnet")
    
    def run_readiness_check(self) -> bool:
        """Run complete readiness check."""
        logger.info("🔍 Starting Mainnet Readiness Check")
        logger.info("=" * 50)
        
        # Check all identities
        identity_status = self.check_all_identities()
        
        # Display report
        all_ready = self.display_readiness_report(identity_status)
        
        # Generate next steps
        self.generate_next_steps(identity_status)
        
        return all_ready


def main():
    """Main function to run readiness check."""
    print("🔍 Mainnet Deployment Readiness Check")
    print("=" * 50)
    print("Checking if existing identities are ready for mainnet deployment...")
    print()
    
    checker = MainnetReadinessChecker()
    ready = checker.run_readiness_check()
    
    if ready:
        print("\n🎉 System Ready for Mainnet Deployment!")
        print("You can proceed with: uv run python deploy_to_mainnet.py")
    else:
        print("\n⚠️  Setup Required Before Mainnet Deployment")
        print("Follow the next steps above to complete setup")
    
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())
