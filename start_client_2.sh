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
export ICP_CLIENT_IDENTITY_NAME="fl_client_2"
export CLIENT_NAME="Healthcare Provider 2"
export CLIENT_ORGANIZATION="Hospital 2"
export CLIENT_LOCATION="Johor"
export CLIENT_DATASET="dataset/clients/client2_data.csv"
export SERVER_ADDRESS="127.0.0.1:8080"

echo "Starting federated learning client 1 with:"
echo "  Identity: $ICP_CLIENT_IDENTITY_NAME"
echo "  Client Name: $CLIENT_NAME"
echo "  Client Organization: $CLIENT_ORGANIZATION"
echo "  Client Location: $CLIENT_LOCATION"
echo "  Client Dataset: $CLIENT_DATASET"
echo "  SERVER_ADDRESS: $SERVER_ADDRESS"
echo "  Trees: 30"
echo ""

# Start the server process
echo "Executing: uv run python client/client.py --dataset $CLIENT_DATASET --trees 30"
uv run python client/client.py --dataset $CLIENT_DATASET --trees 30
