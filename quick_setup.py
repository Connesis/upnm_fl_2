#!/usr/bin/env python3
"""
Quick Setup Script
Automated setup for federated learning on Internet Computer.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(cmd, description, check=True):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        if result.returncode == 0:
            print(f"   ✅ Success")
            return result.stdout.strip()
        else:
            print(f"   ❌ Failed: {result.stderr}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e}")
        return None

def check_prerequisites():
    """Check if required tools are installed."""
    print("🔍 Checking Prerequisites")
    print("=" * 40)
    
    tools = {
        'dfx': 'dfx --version',
        'uv': 'uv --version',
        'python': 'python --version',
        'node': 'node --version'
    }
    
    missing_tools = []
    
    for tool, cmd in tools.items():
        result = run_command(cmd, f"Checking {tool}", check=False)
        if result is None:
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"\n❌ Missing tools: {', '.join(missing_tools)}")
        print("\nPlease install missing tools:")
        print("• dfx: sh -ci \"$(curl -fsSL https://internetcomputer.org/install.sh)\"")
        print("• uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("• python: Install Python 3.11+")
        print("• node: Install Node.js 16+")
        return False
    
    print("✅ All prerequisites installed")
    return True

def setup_local_network():
    """Setup local ICP network."""
    print("\n🏠 Setting Up Local Network")
    print("=" * 40)
    
    # Stop any existing dfx
    run_command("dfx stop", "Stopping existing dfx", check=False)
    
    # Start dfx
    result = run_command("dfx start --background --clean", "Starting local ICP network")
    if result is None:
        return False
    
    # Ping to verify
    result = run_command("dfx ping", "Verifying network connection")
    return result is not None

def create_identities():
    """Create required identities."""
    print("\n🔑 Creating Identities")
    print("=" * 40)
    
    identities = ['fl_server', 'fl_client_1', 'fl_client_2', 'fl_client_3']
    
    for identity in identities:
        # Check if identity exists
        result = run_command(f"dfx identity list | grep {identity}", f"Checking {identity}", check=False)
        
        if result is None:
            # Create identity
            result = run_command(f"dfx identity new {identity}", f"Creating {identity}")
            if result is None:
                return False
        else:
            print(f"   ✅ {identity} already exists")
    
    # Set default identity
    run_command("dfx identity use fl_server", "Setting default identity")
    
    return True

def deploy_canister():
    """Deploy the federated learning canister."""
    print("\n🚀 Deploying Canister")
    print("=" * 40)
    
    # Check if canister directory exists
    canister_dir = Path("icp/fl_cvd_backend")
    if not canister_dir.exists():
        print("❌ Canister directory not found: icp/fl_cvd_backend")
        return False, None
    
    # Deploy canister
    result = run_command(
        f"cd {canister_dir} && dfx deploy",
        "Deploying to local network"
    )
    
    if result is None:
        return False, None
    
    # Get canister ID
    canister_id = run_command(
        f"cd {canister_dir} && dfx canister id fl_cvd_backend_backend",
        "Getting canister ID"
    )
    
    if canister_id:
        print(f"   🆔 Canister ID: {canister_id}")
        
        # Initialize admin
        run_command(
            f"cd {canister_dir} && dfx canister call fl_cvd_backend_backend init_admin --identity fl_server",
            "Initializing admin role"
        )
        
        return True, canister_id
    
    return False, None

def setup_python_environment():
    """Setup Python environment."""
    print("\n🐍 Setting Up Python Environment")
    print("=" * 40)
    
    # Install dependencies
    result = run_command("uv sync", "Installing Python dependencies")
    if result is None:
        # Try alternative installation
        result = run_command(
            "uv add scikit-learn pandas numpy joblib python-dotenv matplotlib seaborn",
            "Installing individual packages"
        )
    
    return result is not None

def create_sample_datasets():
    """Create sample datasets if they don't exist."""
    print("\n📊 Checking Sample Datasets")
    print("=" * 40)
    
    dataset_dir = Path("dataset/clients")
    dataset_files = ["client1_data.csv", "client2_data.csv", "client3_data.csv"]
    
    missing_files = []
    for file in dataset_files:
        if not (dataset_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"⚠️ Missing dataset files: {', '.join(missing_files)}")
        print("   Please ensure you have the cardiovascular disease datasets")
        print("   Place them in: dataset/clients/")
        return False
    
    print("✅ All dataset files found")
    return True

def register_and_approve_clients(canister_id):
    """Register and approve all clients."""
    print("\n👥 Registering and Approving Clients")
    print("=" * 40)
    
    clients = ['fl_client_1', 'fl_client_2', 'fl_client_3']
    
    for client in clients:
        # Register client
        result = run_command(
            f"dfx canister call {canister_id} register_client_enhanced --identity {client}",
            f"Registering {client}"
        )
        
        if result is None:
            return False
        
        # Get principal ID
        principal_id = run_command(
            f"dfx identity get-principal --identity {client}",
            f"Getting {client} principal ID"
        )
        
        if principal_id:
            # Approve client
            result = run_command(
                f"dfx canister call {canister_id} admin_approve_client '(principal \"{principal_id}\")' --identity fl_server",
                f"Approving {client}"
            )
            
            if result is None:
                return False
    
    return True

def create_env_file(canister_id):
    """Create environment configuration file."""
    print("\n📝 Creating Environment Configuration")
    print("=" * 40)
    
    env_content = f"""# Federated Learning Environment Configuration
# Local Network Setup
ICP_CANISTER_ID={canister_id}
ICP_NETWORK=local

# Server Configuration
ICP_CLIENT_IDENTITY_NAME=fl_server

# Client Configuration (uncomment for client machines)
# ICP_CLIENT_IDENTITY_NAME=fl_client_1
# CLIENT_NAME=Healthcare Provider 1
# CLIENT_ORGANIZATION=Hospital 1
# CLIENT_LOCATION=City 1, Country
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("   ✅ Created .env file")
        return True
    except Exception as e:
        print(f"   ❌ Failed to create .env file: {e}")
        return False

def display_next_steps(canister_id):
    """Display next steps for the user."""
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    print(f"\n🆔 Your Local Canister ID: {canister_id}")
    print(f"🌐 Candid Interface: http://127.0.0.1:4943/?canisterId={canister_id}")
    
    print("\n🚀 Next Steps:")
    print("1. Start federated learning training:")
    print("   # On server machine:")
    print("   uv run python server/server.py --rounds 2 --min-clients 3")
    print()
    print("   # On client machines (run simultaneously):")
    print("   export ICP_CLIENT_IDENTITY_NAME=fl_client_1")
    print(f"   export ICP_CANISTER_ID={canister_id}")
    print("   uv run python client/client.py --dataset dataset/clients/client1_data.csv --trees 30")
    print()
    
    print("2. Query training results:")
    print(f"   dfx canister call {canister_id} get_system_stats --identity fl_server")
    print(f"   dfx canister call {canister_id} get_training_history --identity fl_server")
    print()
    
    print("3. Verify model integrity:")
    print("   uv run python verify_model.py --round 1")
    print("   uv run python verify_model.py --all")
    print()
    
    print("4. Test models:")
    print("   uv run python test_model.py models/federated_cvd_model_round_1_*.joblib dataset/test_data.csv")
    print("   uv run python analyze_training.py")
    print()
    
    print("📚 For mainnet deployment, see FEDERATED_LEARNING_USER_GUIDE.md")

def main():
    """Main setup function."""
    print("🏥 Federated Learning Quick Setup")
    print("=" * 60)
    print("This script will set up your federated learning environment")
    print("for local development and testing.")
    print()
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Setup local network
    if not setup_local_network():
        print("❌ Failed to setup local network")
        sys.exit(1)
    
    # Create identities
    if not create_identities():
        print("❌ Failed to create identities")
        sys.exit(1)
    
    # Setup Python environment
    if not setup_python_environment():
        print("❌ Failed to setup Python environment")
        sys.exit(1)
    
    # Check datasets
    if not create_sample_datasets():
        print("❌ Dataset files missing")
        sys.exit(1)
    
    # Deploy canister
    success, canister_id = deploy_canister()
    if not success:
        print("❌ Failed to deploy canister")
        sys.exit(1)
    
    # Register and approve clients
    if not register_and_approve_clients(canister_id):
        print("❌ Failed to register clients")
        sys.exit(1)
    
    # Create environment file
    create_env_file(canister_id)
    
    # Display next steps
    display_next_steps(canister_id)

if __name__ == "__main__":
    main()
