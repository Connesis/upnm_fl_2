"""
Utilities for federated learning with Random Forest models.
"""
import numpy as np
import pickle
import base64
from typing import List, Dict, Any, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier


def serialize_random_forest(model: RandomForestClassifier) -> List[bytes]:
    """
    Serialize a Random Forest model into a list of serialized decision trees.
    
    Args:
        model: Trained RandomForestClassifier
        
    Returns:
        List of serialized decision trees as bytes
    """
    serialized_trees = []
    for estimator in model.estimators_:
        # Serialize each decision tree
        tree_bytes = pickle.dumps(estimator)
        serialized_trees.append(tree_bytes)
    
    return serialized_trees


def deserialize_random_forest(serialized_trees: List[bytes], 
                            n_classes: int = 2,
                            random_state: int = 42) -> RandomForestClassifier:
    """
    Deserialize a list of decision trees back into a Random Forest model.
    
    Args:
        serialized_trees: List of serialized decision trees as bytes
        n_classes: Number of classes for the classifier
        random_state: Random state for reproducibility
        
    Returns:
        RandomForestClassifier with deserialized trees
    """
    # Create a new Random Forest with the same number of estimators
    model = RandomForestClassifier(
        n_estimators=len(serialized_trees),
        random_state=random_state
    )
    
    # Deserialize each tree
    estimators = []
    for tree_bytes in serialized_trees:
        tree = pickle.loads(tree_bytes)
        estimators.append(tree)
    
    # Set the estimators
    model.estimators_ = estimators
    model.n_classes_ = n_classes
    model.classes_ = np.array([0, 1])  # Binary classification
    model.n_features_in_ = estimators[0].n_features_in_ if estimators else 0
    model.n_outputs_ = 1
    
    return model


def aggregate_random_forests(client_trees_list: List[List[bytes]], 
                           weights: List[float] = None) -> List[bytes]:
    """
    Aggregate Random Forest models from multiple clients by combining their trees.
    
    Args:
        client_trees_list: List of serialized trees from each client
        weights: Optional weights for each client (based on dataset size)
        
    Returns:
        List of serialized trees for the aggregated model
    """
    if not client_trees_list:
        return []
    
    # If no weights provided, use equal weights
    if weights is None:
        weights = [1.0] * len(client_trees_list)
    
    # Normalize weights
    total_weight = sum(weights)
    weights = [w / total_weight for w in weights]
    
    # Combine all trees from all clients
    all_trees = []
    for client_trees, weight in zip(client_trees_list, weights):
        # For simplicity, we'll include all trees from each client
        # In a more sophisticated approach, we might sample trees based on weights
        all_trees.extend(client_trees)
    
    return all_trees


def trees_to_numpy_arrays(serialized_trees: List[bytes]) -> np.ndarray:
    """
    Convert serialized trees to numpy arrays for Flower compatibility.

    Args:
        serialized_trees: List of serialized decision trees

    Returns:
        Numpy array containing the serialized trees as concatenated bytes
    """
    if not serialized_trees:
        return np.array([], dtype=np.uint8)

    # Concatenate all tree bytes with length prefixes
    result_bytes = b''
    for tree_bytes in serialized_trees:
        # Add length prefix (4 bytes) followed by tree data
        length = len(tree_bytes)
        result_bytes += length.to_bytes(4, byteorder='big') + tree_bytes

    # Convert to numpy array of uint8
    return np.frombuffer(result_bytes, dtype=np.uint8)


def numpy_arrays_to_trees(tree_array: np.ndarray) -> List[bytes]:
    """
    Convert numpy arrays back to serialized trees.

    Args:
        tree_array: Numpy array containing concatenated tree bytes

    Returns:
        List of serialized decision trees as bytes
    """
    if len(tree_array) == 0:
        return []

    # Convert back to bytes
    data_bytes = tree_array.tobytes()

    # Parse the concatenated data
    serialized_trees = []
    offset = 0

    while offset < len(data_bytes):
        if offset + 4 > len(data_bytes):
            break

        # Read length prefix (4 bytes)
        length = int.from_bytes(data_bytes[offset:offset+4], byteorder='big')
        offset += 4

        if offset + length > len(data_bytes):
            break

        # Read tree data
        tree_bytes = data_bytes[offset:offset+length]
        serialized_trees.append(tree_bytes)
        offset += length

    return serialized_trees


def get_model_parameters(model: RandomForestClassifier) -> np.ndarray:
    """
    Extract parameters from a Random Forest model for federated learning.

    Args:
        model: Trained RandomForestClassifier

    Returns:
        Numpy array containing serialized trees
    """
    # Serialize the trees
    serialized_trees = serialize_random_forest(model)

    # Convert to numpy array for Flower
    tree_array = trees_to_numpy_arrays(serialized_trees)

    return tree_array


def set_model_parameters(model: RandomForestClassifier,
                        tree_array: np.ndarray) -> RandomForestClassifier:
    """
    Set parameters for a Random Forest model from federated learning.

    Args:
        model: RandomForestClassifier to update
        tree_array: Numpy array containing serialized trees

    Returns:
        Updated RandomForestClassifier
    """
    # Convert numpy array back to serialized trees
    serialized_trees = numpy_arrays_to_trees(tree_array)

    # Deserialize the trees and update the model
    updated_model = deserialize_random_forest(
        serialized_trees,
        n_classes=2,
        random_state=model.random_state
    )

    return updated_model
