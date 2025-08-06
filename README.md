# Federated Learning System for CVD Prediction

This project implements a federated learning system using scikit-learn's Random Forest, Flower AI, and ICP smart contracts to predict cardiovascular disease (CVD) while preserving data privacy.

## Technology Stack
- **Machine Learning**: scikit-learn (Random Forest)
- **Federated Learning**: Flower AI
- **Blockchain**: Internet Computer Protocol (ICP)
- **Frontend**: ReactJS
- **Smart Contracts**: Motoko
- **Languages**: Python (ML and federated learning), Motoko (ICP canisters)
- **Package Manager**: uv

## Directory Structure
```
.
├── client/          # Federated learning clients
├── dataset/         # Input dataset (cardio_train.csv)
├── docs/            # Documentation
├── icp/             # ICP smart contracts
├── models/          # Output model files
├── server/          # Federated learning server
├── QWEN.md          # Task list and project overview
└── README.md        # This file
```

## 🔐 Authentication System

This project now includes a comprehensive **role-based authentication system** with:

- **Admin approval workflow** for client registration
- **Principal ID-based authentication** using ICP identities
- **Environment-based credential management** via .env files
- **Role-based permissions** (Admin, Server, Client, Observer)
- **Blockchain audit trail** for all operations

## 🚀 Quick Setup

### Automated Setup (Recommended)
```bash
# Install dependencies
uv pip install -r requirements.txt

# Run automated setup script
uv run python setup_icp_auth.py

# Initialize admin role
uv run python icp_cli.py init-admin

# Start federated learning
uv run python icp_cli.py quick-train
```

### Manual Setup
1. Install Python 3.10+
2. Install uv package manager
3. Install ICP development tools (dfx 0.22+)
4. Install required Python packages with `uv pip install -r requirements.txt`
5. Follow the detailed setup in [AUTHENTICATION.md](AUTHENTICATION.md)

## 🎮 Running the System

### For Administrators
```bash
# List clients pending approval
uv run python icp_cli.py pending

# Approve a client
uv run python icp_cli.py approve <CLIENT_PRINCIPAL_ID>

# Start orchestrated training
uv run python icp_cli.py train --rounds 3 dataset/clients/*.csv
```

### For Healthcare Providers (Clients)
```bash
# Register with the system (requires admin approval)
uv run python icp_cli.py register

# Start client after approval
uv run python client/client.py --dataset your-dataset.csv
```

### System Monitoring
```bash
# Check system status
uv run python icp_cli.py status

# View all clients
uv run python icp_cli.py clients

# View training history
uv run python icp_cli.py rounds
```