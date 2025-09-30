# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Federated Learning System for Cardiovascular Disease (CVD) Prediction using scikit-learn's Random Forest, Flower AI, and Internet Computer Protocol (ICP) blockchain. The system enables privacy-preserving machine learning across multiple healthcare providers with blockchain-based authentication and audit trails.

**Key Technologies:**
- **ML Framework:** scikit-learn (Random Forest)
- **Federated Learning:** Flower AI (flwr)
- **Blockchain:** Internet Computer Protocol (ICP) - Motoko smart contracts
- **Package Manager:** uv
- **Languages:** Python (ML/FL), Motoko (ICP canisters)

## Essential Commands

### Development Setup
```bash
# Install dependencies
uv sync
# or manually:
uv pip install -r requirements.txt

# Start local ICP network
cd icp/fl_cvd_backend
dfx start --background --clean
dfx deploy
dfx canister id fl_cvd_backend_backend

# Initialize admin role (one-time setup)
uv run python icp_cli.py init-admin
```

### Running Federated Learning

**Start Server:**
```bash
# Using bash script (recommended)
./start_server.sh

# Or manually with environment variables
export ICP_CLIENT_IDENTITY_NAME=fl_server
export ICP_CANISTER_ID=<canister-id>
export ICP_NETWORK=local  # or "ic" for mainnet
uv run python server/server.py --rounds 2 --min-clients 3
```

**Start Clients:**
```bash
# Client 1
./start_client_1.sh

# Client 2 and 3
./start_client_2.sh
./start_client_3.sh

# Or manually
export ICP_CLIENT_IDENTITY_NAME=fl_client_1
export CLIENT_NAME="Healthcare Provider 1"
export CLIENT_ORGANIZATION="Hospital 1"
uv run python client/client.py --dataset dataset/clients/client1_data.csv --trees 30
```

### ICP Canister Management

```bash
# View system status
uv run python icp_cli.py status

# List all clients
uv run python icp_cli.py clients

# List clients pending approval
uv run python icp_cli.py pending

# Approve a client (requires admin identity)
uv run python icp_cli.py approve <CLIENT_PRINCIPAL_ID>

# Register a new client
uv run python icp_cli.py register

# View training history
uv run python icp_cli.py rounds

# Orchestrated training (recommended)
uv run python icp_cli.py train --rounds 3 dataset/clients/*.csv
```

### Model Verification

```bash
# Verify specific round model against blockchain hash
uv run python verify_model.py --round 1

# Verify all models
uv run python verify_model.py --all

# List available models
uv run python verify_model.py --list

# Test model performance
uv run python test_model.py models/federated_cvd_model_round_1_*.joblib dataset/test_data.csv

# Analyze training progression
uv run python analyze_training.py
```

### Testing

```bash
# Test ICP client connection
uv run python test_icp_client.py

# Test authentication system
uv run python test_auth_system.py

# Test federated model
uv run python test_federated_model.py
```

## Architecture

### Three-Tier System Design

**1. ICP Canister (Blockchain Backend)**
- **Location:** `icp/fl_cvd_backend/src/fl_cvd_backend_backend/main.mo`
- **Language:** Motoko
- **Role:** Authentication, authorization, audit trail, model metadata storage
- **Key Features:** Role-based access control (Admin/Server/Client/Observer), client approval workflow, immutable training records

**2. Flower Server (Aggregation Coordinator)**
- **Location:** `server/server.py`
- **Role:** Coordinates federated learning rounds, aggregates client models
- **Identity:** Uses `fl_server` dfx identity (Server role in canister)
- **Process:**
  1. Starts training round on ICP canister
  2. Waits for minimum clients (default: 3)
  3. Receives model updates from clients
  4. Aggregates Random Forest models (tree-by-tree)
  5. Stores aggregated model and metadata on ICP
  6. Repeats for configured rounds

**3. Flower Clients (Healthcare Providers)**
- **Location:** `client/client.py`
- **Role:** Train local models on private data, submit updates
- **Identities:** `fl_client_1`, `fl_client_2`, `fl_client_3` (Client role in canister)
- **Process:**
  1. Authenticate with ICP canister
  2. Connect to Flower server
  3. Receive global model parameters
  4. Train Random Forest on local dataset
  5. Submit model update to server

### Authentication Flow

1. **Identity Creation:** Each participant has a dfx identity (cryptographic keypair)
2. **Principal IDs:** Derived from identities, used for blockchain authentication
3. **Registration:** Clients register with canister (Pending status)
4. **Admin Approval:** Admin approves clients (Active status)
5. **Training Participation:** Only Active clients can participate in training

### Model Aggregation Strategy

- **Algorithm:** Custom Random Forest aggregation (not standard FedAvg)
- **Method:** Tree-by-tree aggregation - combines individual decision trees from all clients
- **Serialization:** Uses `trees_to_numpy_arrays()` / `numpy_arrays_to_trees()` for network transfer
- **Storage:** Aggregated models saved as `.joblib` files with cryptographic hashes stored on-chain

## Key Files and Modules

### Core Components

**`icp_auth_client.py`**
- Authenticated ICP client wrapper
- Handles identity loading, canister communication
- Used by both server and clients

**`icp_client.py`**
- Basic ICP client without authentication
- Direct canister interaction functions
- Used for querying system status

**`icp_cli.py`**
- Command-line interface for canister management
- Admin operations (approve, reject, setup)
- Training orchestration

**`client/utils/federated_utils.py`**
- Random Forest aggregation algorithms
- Tree serialization/deserialization
- Model merging logic

**`client/utils/data_preprocessing.py`**
- Data loading and preprocessing
- Feature engineering
- Train/test split

**`client/utils/model.py`**
- CVDModel wrapper class
- Random Forest configuration
- Training and evaluation methods

### Supporting Scripts

- **`setup_icp_auth.py`:** Automated setup for identities and environment
- **`remote_mainnet_client.py`:** Query mainnet canister remotely
- **`verify_model.py`:** Verify model integrity against blockchain hashes
- **`run_federated_learning.py`:** Orchestrated FL workflow
- **`monitor_logs.py`:** Real-time log monitoring

## Environment Configuration

**Required Environment Variables:**

For Server:
```
ICP_CLIENT_IDENTITY_NAME=fl_server
ICP_CANISTER_ID=<your-canister-id>
ICP_NETWORK=local  # or "ic" for mainnet
```

For Clients:
```
ICP_CLIENT_IDENTITY_NAME=fl_client_1  # or fl_client_2, fl_client_3
ICP_CANISTER_ID=<your-canister-id>
ICP_NETWORK=local
CLIENT_NAME="Healthcare Provider 1"
CLIENT_ORGANIZATION="Hospital ABC"
CLIENT_LOCATION="City, Country"
```

**Identity Management:**
- Identities stored in `~/.config/dfx/identity/`
- Use `dfx identity use <name>` to switch identities
- Get principal ID: `dfx identity get-principal`

## Deployment

### Local Network (Development)
```bash
cd icp/fl_cvd_backend
dfx start --background --clean
dfx deploy
```

### Mainnet (Production)
```bash
cd icp/fl_cvd_backend
dfx deploy fl_cvd_backend_backend --network ic --with-cycles 1000000000000
```

**Mainnet Prerequisites:**
- ICP tokens from exchange
- Convert ICP to cycles via NNS (https://nns.ic0.app)
- Configure cycles wallet

## Common Patterns

### Adding a New Client

1. Create identity: `dfx identity new fl_client_4`
2. Get principal: `dfx identity get-principal --identity fl_client_4`
3. Register: `uv run python icp_cli.py register` (while using client identity)
4. Admin approves: `uv run python icp_cli.py approve <PRINCIPAL_ID>`
5. Start client with appropriate environment variables

### Modifying Canister Logic

1. Edit `icp/fl_cvd_backend/src/fl_cvd_backend_backend/main.mo`
2. Redeploy: `cd icp/fl_cvd_backend && dfx deploy`
3. Note: Local network data is transient (marked as `transient var`)
4. For production, convert storage to `stable var` for persistence

### Adjusting Training Parameters

- **Number of rounds:** `--rounds` flag on server
- **Minimum clients:** `--min-clients` flag on server
- **Trees per client:** `--trees` flag on client
- **Maximum trees per round:** Set in `CVDFedAvgStrategy.__init__()` (default: 1000)

## Troubleshooting

**"Canister not found" error:**
- Check canister ID: `dfx canister id fl_cvd_backend_backend`
- Verify network: local uses local canister IDs, mainnet uses different IDs

**"Permission denied" / "Not authorized":**
- Check active identity: `dfx identity whoami`
- Verify role in canister: `uv run python icp_cli.py status`
- Ensure client is approved (Active status)

**"Client not approved" error:**
- Admin must approve: `uv run python icp_cli.py approve <PRINCIPAL_ID>`

**Server/Client connection issues:**
- Verify server is running and listening on correct port (default: 8080)
- Check `SERVER_ADDRESS` environment variable (default: 127.0.0.1:8080)
- Client implements exponential backoff retry with 300s timeout

**Model verification failures:**
- Models are stored in `models/` directory
- Verify model file exists and matches round ID
- Check blockchain hash: `uv run python icp_cli.py rounds`

## Project-Specific Notes

- **Minimum 3 clients required** for training to start (configurable)
- **Random Forest aggregation** is custom - not using standard FedAvg weights
- **Blockchain stores metadata only** - actual model files stored locally
- **Transient storage** in canister - data lost on canister restart (local network)
- **Authentication is mandatory** - all operations require valid dfx identity
- **Client approval workflow** - admin gate before participation
- Use **bash scripts** (`start_server.sh`, `start_client_*.sh`) for consistent environments