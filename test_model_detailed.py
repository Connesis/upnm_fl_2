#!/usr/bin/env python3
"""
Detailed Model Testing Script
Test federated learning models with sample-by-sample prediction comparison.
"""

import sys
import os
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    precision_recall_fscore_support, roc_auc_score
)
import matplotlib.pyplot as plt
import seaborn as sns


def load_test_data(test_data_path):
    """Load and prepare test data."""
    try:
        # Auto-detect delimiter (could be ',' or ';')
        with open(test_data_path, 'r') as f:
            first_line = f.readline()
            delimiter = ';' if ';' in first_line else ','

        test_data = pd.read_csv(test_data_path, sep=delimiter)
        print(f"✅ Loaded test data: {test_data_path}")
        print(f"   Shape: {test_data.shape}")

        # Check if target column exists (cardio or target)
        target_col = 'cardio' if 'cardio' in test_data.columns else 'target'

        if target_col not in test_data.columns:
            print("❌ Error: 'cardio' or 'target' column not found in test data")
            print(f"   Available columns: {list(test_data.columns)}")
            return None, None, None

        # Keep the original dataframe for detailed output
        X_test = test_data.drop([target_col], axis=1)
        y_test = test_data[target_col]

        print(f"   Features: {X_test.shape[1]}")
        print(f"   Samples: {len(y_test)}")
        print(f"   Class distribution: {dict(y_test.value_counts().sort_index())}")

        return X_test, y_test, test_data

    except Exception as e:
        print(f"❌ Error loading test data: {e}")
        return None, None, None


def print_sample_predictions(y_test, y_pred, y_pred_proba=None, num_samples=20):
    """Print detailed sample-by-sample predictions."""
    print(f"\n📋 Sample-by-Sample Predictions (First {num_samples} samples):")
    print("=" * 100)
    print(f"{'Sample':<8} {'Actual':<10} {'Predicted':<10} {'Result':<10} {'Confidence':<12}")
    print("-" * 100)

    correct_count = 0

    for i in range(min(num_samples, len(y_test))):
        actual = int(y_test.iloc[i])
        predicted = int(y_pred[i])
        is_correct = actual == predicted
        result = "✅ Correct" if is_correct else "❌ Wrong"

        if is_correct:
            correct_count += 1

        # Calculate confidence if probabilities available
        if y_pred_proba is not None:
            confidence = y_pred_proba[i][predicted] * 100
            confidence_str = f"{confidence:.2f}%"
        else:
            confidence_str = "N/A"

        print(f"{i+1:<8} {actual:<10} {predicted:<10} {result:<10} {confidence_str:<12}")

    accuracy_in_sample = correct_count / min(num_samples, len(y_test)) * 100
    print("-" * 100)
    print(f"Sample Accuracy: {correct_count}/{min(num_samples, len(y_test))} = {accuracy_in_sample:.2f}%")
    print("=" * 100)


def print_error_analysis(y_test, y_pred, y_pred_proba=None, max_errors=10):
    """Print analysis of misclassified samples."""
    print(f"\n🔍 Error Analysis (Up to {max_errors} misclassified samples):")
    print("=" * 100)

    # Find misclassified samples
    errors = []
    for i in range(len(y_test)):
        if int(y_test.iloc[i]) != int(y_pred[i]):
            confidence = y_pred_proba[i][y_pred[i]] * 100 if y_pred_proba is not None else None
            errors.append({
                'index': i,
                'actual': int(y_test.iloc[i]),
                'predicted': int(y_pred[i]),
                'confidence': confidence
            })

    if not errors:
        print("🎉 No errors! Perfect predictions on all samples!")
        return

    print(f"Total misclassified: {len(errors)} out of {len(y_test)} ({len(errors)/len(y_test)*100:.2f}%)")
    print()
    print(f"{'Sample':<8} {'Actual':<10} {'Predicted':<10} {'Confidence':<12}")
    print("-" * 100)

    for error in errors[:max_errors]:
        conf_str = f"{error['confidence']:.2f}%" if error['confidence'] is not None else "N/A"
        print(f"{error['index']+1:<8} {error['actual']:<10} {error['predicted']:<10} {conf_str:<12}")

    if len(errors) > max_errors:
        print(f"... and {len(errors) - max_errors} more errors")

    print("=" * 100)


def print_class_wise_performance(y_test, y_pred):
    """Print performance metrics for each class."""
    print("\n📊 Class-wise Performance:")
    print("=" * 80)

    # Get unique classes
    classes = sorted(y_test.unique())

    print(f"{'Class':<10} {'Total':<10} {'Correct':<10} {'Wrong':<10} {'Accuracy':<10}")
    print("-" * 80)

    for cls in classes:
        # Get samples for this class
        class_mask = y_test == cls
        class_samples = y_test[class_mask]
        class_predictions = y_pred[class_mask]

        total = len(class_samples)
        correct = np.sum(class_samples == class_predictions)
        wrong = total - correct
        accuracy = correct / total * 100 if total > 0 else 0

        print(f"{cls:<10} {total:<10} {correct:<10} {wrong:<10} {accuracy:.2f}%")

    print("=" * 80)


def save_predictions_to_csv(y_test, y_pred, y_pred_proba, output_path="predictions_output.csv"):
    """Save all predictions to CSV file."""
    try:
        predictions_df = pd.DataFrame({
            'Sample_Index': range(1, len(y_test) + 1),
            'Actual_Label': y_test.values,
            'Predicted_Label': y_pred,
            'Is_Correct': y_test.values == y_pred,
        })

        # Add confidence if available
        if y_pred_proba is not None:
            predictions_df['Confidence'] = [y_pred_proba[i][y_pred[i]] for i in range(len(y_pred))]

            # Add probability for each class
            for cls in range(y_pred_proba.shape[1]):
                predictions_df[f'Prob_Class_{cls}'] = y_pred_proba[:, cls]

        predictions_df.to_csv(output_path, index=False)
        print(f"\n💾 Predictions saved to: {output_path}")
        return output_path

    except Exception as e:
        print(f"⚠️ Warning: Could not save predictions to CSV: {e}")
        return None


def test_model_detailed(model_path, test_data_path, num_samples=20, max_errors=10, save_csv=True):
    """Test a federated learning model with detailed output."""

    print(f"\n🧪 Testing Model: {os.path.basename(model_path)}")
    print("=" * 100)

    # Load model
    try:
        model = joblib.load(model_path)
        print(f"✅ Loaded model: {model_path}")

        # Get model info
        if hasattr(model, 'n_estimators'):
            print(f"   Trees: {model.n_estimators}")
        if hasattr(model, 'max_depth'):
            print(f"   Max depth: {model.max_depth}")

    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return None

    # Load test data
    X_test, y_test, test_data = load_test_data(test_data_path)
    if X_test is None:
        return None

    try:
        # Make predictions
        print("\n🔮 Making predictions...")
        y_pred = model.predict(X_test)

        # Get prediction probabilities if available
        y_pred_proba = None
        if hasattr(model, 'predict_proba'):
            y_pred_proba = model.predict_proba(X_test)

        # Print sample predictions
        print_sample_predictions(y_test, y_pred, y_pred_proba, num_samples)

        # Print error analysis
        print_error_analysis(y_test, y_pred, y_pred_proba, max_errors)

        # Print class-wise performance
        print_class_wise_performance(y_test, y_pred)

        # Calculate overall metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, support = precision_recall_fscore_support(y_test, y_pred, average='weighted')

        print(f"\n📊 Overall Test Results:")
        print("=" * 80)
        print(f"   Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
        print(f"   Precision: {precision:.4f}")
        print(f"   Recall:    {recall:.4f}")
        print(f"   F1-Score:  {f1:.4f}")
        print(f"   Test samples: {len(y_test)}")

        # ROC AUC for binary classification
        if len(np.unique(y_test)) == 2 and y_pred_proba is not None:
            auc = roc_auc_score(y_test, y_pred_proba[:, 1])
            print(f"   ROC AUC:   {auc:.4f}")

        print("=" * 80)

        # Detailed classification report
        print("\n📋 Detailed Classification Report:")
        print("=" * 80)
        print(classification_report(y_test, y_pred, digits=4))

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        print("🔢 Confusion Matrix:")
        print(cm)
        print("=" * 80)

        # Save predictions to CSV
        if save_csv:
            model_name = os.path.basename(model_path).replace('.joblib', '')
            csv_path = f"predictions_{model_name}.csv"
            save_predictions_to_csv(y_test, y_pred, y_pred_proba, csv_path)

        # Save plots
        save_evaluation_plots(y_test, y_pred, y_pred_proba, model_path)

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'confusion_matrix': cm,
            'model_path': model_path
        }

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return None


def save_evaluation_plots(y_test, y_pred, y_pred_proba, model_path):
    """Save evaluation plots."""
    try:
        model_name = os.path.basename(model_path).replace('.joblib', '')

        # Create plots directory
        os.makedirs('plots', exist_ok=True)

        # Confusion Matrix Plot
        plt.figure(figsize=(10, 8))
        cm = confusion_matrix(y_test, y_pred)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=True)
        plt.title(f'Confusion Matrix - {model_name}', fontsize=14, fontweight='bold')
        plt.ylabel('Actual Label', fontsize=12)
        plt.xlabel('Predicted Label', fontsize=12)
        plt.savefig(f'plots/confusion_matrix_{model_name}.png', dpi=300, bbox_inches='tight')
        plt.close()

        # Prediction distribution
        plt.figure(figsize=(10, 6))
        x = np.arange(len(np.unique(y_test)))
        width = 0.35

        actual_counts = [np.sum(y_test == cls) for cls in sorted(y_test.unique())]
        pred_counts = [np.sum(y_pred == cls) for cls in sorted(y_test.unique())]

        plt.bar(x - width/2, actual_counts, width, label='Actual', alpha=0.8)
        plt.bar(x + width/2, pred_counts, width, label='Predicted', alpha=0.8)
        plt.xlabel('Class', fontsize=12)
        plt.ylabel('Count', fontsize=12)
        plt.title(f'Prediction Distribution - {model_name}', fontsize=14, fontweight='bold')
        plt.xticks(x, sorted(y_test.unique()))
        plt.legend()
        plt.grid(True, alpha=0.3, axis='y')
        plt.savefig(f'plots/distribution_{model_name}.png', dpi=300, bbox_inches='tight')
        plt.close()

        # ROC Curve for binary classification
        if len(np.unique(y_test)) == 2 and y_pred_proba is not None:
            from sklearn.metrics import roc_curve

            fpr, tpr, _ = roc_curve(y_test, y_pred_proba[:, 1])
            auc = roc_auc_score(y_test, y_pred_proba[:, 1])

            plt.figure(figsize=(10, 8))
            plt.plot(fpr, tpr, linewidth=2, label=f'ROC Curve (AUC = {auc:.3f})')
            plt.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random Classifier')
            plt.xlim([0.0, 1.0])
            plt.ylim([0.0, 1.05])
            plt.xlabel('False Positive Rate', fontsize=12)
            plt.ylabel('True Positive Rate', fontsize=12)
            plt.title(f'ROC Curve - {model_name}', fontsize=14, fontweight='bold')
            plt.legend(loc="lower right")
            plt.grid(True, alpha=0.3)
            plt.savefig(f'plots/roc_curve_{model_name}.png', dpi=300, bbox_inches='tight')
            plt.close()

        print(f"\n📈 Visualization plots saved to plots/ directory")

    except Exception as e:
        print(f"⚠️ Warning: Could not save plots: {e}")


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Test federated learning model with detailed predictions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test a specific model
  python test_model_detailed.py models/federated_cvd_model_round_1_*.joblib dataset/test_data.csv

  # Test with custom number of sample predictions shown
  python test_model_detailed.py models/federated_cvd_model_round_2_*.joblib dataset/test_data.csv --samples 50

  # Test without saving CSV
  python test_model_detailed.py models/federated_cvd_model_round_1_*.joblib dataset/test_data.csv --no-csv
        """
    )

    parser.add_argument('model_path', help='Path to the model file (.joblib)')
    parser.add_argument('test_data_path', help='Path to the test data CSV file')
    parser.add_argument('--samples', type=int, default=20,
                       help='Number of sample predictions to display (default: 20)')
    parser.add_argument('--max-errors', type=int, default=10,
                       help='Maximum number of errors to display (default: 10)')
    parser.add_argument('--no-csv', action='store_true',
                       help='Do not save predictions to CSV file')

    args = parser.parse_args()

    # Check if files exist
    if not os.path.exists(args.model_path):
        print(f"❌ Model file not found: {args.model_path}")
        sys.exit(1)

    if not os.path.exists(args.test_data_path):
        print(f"❌ Test data file not found: {args.test_data_path}")
        sys.exit(1)

    # Test the model
    result = test_model_detailed(
        args.model_path,
        args.test_data_path,
        num_samples=args.samples,
        max_errors=args.max_errors,
        save_csv=not args.no_csv
    )

    if result:
        print(f"\n✅ Testing completed successfully!")
        print(f"📊 Final Accuracy: {result['accuracy']:.4f} ({result['accuracy']*100:.2f}%)")
        print(f"📈 Check plots/ directory for visualizations")
    else:
        print(f"\n❌ Testing failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()