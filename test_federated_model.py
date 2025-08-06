"""
Test script to verify the federated learning model works correctly.
"""
import joblib
import pandas as pd
import numpy as np
from client.utils.data_preprocessing import load_and_preprocess_data
from sklearn.metrics import accuracy_score, classification_report
import os
import glob


def test_federated_model():
    """Test the latest federated model."""
    print("Testing Federated Learning Model")
    print("=" * 50)
    
    # Find the latest model file
    model_files = glob.glob("models/federated_cvd_model_round_*.joblib")
    if not model_files:
        print("No federated models found!")
        return
    
    # Get the latest model (by filename timestamp)
    latest_model_file = sorted(model_files)[-1]
    print(f"Loading model: {latest_model_file}")
    
    # Load the federated model
    federated_model = joblib.load(latest_model_file)
    print(f"Model loaded successfully!")
    print(f"Number of estimators (trees): {federated_model.n_estimators}")
    print(f"Number of classes: {federated_model.n_classes_}")
    print(f"Feature names in: {getattr(federated_model, 'n_features_in_', 'Not available')}")
    
    # Load test data (using the main dataset)
    print("\nLoading test data...")
    X_test, y_test = load_and_preprocess_data("dataset/cardio_train.csv")
    
    # Use a subset for testing
    X_test_subset = X_test.head(1000)
    y_test_subset = y_test.head(1000)
    
    print(f"Test data shape: {X_test_subset.shape}")
    print(f"Test target distribution:\n{y_test_subset.value_counts()}")
    
    # Make predictions
    print("\nMaking predictions...")
    y_pred = federated_model.predict(X_test_subset)
    y_pred_proba = federated_model.predict_proba(X_test_subset)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test_subset, y_pred)
    print(f"\nFederated Model Performance:")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Prediction probabilities shape: {y_pred_proba.shape}")
    
    # Show classification report
    print("\nClassification Report:")
    print(classification_report(y_test_subset, y_pred))
    
    # Show some sample predictions
    print("\nSample Predictions (first 10):")
    print("Actual | Predicted | Probability")
    print("-" * 35)
    for i in range(10):
        actual = y_test_subset.iloc[i]
        predicted = y_pred[i]
        prob = y_pred_proba[i][1]  # Probability of class 1
        print(f"  {actual}    |     {predicted}     |   {prob:.4f}")
    
    # Load and compare with metadata
    metadata_files = glob.glob("models/federated_cvd_metadata_round_*.joblib")
    if metadata_files:
        latest_metadata_file = sorted(metadata_files)[-1]
        metadata = joblib.load(latest_metadata_file)
        print(f"\nModel Metadata:")
        print(f"Total training examples: {metadata.get('total_examples', 'N/A')}")
        print(f"Number of participating clients: {metadata.get('num_clients', 'N/A')}")
        print(f"Trees per client: {metadata.get('n_estimators', 'N/A') // metadata.get('num_clients', 1) if metadata.get('num_clients') else 'N/A'}")
    
    print("\n" + "=" * 50)
    print("Federated model test completed successfully!")


if __name__ == "__main__":
    test_federated_model()
