# 🏥 Federated Learning on Internet Computer - Complete User Guide

## 📋 Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Local Network Setup](#local-network-setup)
4. [Mainnet Setup](#mainnet-setup)
5. [Running Training](#running-training)
6. [Querying Results](#querying-results)
7. [Model Verification](#model-verification)
8. [Model Testing](#model-testing)
9. [Troubleshooting](#troubleshooting)

## 🎯 Overview

This guide covers setting up a federated learning system for cardiovascular disease prediction using the Internet Computer Protocol (ICP). The system supports:

- **Privacy-preserving training** across multiple healthcare providers
- **Blockchain-based authentication** and audit trails
- **Model integrity verification** using cryptographic hashes
- **Both local and mainnet deployment**

### 🏗️ Architecture
- **Server Machine**: Coordinates training, deploys canister, manages aggregation
- **Client Machines**: Healthcare providers with local datasets
- **ICP Canister**: Blockchain backend for authentication and metadata storage

---

## 🔧 Prerequisites

### All Machines (Server + Clients)

#### 1. Install dfx (Internet Computer SDK)
```bash
# Install dfx
sh -ci "$(curl -fsSL https://internetcomputer.org/install.sh)"

# Verify installation
dfx --version
```

#### 2. Install Python and uv
```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
python --version  # Should be 3.11+
```

#### 3. Install Node.js (for some dfx operations)
```bash
# Install Node.js (version 16+)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Or on macOS
brew install node
```

### Server Machine Only

#### 4. Clone the Project
```bash
git clone <your-federated-learning-repo>
cd federated_learning_project

# Install Python dependencies
uv sync
```

#### 5. Install Additional Dependencies
```bash
# Install scikit-learn, pandas, etc.
uv add scikit-learn pandas numpy joblib python-dotenv
```

---

## 🏠 Local Network Setup

### Step 1: Server Machine Setup

#### 1.1 Start Local ICP Network
```bash
# Start dfx in background
dfx start --background --clean

# Verify network is running
dfx ping
```

#### 1.2 Create Identities
```bash
# Create server identity
dfx identity new fl_server
dfx identity use fl_server

# Create client identities (even if clients are on different machines)
dfx identity new fl_client_1
dfx identity new fl_client_2  
dfx identity new fl_client_3

# Verify identities
dfx identity list
```

#### 1.3 Deploy Canister
```bash
# Navigate to canister directory
cd icp/fl_cvd_backend

# Deploy to local network
dfx deploy

# Note the canister ID (e.g., uxrrr-q7777-77774-qaaaq-cai)
dfx canister id fl_cvd_backend_backend
```

#### 1.4 Setup Canister
```bash
# Initialize admin role
dfx canister call fl_cvd_backend_backend init_admin --identity fl_server

# Verify deployment
dfx canister call fl_cvd_backend_backend get_system_stats --identity fl_server
```

### Step 2: Client Machine Setup

#### 2.1 Install Prerequisites
Follow the prerequisites section above for each client machine.

#### 2.2 Create Client Identity
```bash
# On each client machine, create identity with same name as server
dfx identity new fl_client_1  # Use fl_client_2, fl_client_3 for other clients
dfx identity use fl_client_1

# Get principal ID (share this with server admin)
dfx identity get-principal
```

#### 2.3 Get Project Files
```bash
# Option A: Clone full repository
git clone <your-federated-learning-repo>
cd federated_learning_project

# Option B: Copy only necessary files
# - client/client.py
# - dataset/clients/client1_data.csv (or client2_data.csv, client3_data.csv)
# - requirements or pyproject.toml
# - remote_mainnet_client.py (for querying)
```

#### 2.4 Install Python Dependencies
```bash
uv sync
# or
uv add scikit-learn pandas numpy joblib python-dotenv
```

### Step 3: Register and Approve Clients

#### 3.1 Client Registration (on each client machine)
```bash
# Register with local canister (replace with actual canister ID)
dfx canister call uxrrr-q7777-77774-qaaaq-cai register_client_enhanced --identity fl_client_1

# For clients on different machines, use canister ID directly
```

#### 3.2 Admin Approval (on server machine)
```bash
# Get client principal IDs and approve them
dfx canister call fl_cvd_backend_backend admin_approve_client '(principal "CLIENT_PRINCIPAL_ID")' --identity fl_server

# Repeat for all clients
```

### Step 4: Prepare Datasets

#### 4.1 Server Machine
```bash
# Ensure datasets exist
ls dataset/clients/
# Should show: client1_data.csv, client2_data.csv, client3_data.csv
```

#### 4.2 Client Machines
```bash
# Each client needs their respective dataset
# Client 1: client1_data.csv
# Client 2: client2_data.csv  
# Client 3: client3_data.csv

# Place in dataset/clients/ directory
mkdir -p dataset/clients
# Copy your dataset file here
```

---

## 🌐 Mainnet Setup

### Step 1: Server Machine Mainnet Setup

#### 1.1 Setup Cycles Wallet
```bash
# Check if you have a wallet configured
dfx wallet balance --identity fl_server --network ic

# If no wallet, you need to:
# 1. Get ICP tokens from exchange
# 2. Go to https://nns.ic0.app
# 3. Convert ICP to cycles
# 4. Create cycles wallet
# 5. Set wallet: dfx identity set-wallet <wallet-id> --identity fl_server --network ic
```

#### 1.2 Deploy to Mainnet
```bash
cd icp/fl_cvd_backend

# Deploy to mainnet (costs ~1T cycles)
dfx deploy fl_cvd_backend_backend --network ic --identity fl_server --with-cycles 1000000000000

# Note the mainnet canister ID (e.g., wstch-aqaaa-aaaao-a4osq-cai)
dfx canister id fl_cvd_backend_backend --network ic
```

#### 1.3 Setup Mainnet Canister
```bash
# Initialize admin
dfx canister call fl_cvd_backend_backend init_admin --network ic --identity fl_server

# Verify
dfx canister call fl_cvd_backend_backend get_system_stats --network ic --identity fl_server
```

### Step 2: Client Machine Mainnet Setup

#### 2.1 Use Existing Identities
```bash
# Use the same identity names as local
dfx identity use fl_client_1

# Get principal ID
dfx identity get-principal --identity fl_client_1
```

#### 2.2 Register with Mainnet Canister
```bash
# Register with mainnet canister (replace with actual mainnet canister ID)
dfx canister call wstch-aqaaa-aaaao-a4osq-cai register_client_enhanced --network ic --identity fl_client_1
```

### Step 3: Admin Approval on Mainnet

```bash
# On server machine, approve clients
dfx canister call fl_cvd_backend_backend admin_approve_client '(principal "CLIENT_PRINCIPAL_ID")' --network ic --identity fl_server
```

---

## 🏋️ Running Training

### Local Network Training

#### Server Machine
```bash
# Set environment for local network
export ICP_CLIENT_IDENTITY_NAME=fl_server
export ICP_NETWORK=local

# Start server (2 rounds, minimum 3 clients)
uv run python server/server.py --rounds 2 --min-clients 3
```

#### Client Machines
```bash
# Client 1
export ICP_CLIENT_IDENTITY_NAME=fl_client_1
export ICP_CANISTER_ID=uxrrr-q7777-77774-qaaaq-cai  # Use your local canister ID
export ICP_NETWORK=local
export CLIENT_NAME="Healthcare Provider 1"
export CLIENT_ORGANIZATION="Hospital 1"

uv run python client/client.py --dataset dataset/clients/client1_data.csv --trees 30

# Client 2 (on different machine)
export ICP_CLIENT_IDENTITY_NAME=fl_client_2
export ICP_CANISTER_ID=uxrrr-q7777-77774-qaaaq-cai
export ICP_NETWORK=local
export CLIENT_NAME="Healthcare Provider 2"
export CLIENT_ORGANIZATION="Hospital 2"

uv run python client/client.py --dataset dataset/clients/client2_data.csv --trees 30

# Client 3 (on different machine)
export ICP_CLIENT_IDENTITY_NAME=fl_client_3
export ICP_CANISTER_ID=uxrrr-q7777-77774-qaaaq-cai
export ICP_NETWORK=local
export CLIENT_NAME="Healthcare Provider 3"
export CLIENT_ORGANIZATION="Hospital 3"

uv run python client/client.py --dataset dataset/clients/client3_data.csv --trees 30
```

### Mainnet Training

#### Server Machine
```bash
# Set environment for mainnet
export ICP_CLIENT_IDENTITY_NAME=fl_server
export ICP_NETWORK=ic

# Start server
uv run python server/server.py --rounds 2 --min-clients 3
```

#### Client Machines
```bash
# Client 1
export ICP_CLIENT_IDENTITY_NAME=fl_client_1
export ICP_CANISTER_ID=wstch-aqaaa-aaaao-a4osq-cai  # Use your mainnet canister ID
export ICP_NETWORK=ic
export CLIENT_NAME="Healthcare Provider 1"
export CLIENT_ORGANIZATION="Hospital 1"

uv run python client/client.py --dataset dataset/clients/client1_data.csv --trees 30

# Repeat for other clients with their respective identities and datasets
```

---

## 🔍 Querying Results

### Method 1: Direct dfx Commands

#### Local Network
```bash
# Get system statistics
dfx canister call fl_cvd_backend_backend get_system_stats --identity fl_server

# Get training history
dfx canister call fl_cvd_backend_backend get_training_history --identity fl_server

# Get specific round metadata
dfx canister call fl_cvd_backend_backend get_training_round_metadata '(1)' --identity fl_server
```

#### Mainnet
```bash
# Get system statistics
dfx canister call wstch-aqaaa-aaaao-a4osq-cai get_system_stats --network ic --identity fl_server

# Get training history
dfx canister call wstch-aqaaa-aaaao-a4osq-cai get_training_history --network ic --identity fl_server

# Get specific round metadata
dfx canister call wstch-aqaaa-aaaao-a4osq-cai get_training_round_metadata '(1)' --network ic --identity fl_server
```

### Method 2: Python Remote Client

#### For Local Network
```bash
# Get system stats
python remote_mainnet_client.py --action stats --identity fl_server --canister-id uxrrr-q7777-77774-qaaaq-cai --network local

# Get training history
python remote_mainnet_client.py --action history --identity fl_server --canister-id uxrrr-q7777-77774-qaaaq-cai --network local
```

#### For Mainnet
```bash
# Get system stats
python remote_mainnet_client.py --action stats --identity fl_server

# Get training history  
python remote_mainnet_client.py --action history --identity fl_server

# Get round metadata
python remote_mainnet_client.py --action round --round-id 1 --identity fl_server
```

### Method 3: Web Interface (Mainnet Only)

Visit the Candid interface:
- **URL**: https://a4gq6-oaaaa-aaaab-qaa4q-cai.raw.icp0.io/?id=wstch-aqaaa-aaaao-a4osq-cai
- Connect with your dfx identity
- Call methods directly from the web interface

---

## ✅ Model Verification

### Verify Model Integrity

#### Local Network
```bash
# Verify specific round
uv run python verify_model.py --round 1

# Verify all rounds
uv run python verify_model.py --all

# List available models
uv run python verify_model.py --list
```

#### Mainnet
```bash
# Set network environment
export ICP_NETWORK=ic

# Verify specific round
ICP_NETWORK=ic uv run python verify_model.py --round 1

# Verify all rounds
ICP_NETWORK=ic uv run python verify_model.py --all
```

### Manual Hash Verification

```bash
# Calculate file hash
sha256sum models/federated_cvd_model_round_1_*.joblib

# Compare with stored hash from canister query
dfx canister call fl_cvd_backend_backend get_training_round_metadata '(1)' --identity fl_server
```

---

## 🚀 Quick Setup (Automated)

For a fully automated setup, use the quick setup script:

```bash
# Run automated setup
uv run python quick_setup.py

# This will:
# 1. Check prerequisites
# 2. Start local ICP network
# 3. Create identities
# 4. Deploy canister
# 5. Register and approve clients
# 6. Create environment configuration
```

---

## 🧪 Model Testing

### Load and Test Models

#### Create Test Script
```python
# test_model.py
import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
import numpy as np

def test_model(model_path, test_data_path):
    """Test a federated learning model."""
    
    # Load model
    model = joblib.load(model_path)
    print(f"✅ Loaded model: {model_path}")
    
    # Load test data
    test_data = pd.read_csv(test_data_path)
    
    # Prepare features and labels
    X_test = test_data.drop(['target'], axis=1)
    y_test = test_data['target']
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"📊 Test Results:")
    print(f"   Accuracy: {accuracy:.4f}")
    print(f"   Test samples: {len(y_test)}")
    
    # Detailed classification report
    print("\n📋 Classification Report:")
    print(classification_report(y_test, y_pred))
    
    return accuracy

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python test_model.py <model_path> <test_data_path>")
        sys.exit(1)
    
    model_path = sys.argv[1]
    test_data_path = sys.argv[2]
    
    test_model(model_path, test_data_path)
```

#### Run Model Tests
```bash
# Test round 1 model
uv run python test_model.py models/federated_cvd_model_round_1_*.joblib dataset/test_data.csv

# Test round 2 model
uv run python test_model.py models/federated_cvd_model_round_2_*.joblib dataset/test_data.csv

# Compare models
uv run python compare_models.py
```

### Model Performance Analysis

#### Create Analysis Script
```python
# analyze_training.py
import joblib
import matplotlib.pyplot as plt
import pandas as pd

def analyze_training_progression():
    """Analyze how model performance improves across rounds."""
    
    rounds_data = []
    
    # Load models from different rounds
    for round_id in [1, 2]:
        try:
            model_files = glob.glob(f"models/federated_cvd_model_round_{round_id}_*.joblib")
            if model_files:
                model = joblib.load(model_files[0])
                
                # Test on validation set
                accuracy = test_model_accuracy(model, "dataset/validation_data.csv")
                
                rounds_data.append({
                    'round': round_id,
                    'accuracy': accuracy,
                    'model_file': model_files[0]
                })
        except Exception as e:
            print(f"Error loading round {round_id}: {e}")
    
    # Plot progression
    if rounds_data:
        df = pd.DataFrame(rounds_data)
        plt.figure(figsize=(10, 6))
        plt.plot(df['round'], df['accuracy'], marker='o', linewidth=2, markersize=8)
        plt.title('Federated Learning Model Performance Progression')
        plt.xlabel('Training Round')
        plt.ylabel('Accuracy')
        plt.grid(True, alpha=0.3)
        plt.savefig('training_progression.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("📈 Training Progression Analysis:")
        for _, row in df.iterrows():
            print(f"   Round {row['round']}: {row['accuracy']:.4f} accuracy")

if __name__ == "__main__":
    analyze_training_progression()
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Canister Not Found
```bash
# Problem: "Canister not found" error
# Solution: Check canister ID and network

# Get correct canister ID
dfx canister id fl_cvd_backend_backend --network local  # for local
dfx canister id fl_cvd_backend_backend --network ic     # for mainnet
```

#### 2. Identity Issues
```bash
# Problem: Authentication failed
# Solution: Verify identity exists and is correct

dfx identity list
dfx identity get-principal --identity fl_server
```

#### 3. Network Connection Issues
```bash
# Problem: Cannot connect to local network
# Solution: Restart dfx

dfx stop
dfx start --background --clean
```

#### 4. Cycles Issues (Mainnet)
```bash
# Problem: Insufficient cycles
# Solution: Check wallet balance

dfx wallet balance --identity fl_server --network ic

# Top up cycles if needed
```

#### 5. Client Registration Issues
```bash
# Problem: Client registration fails
# Solution: Check if client is already registered

dfx canister call fl_cvd_backend_backend get_client_info '(principal "CLIENT_PRINCIPAL_ID")' --identity fl_server
```

### Debug Commands

#### Check System Status
```bash
# Local network
dfx canister call fl_cvd_backend_backend get_system_stats --identity fl_server

# Mainnet
dfx canister call wstch-aqaaa-aaaao-a4osq-cai get_system_stats --network ic --identity fl_server
```

#### View Logs
```bash
# Check dfx logs
dfx logs

# Check training logs
tail -f logs/server.log
tail -f logs/client_1.log
```

#### Reset Local Environment
```bash
# Clean restart
dfx stop
dfx start --background --clean
dfx deploy
```

---

## 📚 Additional Resources

### Documentation
- [Internet Computer Documentation](https://internetcomputer.org/docs)
- [dfx Command Reference](https://internetcomputer.org/docs/current/references/cli-reference/dfx-parent)
- [Candid Guide](https://internetcomputer.org/docs/current/developer-docs/backend/candid/)

### Support
- [IC Developer Forum](https://forum.dfinity.org)
- [IC Discord](https://discord.gg/cA7y6ezyE2)
- [GitHub Issues](https://github.com/dfinity/sdk/issues)

### Cost Calculator
- [Cycles Cost Calculator](https://internetcomputer.org/docs/current/developer-docs/gas-cost)

---

## 🎉 Conclusion

You now have a complete federated learning system running on the Internet Computer! This setup provides:

- ✅ **Privacy-preserving training** across multiple organizations
- ✅ **Blockchain-based authentication** and audit trails
- ✅ **Model integrity verification** using cryptographic hashes
- ✅ **Scalable architecture** supporting both local testing and global deployment
- ✅ **Complete transparency** with immutable training records

Your federated learning system is ready for real-world healthcare applications! 🏥🚀
