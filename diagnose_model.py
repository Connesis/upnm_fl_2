#!/usr/bin/env python3
"""
Diagnostic script to investigate model performance issues.
"""

import pandas as pd
import numpy as np
import joblib
import os
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns


def analyze_data_distribution(data_path, data_name="Dataset"):
    """Analyze the distribution of a dataset."""
    print(f"\n{'='*80}")
    print(f"📊 Analyzing {data_name}: {data_path}")
    print(f"{'='*80}")

    try:
        # Auto-detect delimiter (could be ',' or ';')
        with open(data_path, 'r') as f:
            first_line = f.readline()
            delimiter = ';' if ';' in first_line else ','

        df = pd.read_csv(data_path, sep=delimiter)

        print(f"\n📏 Dataset Shape: {df.shape}")
        print(f"   Rows: {df.shape[0]}")
        print(f"   Columns: {df.shape[1]}")

        # Check for target column (cardio or target)
        target_col = 'cardio' if 'cardio' in df.columns else 'target'

        if target_col not in df.columns:
            print(f"❌ Error: 'cardio' or 'target' column not found!")
            print(f"   Available columns: {list(df.columns)}")
            return None

        # Class distribution
        print(f"\n🎯 Target Distribution (column: '{target_col}'):")
        target_counts = df[target_col].value_counts().sort_index()
        for cls, count in target_counts.items():
            percentage = count / len(df) * 100
            print(f"   Class {cls}: {count:>6} samples ({percentage:>5.2f}%)")

        # Check for imbalance
        class_ratio = target_counts.max() / target_counts.min()
        print(f"\n⚖️  Class Imbalance Ratio: {class_ratio:.2f}:1")
        if class_ratio > 3:
            print(f"   ⚠️  WARNING: Significant class imbalance detected!")

        # Check for missing values
        missing = df.isnull().sum()
        if missing.any():
            print(f"\n❓ Missing Values:")
            for col, count in missing[missing > 0].items():
                print(f"   {col}: {count} missing")
        else:
            print(f"\n✅ No missing values detected")

        # Basic statistics
        print(f"\n📈 Feature Statistics:")
        X = df.drop(target_col, axis=1)
        print(f"   Mean: {X.mean().mean():.4f}")
        print(f"   Std:  {X.std().mean():.4f}")
        print(f"   Min:  {X.min().min():.4f}")
        print(f"   Max:  {X.max().max():.4f}")

        return df

    except Exception as e:
        print(f"❌ Error analyzing data: {e}")
        return None


def compare_data_distributions(train_paths, test_path):
    """Compare distributions between training and test data."""
    print(f"\n{'='*80}")
    print("🔍 COMPARING TRAIN vs TEST DISTRIBUTIONS")
    print(f"{'='*80}")

    # Auto-detect delimiter for test data
    with open(test_path, 'r') as f:
        first_line = f.readline()
        delimiter = ';' if ';' in first_line else ','

    # Load test data
    test_df = pd.read_csv(test_path, sep=delimiter)
    target_col = 'cardio' if 'cardio' in test_df.columns else 'target'
    test_target_dist = test_df[target_col].value_counts(normalize=True).sort_index()

    print("\n📊 Class Distribution Comparison:")
    print(f"{'Dataset':<30} {'Class 0':<15} {'Class 1':<15}")
    print("-" * 60)

    # Test data
    print(f"{'Test Data':<30} {test_target_dist.get(0, 0)*100:>6.2f}% {test_target_dist.get(1, 0)*100:>12.2f}%")

    # Training data
    all_train = []
    for i, train_path in enumerate(train_paths, 1):
        if os.path.exists(train_path):
            # Auto-detect delimiter
            with open(train_path, 'r') as f:
                first_line = f.readline()
                train_delimiter = ';' if ';' in first_line else ','

            train_df = pd.read_csv(train_path, sep=train_delimiter)
            all_train.append(train_df)
            train_target_col = 'cardio' if 'cardio' in train_df.columns else 'target'
            train_target_dist = train_df[train_target_col].value_counts(normalize=True).sort_index()
            print(f"{f'Client {i} Train':<30} {train_target_dist.get(0, 0)*100:>6.2f}% {train_target_dist.get(1, 0)*100:>12.2f}%")

    # Combined training data
    if all_train:
        combined_train = pd.concat(all_train, ignore_index=True)
        combined_target_col = 'cardio' if 'cardio' in combined_train.columns else 'target'
        combined_dist = combined_train[combined_target_col].value_counts(normalize=True).sort_index()
        print("-" * 60)
        print(f"{'Combined Train':<30} {combined_dist.get(0, 0)*100:>6.2f}% {combined_dist.get(1, 0)*100:>12.2f}%")

        # Calculate distribution difference
        test_class1 = test_target_dist.get(1, 0)
        train_class1 = combined_dist.get(1, 0)
        diff = abs(test_class1 - train_class1) * 100

        print(f"\n⚠️  Distribution Difference: {diff:.2f}%")
        if diff > 10:
            print("   ⚠️  WARNING: Significant distribution mismatch between train and test!")


def analyze_model_predictions(model_path, test_data_path):
    """Detailed analysis of model predictions."""
    print(f"\n{'='*80}")
    print("🔬 ANALYZING MODEL PREDICTIONS")
    print(f"{'='*80}")

    # Auto-detect delimiter
    with open(test_data_path, 'r') as f:
        first_line = f.readline()
        delimiter = ';' if ';' in first_line else ','

    # Load model and data
    model = joblib.load(model_path)
    test_df = pd.read_csv(test_data_path, sep=delimiter)

    target_col = 'cardio' if 'cardio' in test_df.columns else 'target'
    X_test = test_df.drop(target_col, axis=1)
    y_test = test_df[target_col]

    # Make predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test) if hasattr(model, 'predict_proba') else None

    print(f"\n📊 Prediction Distribution:")
    pred_counts = pd.Series(y_pred).value_counts().sort_index()
    actual_counts = y_test.value_counts().sort_index()

    print(f"{'Class':<10} {'Actual':<15} {'Predicted':<15} {'Difference':<15}")
    print("-" * 55)
    for cls in sorted(y_test.unique()):
        actual = actual_counts.get(cls, 0)
        pred = pred_counts.get(cls, 0)
        diff = pred - actual
        print(f"{cls:<10} {actual:<15} {pred:<15} {diff:+<15}")

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    print(f"\n🔢 Confusion Matrix:")
    print(cm)

    # Check if model is biased towards one class
    print(f"\n🎯 Model Bias Analysis:")
    for cls in sorted(y_test.unique()):
        cls_pred_count = np.sum(y_pred == cls)
        cls_pred_pct = cls_pred_count / len(y_pred) * 100
        print(f"   Model predicts Class {cls}: {cls_pred_count}/{len(y_pred)} times ({cls_pred_pct:.2f}%)")

    # Confidence analysis
    if y_pred_proba is not None:
        print(f"\n🎲 Confidence Analysis:")
        for cls in sorted(y_test.unique()):
            cls_mask = y_pred == cls
            if cls_mask.any():
                cls_confidences = y_pred_proba[cls_mask, cls]
                print(f"   Class {cls} predictions:")
                print(f"      Mean confidence: {cls_confidences.mean():.4f}")
                print(f"      Min confidence:  {cls_confidences.min():.4f}")
                print(f"      Max confidence:  {cls_confidences.max():.4f}")


def check_model_info(model_path):
    """Check model configuration."""
    print(f"\n{'='*80}")
    print("🔧 MODEL CONFIGURATION")
    print(f"{'='*80}")

    model = joblib.load(model_path)

    print(f"\nModel Type: {type(model).__name__}")

    if hasattr(model, 'n_estimators'):
        print(f"Number of Trees: {model.n_estimators}")
        if model.n_estimators < 50:
            print(f"   ⚠️  WARNING: Too few trees! Recommend at least 100 trees.")

    if hasattr(model, 'max_depth'):
        print(f"Max Depth: {model.max_depth}")

    if hasattr(model, 'min_samples_split'):
        print(f"Min Samples Split: {model.min_samples_split}")

    if hasattr(model, 'class_weight'):
        print(f"Class Weight: {model.class_weight}")
        if model.class_weight is None:
            print(f"   ⚠️  WARNING: No class weighting! May struggle with imbalanced data.")


def generate_recommendations(test_data_path, model_path):
    """Generate recommendations based on analysis."""
    print(f"\n{'='*80}")
    print("💡 RECOMMENDATIONS")
    print(f"{'='*80}")

    # Auto-detect delimiter
    with open(test_data_path, 'r') as f:
        first_line = f.readline()
        delimiter = ';' if ';' in first_line else ','

    # Load data
    test_df = pd.read_csv(test_data_path, sep=delimiter)
    model = joblib.load(model_path)

    recommendations = []

    # Check class imbalance
    target_col = 'cardio' if 'cardio' in test_df.columns else 'target'
    target_counts = test_df[target_col].value_counts()
    class_ratio = target_counts.max() / target_counts.min()
    if class_ratio > 2:
        recommendations.append(
            "1. ADDRESS CLASS IMBALANCE:\n"
            "   - Use class_weight='balanced' in Random Forest\n"
            "   - Apply SMOTE or other resampling techniques\n"
            "   - Adjust evaluation metrics (use F1, AUC instead of accuracy)"
        )

    # Check number of trees
    if hasattr(model, 'n_estimators') and model.n_estimators < 50:
        recommendations.append(
            "2. INCREASE MODEL COMPLEXITY:\n"
            "   - Use more trees: --trees 100 or higher\n"
            "   - Each client should contribute more trees (30 is minimum)"
        )

    # Check sample size
    if len(test_df) < 100:
        recommendations.append(
            "3. INCREASE TEST SAMPLE SIZE:\n"
            f"   - Current: {len(test_df)} samples (very small!)\n"
            "   - Recommend at least 1000+ samples for reliable evaluation\n"
            "   - Small test sets lead to unstable metrics"
        )

    # Check data preprocessing
    recommendations.append(
        "4. VERIFY DATA PREPROCESSING:\n"
        "   - Ensure train and test data use same preprocessing\n"
        "   - Check for feature scaling/normalization\n"
        "   - Verify no data leakage between train/test"
    )

    # Training recommendations
    recommendations.append(
        "5. IMPROVE TRAINING PROCESS:\n"
        "   - Increase training rounds (currently 2, try 5-10)\n"
        "   - Add more clients if possible (diversifies data)\n"
        "   - Monitor training metrics on each round"
    )

    # Print recommendations
    for rec in recommendations:
        print(f"\n{rec}")


def main():
    """Main diagnostic function."""
    print("\n" + "="*80)
    print("🔬 FEDERATED LEARNING MODEL DIAGNOSTICS")
    print("="*80)

    # Define paths
    test_data_path = "dataset/test_data.csv"
    train_data_paths = [
        "dataset/clients/client1_data.csv",
        "dataset/clients/client2_data.csv",
        "dataset/clients/client3_data.csv"
    ]

    # Find latest model
    import glob
    model_files = glob.glob("models/federated_cvd_model_round_*.joblib")
    if not model_files:
        print("❌ No model files found!")
        return

    model_path = sorted(model_files)[-1]  # Get latest model
    print(f"\n📦 Using Model: {model_path}")

    # Run diagnostics
    check_model_info(model_path)

    analyze_data_distribution(test_data_path, "Test Data")

    for i, train_path in enumerate(train_data_paths, 1):
        if os.path.exists(train_path):
            analyze_data_distribution(train_path, f"Client {i} Training Data")

    compare_data_distributions(train_data_paths, test_data_path)

    analyze_model_predictions(model_path, test_data_path)

    generate_recommendations(test_data_path, model_path)

    print(f"\n{'='*80}")
    print("✅ DIAGNOSTIC COMPLETE")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()