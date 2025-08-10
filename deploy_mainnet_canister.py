#!/usr/bin/env python3
"""
Deploy Canister to ICP Mainnet
Simple script to deploy the federated learning canister to mainnet.
"""

import os
import sys
import subprocess
import logging
import time
from typing import Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mainnet_deployment.log')
    ]
)
logger = logging.getLogger('MAINNET_DEPLOY')

class MainnetCanisterDeployer:
    """Deploy canister to ICP mainnet."""
    
    def __init__(self):
        """Initialize the deployer."""
        self.server_identity = "fl_server"
        self.network = "ic"
        self.canister_name = "fl_cvd_backend_backend"
        self.canister_id = None
        
        logger.info("🌐 Mainnet Canister Deployer Initialized")
        logger.info(f"   Identity: {self.server_identity}")
        logger.info(f"   Network: {self.network}")
    
    def check_prerequisites(self) -> bool:
        """Check if prerequisites are met."""
        logger.info("🔍 Checking deployment prerequisites...")
        
        try:
            # Check identity exists
            result = subprocess.run([
                "dfx", "identity", "get-principal", "--identity", self.server_identity
            ], capture_output=True, text=True, check=True)
            
            principal_id = result.stdout.strip()
            logger.info(f"   ✅ Identity: {self.server_identity}")
            logger.info(f"   📋 Principal: {principal_id}")
            
            # Check wallet
            try:
                wallet_result = subprocess.run([
                    "dfx", "wallet", "balance", "--identity", self.server_identity, "--network", self.network
                ], capture_output=True, text=True, check=True)
                
                balance = wallet_result.stdout.strip()
                logger.info(f"   💰 Wallet Balance: {balance}")
                
                # Check if balance is sufficient (rough check)
                if "0 cycles" in balance.lower():
                    logger.error("   ❌ Insufficient cycles for deployment")
                    return False
                
                return True
                
            except subprocess.CalledProcessError:
                logger.error("   ❌ No cycles wallet configured")
                logger.info("   💡 Set up wallet with: dfx identity set-wallet <wallet-id> --identity fl_server --network ic")
                return False
            
        except subprocess.CalledProcessError as e:
            logger.error(f"   ❌ Prerequisites check failed: {e}")
            return False
    
    def deploy_canister(self) -> bool:
        """Deploy the canister to mainnet."""
        logger.info("🚀 Deploying canister to ICP mainnet...")
        
        try:
            # Change to canister directory
            canister_dir = "icp/fl_cvd_backend"
            
            # Deploy command
            cmd = [
                "dfx", "deploy", self.canister_name,
                "--network", self.network,
                "--identity", self.server_identity,
                "--with-cycles", "1000000000000"  # 1T cycles
            ]
            
            logger.info(f"   🔧 Running: {' '.join(cmd)}")
            logger.info("   ⏳ This may take several minutes...")
            
            # Run deployment
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True,
                cwd=canister_dir,
                timeout=600  # 10 minutes timeout
            )
            
            # Parse output for canister ID
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if "canister ID" in line.lower() or "deployed" in line.lower():
                    logger.info(f"   📋 {line.strip()}")
                    
                    # Try to extract canister ID
                    parts = line.split()
                    for part in parts:
                        if len(part) > 20 and "-" in part and part.count("-") >= 4:
                            self.canister_id = part
                            break
            
            if not self.canister_id:
                # Try to get canister ID from dfx
                try:
                    id_result = subprocess.run([
                        "dfx", "canister", "id", self.canister_name,
                        "--network", self.network
                    ], capture_output=True, text=True, check=True, cwd=canister_dir)
                    
                    self.canister_id = id_result.stdout.strip()
                except:
                    pass
            
            if self.canister_id:
                logger.info(f"✅ Canister deployed successfully!")
                logger.info(f"   🆔 Canister ID: {self.canister_id}")
                logger.info(f"   🌐 Mainnet URL: https://{self.canister_id}.ic0.app")
                logger.info(f"   🔗 Candid UI: https://a4gq6-oaaaa-aaaab-qaa4q-cai.raw.ic0.app/?id={self.canister_id}")
            else:
                logger.warning("⚠️  Deployment completed but couldn't extract canister ID")
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Deployment timed out (>10 minutes)")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Deployment failed: {e}")
            if e.stdout:
                logger.error(f"   stdout: {e.stdout}")
            if e.stderr:
                logger.error(f"   stderr: {e.stderr}")
            return False
    
    def setup_canister(self) -> bool:
        """Set up the deployed canister."""
        if not self.canister_id:
            logger.error("❌ Cannot setup canister - no canister ID available")
            return False
        
        logger.info("⚙️ Setting up deployed canister...")
        
        try:
            # Set admin role
            logger.info("   👑 Setting admin role...")
            result = subprocess.run([
                "dfx", "canister", "call", self.canister_name,
                "init_admin",
                "--network", self.network,
                "--identity", self.server_identity
            ], capture_output=True, text=True, check=True,
               cwd="icp/fl_cvd_backend", timeout=60)
            
            logger.info(f"   ✅ Admin role set: {result.stdout.strip()}")
            
            # Test canister functionality
            logger.info("   🧪 Testing canister functionality...")
            test_result = subprocess.run([
                "dfx", "canister", "call", self.canister_name,
                "get_system_stats",
                "--network", self.network,
                "--identity", self.server_identity
            ], capture_output=True, text=True, check=True,
               cwd="icp/fl_cvd_backend", timeout=60)
            
            logger.info(f"   ✅ Canister is functional: {test_result.stdout.strip()}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Canister setup failed: {e}")
            return False
    
    def display_deployment_info(self) -> None:
        """Display deployment information."""
        print("\n" + "=" * 80)
        print("🎉 MAINNET DEPLOYMENT COMPLETED!")
        print("=" * 80)
        
        if self.canister_id:
            print(f"🆔 Canister ID: {self.canister_id}")
            print(f"🌐 Mainnet URL: https://{self.canister_id}.ic0.app")
            print(f"🔗 Candid UI: https://a4gq6-oaaaa-aaaab-qaa4q-cai.raw.ic0.app/?id={self.canister_id}")
            print()
            print("📋 NEXT STEPS:")
            print("1. Register and approve clients")
            print("2. Run federated learning training")
            print("3. Query metadata from mainnet")
            print()
            print("🔧 USEFUL COMMANDS:")
            print(f"# Query canister status")
            print(f"dfx canister status {self.canister_name} --network ic --identity fl_server")
            print()
            print(f"# Get system stats")
            print(f"dfx canister call {self.canister_name} get_system_stats --network ic --identity fl_server")
        
        print("=" * 80)
    
    def run_deployment(self) -> bool:
        """Run the complete deployment process."""
        logger.info("🌐 STARTING MAINNET CANISTER DEPLOYMENT")
        logger.info("=" * 60)
        
        # Check prerequisites
        if not self.check_prerequisites():
            logger.error("❌ Prerequisites not met")
            return False
        
        # Deploy canister
        if not self.deploy_canister():
            logger.error("❌ Canister deployment failed")
            return False
        
        # Setup canister
        if not self.setup_canister():
            logger.error("❌ Canister setup failed")
            return False
        
        # Display info
        self.display_deployment_info()
        
        logger.info("🎉 MAINNET DEPLOYMENT COMPLETED SUCCESSFULLY!")
        return True


def main():
    """Main deployment function."""
    print("🌐 ICP Mainnet Canister Deployment")
    print("=" * 50)
    print("⚠️  WARNING: This will deploy to ICP mainnet and consume cycles!")
    print()
    
    # Check if user wants to proceed
    response = input("Do you want to proceed with mainnet deployment? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Deployment cancelled by user")
        return 1
    
    deployer = MainnetCanisterDeployer()
    success = deployer.run_deployment()
    
    if success:
        print("\n🎉 Mainnet Deployment Successful!")
        print("📝 Check mainnet_deployment.log for detailed logs")
        print("🌐 Your canister is now live on ICP mainnet!")
    else:
        print("\n❌ Mainnet Deployment Failed!")
        print("📝 Check mainnet_deployment.log for error details")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
