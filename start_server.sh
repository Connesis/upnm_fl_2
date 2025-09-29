#!/bin/bash

# Bash script to start the federated learning server
# Requires environment variables: ICP_CLIENT_IDENTITY_NAME, ICP_CANISTER_ID, ICP_NETWORK

set -e  # Exit on any error

# Check if required environment variables are set
#if [ -z "$ICP_CLIENT_IDENTITY_NAME" ]; then
#    echo "Error: ICP_CLIENT_IDENTITY_NAME environment variable is not set"
#    exit 1
#fi

#if [ -z "$ICP_CANISTER_ID" ]; then
#    echo "Error: ICP_CANISTER_ID environment variable is not set"
#    exit 1
#fi

#if [ -z "$ICP_NETWORK" ]; then
#    echo "Error: ICP_NETWORK environment variable is not set"
#    exit 1
#fi

# Export environment variables to ensure they're available
export ICP_CLIENT_IDENTITY_NAME="fl_server"
export ICP_CANISTER_ID="bkyz2-fmaaa-aaaaa-qaaaq-cai"

# set to "ic" for mainnet
export ICP_NETWORK="local"
export MIN_CLIENTS=3
export ROUNDS=2

echo "Starting federated learning server with:"
echo "  Identity: $ICP_CLIENT_IDENTITY_NAME"
echo "  Canister ID: $ICP_CANISTER_ID"
echo "  Network: $ICP_NETWORK"
echo "  Rounds: $ROUNDS"
echo "  Min Clients: $MIN_CLIENTS"
echo ""

# Start the server process
echo "Executing: uv run python server/server.py --rounds $ROUNDS --min-clients $MIN_CLIENTS"
uv run python server/server.py --rounds $ROUNDS --min-clients $MIN_CLIENTS
