#!/usr/bin/env python3
"""
Model Testing Script
Test federated learning models and evaluate their performance.
"""

import sys
import os
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score
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
        print(f"   Columns: {test_data.columns}")

        # Check if target column exists (cardio or target)
        target_col = 'cardio' if 'cardio' in test_data.columns else 'target'

        if target_col not in test_data.columns:
            print("❌ Error: 'cardio' or 'target' column not found in test data")
            print(f"   Available columns: {list(test_data.columns)}")
            return None, None

        # Prepare features and labels
        X_test = test_data.drop([target_col], axis=1)
        y_test = test_data[target_col]
        
        print(f"   Features: {X_test.shape[1]}")
        print(f"   Samples: {len(y_test)}")
        print(f"   Classes: {sorted(y_test.unique())}")
        
        return X_test, y_test
        
    except Exception as e:
        print(f"❌ Error loading test data: {e}")
        return None, None

def test_model(model_path, test_data_path, save_plots=True):
    """Test a federated learning model."""
    
    print(f"🧪 Testing Model: {os.path.basename(model_path)}")
    print("=" * 60)
    
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
    X_test, y_test = load_test_data(test_data_path)
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
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, support = precision_recall_fscore_support(y_test, y_pred, average='weighted')
        
        print(f"\n📊 Test Results:")
        print(f"   Accuracy: {accuracy:.4f}")
        print(f"   Precision: {precision:.4f}")
        print(f"   Recall: {recall:.4f}")
        print(f"   F1-Score: {f1:.4f}")
        print(f"   Test samples: {len(y_test)}")
        
        # ROC AUC for binary classification
        if len(np.unique(y_test)) == 2 and y_pred_proba is not None:
            auc = roc_auc_score(y_test, y_pred_proba[:, 1])
            print(f"   ROC AUC: {auc:.4f}")
        
        # Detailed classification report
        print("\n📋 Classification Report:")
        print(classification_report(y_test, y_pred))
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        print("\n🔢 Confusion Matrix:")
        print(cm)
        
        # Save plots if requested
        if save_plots:
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
        return None

def save_evaluation_plots(y_test, y_pred, y_pred_proba, model_path):
    """Save evaluation plots."""
    try:
        model_name = os.path.basename(model_path).replace('.joblib', '')
        
        # Create plots directory
        os.makedirs('plots', exist_ok=True)
        
        # Confusion Matrix Plot
        plt.figure(figsize=(8, 6))
        cm = confusion_matrix(y_test, y_pred)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title(f'Confusion Matrix - {model_name}')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.savefig(f'plots/confusion_matrix_{model_name}.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # ROC Curve for binary classification
        if len(np.unique(y_test)) == 2 and y_pred_proba is not None:
            from sklearn.metrics import roc_curve
            
            fpr, tpr, _ = roc_curve(y_test, y_pred_proba[:, 1])
            auc = roc_auc_score(y_test, y_pred_proba[:, 1])
            
            plt.figure(figsize=(8, 6))
            plt.plot(fpr, tpr, linewidth=2, label=f'ROC Curve (AUC = {auc:.3f})')
            plt.plot([0, 1], [0, 1], 'k--', linewidth=1)
            plt.xlim([0.0, 1.0])
            plt.ylim([0.0, 1.05])
            plt.xlabel('False Positive Rate')
            plt.ylabel('True Positive Rate')
            plt.title(f'ROC Curve - {model_name}')
            plt.legend(loc="lower right")
            plt.grid(True, alpha=0.3)
            plt.savefig(f'plots/roc_curve_{model_name}.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        print(f"📈 Plots saved to plots/ directory")
        
    except Exception as e:
        print(f"⚠️ Warning: Could not save plots: {e}")

def compare_models(model_paths, test_data_path):
    """Compare multiple models."""
    print("🔄 Comparing Multiple Models")
    print("=" * 60)
    
    results = []
    
    for model_path in model_paths:
        if os.path.exists(model_path):
            result = test_model(model_path, test_data_path, save_plots=False)
            if result:
                results.append(result)
            print()
    
    if results:
        print("📊 Model Comparison Summary:")
        print("-" * 60)
        print(f"{'Model':<40} {'Accuracy':<10} {'F1-Score':<10}")
        print("-" * 60)
        
        for result in results:
            model_name = os.path.basename(result['model_path'])[:35]
            print(f"{model_name:<40} {result['accuracy']:<10.4f} {result['f1']:<10.4f}")
        
        # Find best model
        best_model = max(results, key=lambda x: x['accuracy'])
        print(f"\n🏆 Best Model: {os.path.basename(best_model['model_path'])}")
        print(f"   Accuracy: {best_model['accuracy']:.4f}")

def main():
    """Main function."""
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python test_model.py <model_path> <test_data_path>")
        print("  python test_model.py compare <test_data_path>  # Compare all models")
        print()
        print("Examples:")
        print("  python test_model.py models/federated_cvd_model_round_1_*.joblib dataset/test_data.csv")
        print("  python test_model.py compare dataset/test_data.csv")
        sys.exit(1)
    
    if sys.argv[1] == "compare":
        # Compare all models
        test_data_path = sys.argv[2]
        
        # Find all model files
        import glob
        model_files = glob.glob("models/federated_cvd_model_*.joblib")
        
        if not model_files:
            print("❌ No model files found in models/ directory")
            sys.exit(1)
        
        model_files.sort()
        compare_models(model_files, test_data_path)
        
    else:
        # Test single model
        model_path = sys.argv[1]
        test_data_path = sys.argv[2]
        
        if not os.path.exists(model_path):
            print(f"❌ Model file not found: {model_path}")
            sys.exit(1)
        
        if not os.path.exists(test_data_path):
            print(f"❌ Test data file not found: {test_data_path}")
            sys.exit(1)
        
        result = test_model(model_path, test_data_path)
        
        if result:
            print(f"\n🎉 Testing completed successfully!")
            print(f"📈 Check plots/ directory for visualizations")
        else:
            print(f"\n❌ Testing failed!")
            sys.exit(1)

if __name__ == "__main__":
    main()
