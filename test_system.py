"""
Test script for the federated learning system.
"""
import pandas as pd
import os
import sys
from client.utils.data_preprocessing import load_and_preprocess_data
from client.utils.model import CVDModel


def test_data_preprocessing():
    """Test data preprocessing functionality."""
    print("Testing data preprocessing...")
    
    # Check if dataset exists
    dataset_path = "dataset/cardio_train.csv"
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}")
        return False
        
    # Load and preprocess data
    try:
        X, y = load_and_preprocess_data(dataset_path)
        print(f"Data preprocessing successful. Shape: {X.shape}")
        print(f"Features: {list(X.columns)}")
        print(f"Target distribution:\n{y.value_counts()}")
        return True
    except Exception as e:
        print(f"Error in data preprocessing: {e}")
        return False


def test_model_training():
    """Test model training functionality."""
    print("\nTesting model training...")
    
    # Load and preprocess data
    dataset_path = "dataset/cardio_train.csv"
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}")
        return False
        
    try:
        X, y = load_and_preprocess_data(dataset_path)
        
        # Use only a subset for testing
        X_test = X.head(1000)
        y_test = y.head(1000)
        
        # Initialize and train model
        model = CVDModel()
        model.train(X_test, y_test)
        
        # Evaluate model
        metrics = model.evaluate(X_test, y_test)
        print(f"Model training successful. Accuracy: {metrics['accuracy']:.4f}")
        
        # Test prediction
        predictions = model.predict(X_test.head(5))
        print(f"Sample predictions: {predictions}")
        
        # Test probability prediction
        probabilities = model.predict_proba(X_test.head(5))
        print(f"Sample probabilities shape: {probabilities.shape}")
        
        return True
    except Exception as e:
        print(f"Error in model training: {e}")
        return False


def main():
    """Run all tests."""
    print("Running tests for federated learning system...\n")
    
    success = True
    
    # Test data preprocessing
    if not test_data_preprocessing():
        success = False
    
    # Test model training
    if not test_model_training():
        success = False
    
    if success:
        print("\nAll tests passed!")
        return 0
    else:
        print("\nSome tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())