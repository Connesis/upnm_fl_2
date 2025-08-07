# 🌳 Tree Configuration Guide

This guide explains how to control the number of trees sent from each client in the federated learning system.

## 📊 Overview

The federated learning system uses Random Forest models, where each client trains a local Random Forest and sends its decision trees to the server for aggregation. You can control:

1. **Trees per Client**: How many trees each client trains and sends
2. **Server Tree Limit**: Maximum total trees the server accepts per round
3. **Tree Sampling**: How the server handles excess trees

## 🎛️ Configuration Parameters

### 1. Client-Side Configuration

#### **Primary Control: `n_estimators` Parameter**

The main parameter controlling trees per client is in `client/utils/model.py`:

```python
class CVDModel:
    def __init__(self, 
                 n_estimators: int = 100,  # ← TREES PER CLIENT
                 max_depth: int = 10,
                 min_samples_leaf: int = 5,
                 random_state: int = 42):
```

#### **Command Line Control**

You can now control trees per client via command line:

```bash
# Run client with 50 trees
python client/client.py --dataset dataset/clients/client1_data.csv --trees 50

# Run client with 200 trees  
python client/client.py --dataset dataset/clients/client1_data.csv --trees 200
```

### 2. Server-Side Configuration

#### **Tree Limit Parameter**

The server has a configurable limit for total trees per round:

```bash
# Run server with 600 tree limit (default)
python server/server.py --max-trees 600

# Run server with 1000 tree limit
python server/server.py --max-trees 1000
```

## 🚀 Usage Examples

### Example 1: Small Trees Configuration

```bash
# Start server with 300 tree limit
python server/server.py --rounds 3 --max-trees 300

# Start clients with 50 trees each
python client/client.py --dataset dataset/clients/client1_data.csv --trees 50
python client/client.py --dataset dataset/clients/client2_data.csv --trees 50
python client/client.py --dataset dataset/clients/client3_data.csv --trees 50

# Result: 3 clients × 50 trees = 150 trees per round (within 300 limit)
```

### Example 2: Large Trees Configuration

```bash
# Start server with 1000 tree limit
python server/server.py --rounds 3 --max-trees 1000

# Start clients with 200 trees each
python client/client.py --dataset dataset/clients/client1_data.csv --trees 200
python client/client.py --dataset dataset/clients/client2_data.csv --trees 200
python client/client.py --dataset dataset/clients/client3_data.csv --trees 200

# Result: 3 clients × 200 trees = 600 trees per round (within 1000 limit)
```

### Example 3: Using the Automated Script

```bash
# Run with default 100 trees per client
python run_federated_learning.py

# Run with 75 trees per client
python run_federated_learning.py --trees 75

# Run with 150 trees per client
python run_federated_learning.py --trees 150
```

### Example 4: Testing Configuration

```bash
# Test with 25 trees per client (fast testing)
python test_tree_configuration.py --trees 25

# Test with 100 trees per client
python test_tree_configuration.py --trees 100
```

## 📈 Tree Scaling Behavior

### Current Default Configuration
- **Client Trees**: 100 trees per client
- **Server Limit**: 600 trees per round
- **3 Clients**: 3 × 100 = 300 trees per round ✅

### What Happens with Different Client Counts

| Clients | Trees/Client | Total Trees | Server Limit | Result |
|---------|--------------|-------------|--------------|---------|
| 1 | 100 | 100 | 600 | ✅ All trees used |
| 2 | 100 | 200 | 600 | ✅ All trees used |
| 3 | 100 | 300 | 600 | ✅ All trees used |
| 3 | 200 | 600 | 600 | ✅ All trees used |
| 3 | 250 | 750 | 600 | ⚠️ Sampled to 600 |
| 4 | 200 | 800 | 600 | ⚠️ Sampled to 600 |

### Tree Sampling Logic

When total trees exceed the server limit:

1. **Warning Issued**: Server logs a warning about excess trees
2. **Random Sampling**: Trees are randomly sampled to stay within limit
3. **Diversity Preserved**: Sampling maintains representation from all clients
4. **Reproducible**: Uses fixed random seed (42) for consistent results

## 🔧 Advanced Configuration

### Environment Variables

You can also set trees per client via environment variables:

```bash
# Set default trees for all clients
export FL_DEFAULT_TREES=150

# Run client (will use environment variable if no --trees specified)
python client/client.py --dataset dataset/clients/client1_data.csv
```

### Programmatic Configuration

For custom scripts, you can configure trees programmatically:

```python
from client.utils.model import CVDModel

# Create model with custom tree count
model = CVDModel(n_estimators=75)  # 75 trees per client
```

## 📊 Performance Considerations

### Tree Count vs Performance

| Trees/Client | Training Time | Model Size | Accuracy | Memory Usage |
|--------------|---------------|------------|----------|--------------|
| 25 | Fast | Small | Good | Low |
| 50 | Fast | Small | Good | Low |
| 100 | Medium | Medium | Better | Medium |
| 200 | Slow | Large | Best | High |
| 300+ | Very Slow | Very Large | Best | Very High |

### Recommendations

- **Development/Testing**: 25-50 trees per client
- **Production**: 100-200 trees per client  
- **High Accuracy**: 200-300 trees per client
- **Resource Constrained**: 50-100 trees per client

## 🎯 Summary

The tree configuration system provides flexible control over model complexity and training time:

1. **Client Control**: Use `--trees` parameter or modify `CVDModel(n_estimators=X)`
2. **Server Control**: Use `--max-trees` parameter to set total tree limits
3. **Automated Scripts**: Use `run_federated_learning.py --trees X` for easy testing
4. **Smart Sampling**: Server automatically handles excess trees while preserving diversity

This allows you to balance between model accuracy, training time, and resource usage based on your specific requirements.
