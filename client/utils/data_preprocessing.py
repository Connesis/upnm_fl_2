"""
Data preprocessing utilities for the federated learning system.
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder, OrdinalEncoder
from typing import Tuple


def preprocess_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Preprocess the cardiovascular dataset according to specifications.

    Args:
        df: Input dataframe with cardiovascular data

    Returns:
        Tuple of (features DataFrame, target Series)
    """
    # Convert age from days to years
    df = df.copy()
    df['age_years'] = df['age'] // 365

    # Select features
    feature_columns = ['age_years', 'height', 'weight', 'ap_hi', 'ap_lo',
                      'gender', 'cholesterol', 'gluc', 'smoke', 'alco', 'active']
    X = df[feature_columns].copy()  # Create explicit copy to avoid warning
    y = df['cardio']

    # Standardize numerical features
    numerical_features = ['age_years', 'height', 'weight', 'ap_hi', 'ap_lo']
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X[numerical_features])
    X[numerical_features] = X_scaled

    # One-hot encode gender
    X = pd.get_dummies(X, columns=['gender'], prefix='gender')

    # Ordinal encode cholesterol and glucose
    ordinal_features = ['cholesterol', 'gluc']
    ordinal_encoder = OrdinalEncoder()
    X_encoded = ordinal_encoder.fit_transform(X[ordinal_features])
    X[ordinal_features] = X_encoded

    # Ensure binary features are 0/1 (they should already be)
    binary_features = ['smoke', 'alco', 'active']
    for feature in binary_features:
        X[feature] = X[feature].astype(int)

    return X, y


def load_and_preprocess_data(file_path: str) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load data from CSV and preprocess it.

    Args:
        file_path: Path to the CSV file

    Returns:
        Tuple of (features DataFrame, target Series)
    """
    # Try to detect delimiter by reading first line
    with open(file_path, 'r') as f:
        first_line = f.readline()

    # Determine delimiter based on which one appears more frequently
    if first_line.count(';') > first_line.count(','):
        delimiter = ';'
    else:
        delimiter = ','

    # Load data with detected delimiter
    df = pd.read_csv(file_path, delimiter=delimiter)

    # Preprocess data
    return preprocess_data(df)