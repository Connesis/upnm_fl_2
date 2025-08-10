#!/usr/bin/env python3
"""
Setup Mainnet Identities
Create and configure identities for mainnet deployment.
"""

import os
import sys
import subprocess
import logging
from typing import List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class MainnetIdentitySetup:
    """Setup identities for mainnet deployment."""
    
    def __init__(self):
        """Initialize identity setup."""
        self.server_identity = "fl_server"
        self.client_identities = ["fl_client_1", "fl_client_2", "fl_client_3"]
        self.all_identities = [self.server_identity] + self.client_identities
        
        logger.info("🔐 Mainnet Identity Setup Initialized")
    
    def create_identity(self, identity_name: str) -> bool:
        """Create a new identity."""
        try:
            # Check if identity already exists
            result = subprocess.run([
                "dfx", "identity", "list"
            ], capture_output=True, text=True, check=True)
            
            if identity_name in result.stdout:
                logger.info(f"   ✅ Identity {identity_name} already exists")
                return True
            
            # Create new identity
            result = subprocess.run([
                "dfx", "identity", "new", identity_name
            ], capture_output=True, text=True, check=True)
            
            logger.info(f"   ✅ Created identity: {identity_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"   ❌ Failed to create identity {identity_name}: {e}")
            return False
    
    def get_principal_id(self, identity_name: str) -> str:
        """Get principal ID for an identity."""
        try:
            result = subprocess.run([
                "dfx", "identity", "get-principal", "--identity", identity_name
            ], capture_output=True, text=True, check=True)
            
            principal_id = result.stdout.strip()
            logger.info(f"   📋 {identity_name}: {principal_id}")
            return principal_id
            
        except subprocess.CalledProcessError as e:
            logger.error(f"   ❌ Failed to get principal for {identity_name}: {e}")
            return ""
    
    def setup_cycles_wallet(self, identity_name: str) -> bool:
        """Setup cycles wallet for an identity."""
        logger.info(f"💰 Setting up cycles wallet for {identity_name}...")
        
        try:
            # Check if wallet already exists
            result = subprocess.run([
                "dfx", "identity", "get-wallet", "--identity", identity_name, "--network", "ic"
            ], capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                wallet_id = result.stdout.strip()
                logger.info(f"   ✅ Wallet already exists: {wallet_id}")
                return True
            
            logger.warning(f"   ⚠️  No wallet found for {identity_name}")
            logger.info(f"   💡 You need to:")
            logger.info(f"      1. Get ICP tokens from an exchange")
            logger.info(f"      2. Convert ICP to cycles using NNS dapp")
            logger.info(f"      3. Set wallet with: dfx identity set-wallet <wallet-id> --identity {identity_name} --network ic")
            
            return False
            
        except Exception as e:
            logger.error(f"   ❌ Error checking wallet for {identity_name}: {e}")
            return False
    
    def create_all_identities(self) -> bool:
        """Create all required identities."""
        logger.info("🔐 Creating mainnet identities...")
        
        success_count = 0
        for identity in self.all_identities:
            if self.create_identity(identity):
                success_count += 1
        
        if success_count == len(self.all_identities):
            logger.info(f"✅ All {len(self.all_identities)} identities created successfully")
            return True
        else:
            logger.error(f"❌ Only {success_count}/{len(self.all_identities)} identities created")
            return False
    
    def display_identity_info(self) -> None:
        """Display information about all identities."""
        logger.info("📋 Identity Information:")
        logger.info("-" * 50)
        
        for identity in self.all_identities:
            principal_id = self.get_principal_id(identity)
            if principal_id:
                logger.info(f"🔑 {identity}")
                logger.info(f"   Principal: {principal_id}")
                
                # Check wallet status
                try:
                    result = subprocess.run([
                        "dfx", "identity", "get-wallet", "--identity", identity, "--network", "ic"
                    ], capture_output=True, text=True, check=False)
                    
                    if result.returncode == 0:
                        wallet_id = result.stdout.strip()
                        logger.info(f"   Wallet: {wallet_id}")
                        
                        # Check wallet balance
                        try:
                            balance_result = subprocess.run([
                                "dfx", "wallet", "balance", "--identity", identity, "--network", "ic"
                            ], capture_output=True, text=True, check=True)
                            logger.info(f"   Balance: {balance_result.stdout.strip()}")
                        except:
                            logger.info(f"   Balance: Unable to check")
                    else:
                        logger.info(f"   Wallet: Not configured")
                except:
                    logger.info(f"   Wallet: Error checking")
                
                logger.info("")
    
    def generate_setup_instructions(self) -> None:
        """Generate setup instructions for mainnet deployment."""
        print("\n" + "=" * 80)
        print("🌐 MAINNET DEPLOYMENT SETUP INSTRUCTIONS")
        print("=" * 80)
        
        print("\n💰 CYCLES WALLET SETUP:")
        print("1. Get ICP tokens from an exchange (Coinbase, Binance, etc.)")
        print("2. Send ICP to your identity's account address")
        print("3. Go to https://nns.ic0.app")
        print("4. Convert ICP to cycles")
        print("5. Create a cycles wallet")
        print("6. Set the wallet for your server identity:")
        print(f"   dfx identity set-wallet <wallet-canister-id> --identity {self.server_identity} --network ic")
        
        print("\n🔐 IDENTITY VERIFICATION:")
        print("Run this command to verify your identities:")
        print("   dfx identity list")
        
        print("\n💳 MINIMUM CYCLES REQUIRED:")
        print("   • Canister creation: ~1T cycles")
        print("   • Training operations: ~100B cycles per round")
        print("   • Total recommended: ~2T cycles")
        
        print("\n🚀 DEPLOYMENT COMMAND:")
        print("Once setup is complete, run:")
        print("   uv run python deploy_to_mainnet.py")
        
        print("\n⚠️  IMPORTANT NOTES:")
        print("   • Mainnet operations cost real ICP tokens")
        print("   • Data stored on mainnet is permanent and public")
        print("   • Test thoroughly on local network first")
        print("   • Keep your identity files secure")
        
        print("=" * 80)
    
    def run_complete_setup(self) -> bool:
        """Run the complete identity setup process."""
        logger.info("🔐 Starting Mainnet Identity Setup")
        logger.info("=" * 50)
        
        # Create identities
        if not self.create_all_identities():
            logger.error("❌ Failed to create all identities")
            return False
        
        # Display identity information
        self.display_identity_info()
        
        # Check wallet setup for server identity
        wallet_configured = self.setup_cycles_wallet(self.server_identity)
        
        # Generate instructions
        self.generate_setup_instructions()
        
        if wallet_configured:
            logger.info("✅ Identity setup completed - ready for mainnet deployment!")
            return True
        else:
            logger.warning("⚠️  Identity setup completed - wallet configuration needed")
            return False


def main():
    """Main function to run identity setup."""
    print("🔐 Mainnet Identity Setup for Federated Learning")
    print("=" * 60)
    
    setup = MainnetIdentitySetup()
    success = setup.run_complete_setup()
    
    if success:
        print("\n🎉 Identity Setup Completed Successfully!")
        print("💰 Wallet is configured - ready for mainnet deployment")
    else:
        print("\n⚠️  Identity Setup Completed with Warnings!")
        print("💰 Please configure cycles wallet before mainnet deployment")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
