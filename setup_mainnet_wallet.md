# 💰 Mainnet Cycles Wallet Setup Guide

Before deploying to ICP mainnet, you need to set up a cycles wallet for the `fl_server` identity.

## 🔑 Your Identity Information

- **Identity**: `fl_server`
- **Principal ID**: `d5mfv-oefjt-6bphj-2hody-nzrw2-6dlny-cyqpq-kb3h4-sambi-eflno-xae`

## 💳 Option 1: Using NNS Dapp (Recommended)

### Step 1: Get ICP Tokens
1. Purchase ICP tokens from an exchange (Coinbase, Binance, etc.)
2. You'll need approximately 2-3 ICP tokens (~$20-30 USD)

### Step 2: Set up NNS Dapp
1. Go to https://nns.ic0.app
2. Click "Login" and select "Internet Identity"
3. Create or use existing Internet Identity
4. Connect your `fl_server` identity

### Step 3: Convert ICP to Cycles
1. In NNS dapp, go to "Canisters" section
2. Click "Create Canister"
3. Convert ICP to cycles (1 ICP ≈ 1T cycles)
4. Create a cycles wallet canister

### Step 4: Configure dfx
```bash
# Set the wallet for your identity
dfx identity set-wallet <wallet-canister-id> --identity fl_server --network ic

# Verify wallet is set
dfx wallet balance --identity fl_server --network ic
```

## 💳 Option 2: Using dfx Directly

If you already have a cycles wallet:

```bash
# Set existing wallet
dfx identity set-wallet <your-wallet-id> --identity fl_server --network ic

# Check balance
dfx wallet balance --identity fl_server --network ic
```

## 💳 Option 3: Development/Testing

For development purposes, you might be able to get free cycles from:
- IC developer grants
- Community faucets (if available)
- Testnet cycles

## 🔍 Verify Setup

Once your wallet is configured, verify it's working:

```bash
# Check wallet balance
dfx wallet balance --identity fl_server --network ic

# Should show something like: "1.000 TC (trillion cycles)"
```

## 🚀 Ready to Deploy

Once your wallet shows a balance > 1T cycles, you're ready to deploy:

```bash
uv run python deploy_mainnet_canister.py
```

## 💰 Cost Breakdown

- **Canister Creation**: ~1T cycles (~$1.30)
- **Canister Operations**: ~100B cycles per training round (~$0.13)
- **Total for deployment + 2 rounds**: ~1.2T cycles (~$1.56)
- **Recommended minimum**: 2T cycles (~$2.60)

## ❓ Need Help?

If you encounter issues:
1. Check the Internet Computer documentation: https://internetcomputer.org/docs
2. Visit the IC developer forum: https://forum.dfinity.org
3. Check the dfx documentation: https://internetcomputer.org/docs/current/references/cli-reference/dfx-parent

## 🎯 Next Steps

After wallet setup:
1. Run `uv run python deploy_mainnet_canister.py`
2. Register and approve clients
3. Execute federated learning on mainnet
4. Query metadata from mainnet canister
