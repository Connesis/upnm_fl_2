# 🔐 Client Authentication System Guide

This guide explains the comprehensive client authentication system for federated learning, which ensures only approved clients can participate in training.

## 🎯 Overview

The authentication system implements a secure workflow where:

1. **Clients register** their principal IDs with the canister
2. **Admin approves** client registrations
3. **Server verifies** client authentication before accepting training data
4. **Only approved clients** can participate in federated learning

## 🔑 Key Components

### 1. Principal ID Management

Each client has a unique **Principal ID** derived from their ICP identity:

```bash
# Get principal ID for a client identity
dfx identity use fl_client_1
dfx identity get-principal
# Output: rdmx6-jaaaa-aaaah-qcaiq-cai
```

### 2. Client Registration Process

When a client starts, it automatically:

1. **Connects to ICP canister** using configured identity
2. **Retrieves principal ID** from the identity
3. **Registers with metadata** (name, organization, contact)
4. **Waits for admin approval** before participating

### 3. Server Authentication Verification

The server verifies each client by:

1. **Checking authentication status** in client responses
2. **Rejecting unauthenticated clients** from aggregation
3. **Logging authentication events** for audit trail

## 🚀 Usage Workflow

### Step 1: Client Registration

Clients automatically register when they start:

```bash
# Client registers with identity fl_client_1
ICP_CLIENT_IDENTITY_NAME=fl_client_1 \
CLIENT_NAME="Hospital A" \
CLIENT_ORGANIZATION="Healthcare Network" \
CLIENT_CONTACT_EMAIL="admin@hospital-a.com" \
uv run python client/client.py --dataset dataset/clients/client1_data.csv
```

**Expected Output:**
```
🔑 Client principal ID: rdmx6-jaaaa-aaaah-qcaiq-cai
📋 Registration submitted. Waiting for admin approval...
   Client: Hospital A
   Organization: Healthcare Network
   Contact: admin@hospital-a.com
   Principal ID: rdmx6-jaaaa-aaaah-qcaiq-cai
⚠️  Client will not be able to participate in training until approved
```

### Step 2: Admin Approval

Admin approves pending registrations:

```bash
# List pending clients
uv run python manage_client_auth.py list-pending

# Approve specific client
uv run python manage_client_auth.py approve rdmx6-jaaaa-aaaah-qcaiq-cai

# Interactive approval process
uv run python manage_client_auth.py interactive
```

### Step 3: Authenticated Training

Once approved, clients can participate in training:

```bash
# Start server
ICP_CLIENT_IDENTITY_NAME=fl_server uv run python server/server.py --rounds 3

# Start approved client
ICP_CLIENT_IDENTITY_NAME=fl_client_1 uv run python client/client.py --dataset dataset/clients/client1_data.csv
```

**Expected Server Output:**
```
✅ Authenticated client contributed 100 trees
✅ Processed 1/1 authenticated clients
```

## 🛠️ Management Commands

### List Pending Clients

```bash
uv run python manage_client_auth.py list-pending
```

**Output:**
```
📊 Found 2 pending client(s):

1. Client Registration:
   🔑 Principal ID: rdmx6-jaaaa-aaaah-qcaiq-cai
   👤 Name: Hospital A
   🏥 Organization: Healthcare Network
   📧 Contact: admin@hospital-a.com
```

### Approve Client

```bash
uv run python manage_client_auth.py approve rdmx6-jaaaa-aaaah-qcaiq-cai
```

### List Active Clients

```bash
uv run python manage_client_auth.py list-active
```

### Interactive Approval

```bash
uv run python manage_client_auth.py interactive
```

## 🧪 Testing Authentication

### Test Unauthenticated Client

```bash
uv run python test_client_authentication.py
```

This script tests:
1. **Unauthenticated client behavior** - should be rejected
2. **Client registration process** - should create pending registration
3. **Current authentication status** - shows pending/active clients

## 🔒 Security Features

### 1. Principal ID Verification

- Each client must provide valid principal ID
- Principal IDs are cryptographically derived from identities
- Cannot be forged or spoofed

### 2. Admin-Only Approval

- Only admin can approve/reject clients
- Admin identity is set during canister initialization
- Role-based access control enforced

### 3. Server-Side Validation

- Server verifies authentication before processing
- Unauthenticated clients are rejected from aggregation
- All authentication events are logged

### 4. Audit Trail

- All registrations, approvals, and rejections are logged
- Principal IDs and timestamps recorded
- Full traceability of client access

## 📊 Authentication States

| State | Description | Can Train? | Actions Available |
|-------|-------------|------------|-------------------|
| **Unregistered** | Client not in system | ❌ No | Register |
| **Pending** | Registered, awaiting approval | ❌ No | Wait for approval |
| **Active** | Approved and active | ✅ Yes | Participate in training |
| **Rejected** | Registration rejected | ❌ No | Re-register if needed |

## 🚨 Error Handling

### Client-Side Errors

```
❌ Authentication required: Client must be approved by admin before training
   Principal ID: rdmx6-jaaaa-aaaah-qcaiq-cai
   Please contact admin to approve this client
```

### Server-Side Errors

```
❌ Rejecting unauthenticated client
❌ No authenticated clients found. Cannot proceed with aggregation.
```

## 🔧 Configuration

### Environment Variables

**Client Configuration:**
```bash
ICP_CLIENT_IDENTITY_NAME=fl_client_1    # Client identity name
CLIENT_NAME="Hospital A"                # Human-readable name
CLIENT_ORGANIZATION="Healthcare Net"    # Organization name
CLIENT_CONTACT_EMAIL="admin@hospital.com" # Contact email
```

**Server Configuration:**
```bash
ICP_CLIENT_IDENTITY_NAME=fl_server      # Server identity name
ICP_NETWORK=local                       # ICP network
ICP_CANISTER_ID=your-canister-id        # Canister ID
```

## 📈 Best Practices

### 1. Identity Management

- Use descriptive identity names (`fl_client_hospital_a`)
- Keep identity credentials secure
- Rotate identities periodically

### 2. Registration Process

- Provide complete metadata during registration
- Use official contact information
- Register clients before training sessions

### 3. Admin Workflow

- Review client registrations promptly
- Verify client legitimacy before approval
- Monitor active client list regularly

### 4. Security Monitoring

- Check authentication logs regularly
- Monitor for unauthorized access attempts
- Audit client participation patterns

## 🎉 Summary

The client authentication system provides:

- **🔐 Secure Access Control**: Only approved clients can participate
- **👥 Identity Management**: Principal ID-based authentication
- **📋 Admin Oversight**: Manual approval process for new clients
- **🔍 Audit Trail**: Complete logging of authentication events
- **⚡ Easy Management**: Simple commands for client approval
- **🧪 Testing Tools**: Comprehensive testing and validation

This ensures that your federated learning system maintains security and compliance while providing a smooth user experience for legitimate participants.
