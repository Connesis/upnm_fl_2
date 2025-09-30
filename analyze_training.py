#!/usr/bin/env python3
"""
Training Analysis Script
Analyze federated learning training progression and model performance.
"""

import os
import sys
import glob
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score
import re
from datetime import datetime

def extract_round_info(filename):
    """Extract round number and timestamp from model filename."""
    # Pattern: federated_cvd_model_round_X_YYYYMMDD_HHMMSS.joblib
    pattern = r'federated_cvd_model_round_(\d+)_(\d{8})_(\d{6})\.joblib'
    match = re.search(pattern, filename)
    
    if match:
        round_num = int(match.group(1))
        date_str = match.group(2)
        time_str = match.group(3)
        
        # Parse timestamp
        timestamp_str = f"{date_str}_{time_str}"
        timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        
        return round_num, timestamp
    
    return None, None

def test_model_accuracy(model, test_data_path):
    """Test model accuracy on validation data."""
    try:
        # Auto-detect delimiter (could be ',' or ';')
        with open(test_data_path, 'r') as f:
            first_line = f.readline()
            delimiter = ';' if ';' in first_line else ','

        # Load test data
        test_data = pd.read_csv(test_data_path, sep=delimiter)

        # Prepare features and labels
        target_col = 'cardio' if 'cardio' in test_data.columns else 'target'
        X_test = test_data.drop([target_col], axis=1)
        y_test = test_data[target_col]

        # Make predictions
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        return accuracy

    except Exception as e:
        print(f"⚠️ Warning: Could not test model accuracy: {e}")
        return None

def analyze_training_progression(test_data_path=None):
    """Analyze how model performance improves across rounds."""
    print("📈 Analyzing Training Progression")
    print("=" * 50)
    
    # Find all model files
    model_files = glob.glob("models/federated_cvd_model_*.joblib")
    
    if not model_files:
        print("❌ No model files found in models/ directory")
        return
    
    rounds_data = []
    
    for model_file in model_files:
        try:
            round_num, timestamp = extract_round_info(os.path.basename(model_file))
            
            if round_num is None:
                print(f"⚠️ Could not parse round info from: {model_file}")
                continue
            
            # Load model
            model = joblib.load(model_file)
            
            # Get model properties
            n_estimators = getattr(model, 'n_estimators', 0)
            max_depth = getattr(model, 'max_depth', None)
            
            # Test accuracy if test data provided
            accuracy = None
            if test_data_path and os.path.exists(test_data_path):
                accuracy = test_model_accuracy(model, test_data_path)
            
            rounds_data.append({
                'round': round_num,
                'timestamp': timestamp,
                'model_file': model_file,
                'n_estimators': n_estimators,
                'max_depth': max_depth,
                'accuracy': accuracy,
                'file_size_mb': os.path.getsize(model_file) / (1024 * 1024)
            })
            
        except Exception as e:
            print(f"❌ Error processing {model_file}: {e}")
    
    if not rounds_data:
        print("❌ No valid model data found")
        return
    
    # Sort by round number
    rounds_data.sort(key=lambda x: x['round'])
    
    # Create DataFrame
    df = pd.DataFrame(rounds_data)
    
    # Display summary
    print(f"📊 Found {len(df)} training rounds")
    print("\n📋 Training Round Summary:")
    print("-" * 80)
    print(f"{'Round':<6} {'Trees':<8} {'Depth':<8} {'Size(MB)':<10} {'Accuracy':<10} {'Timestamp'}")
    print("-" * 80)
    
    for _, row in df.iterrows():
        accuracy_str = f"{row['accuracy']:.4f}" if row['accuracy'] is not None else "N/A"
        depth_str = str(row['max_depth']) if row['max_depth'] is not None else "N/A"
        timestamp_str = row['timestamp'].strftime("%Y-%m-%d %H:%M") if row['timestamp'] else "N/A"
        
        print(f"{row['round']:<6} {row['n_estimators']:<8} {depth_str:<8} {row['file_size_mb']:<10.1f} {accuracy_str:<10} {timestamp_str}")
    
    # Create visualizations
    create_training_plots(df)
    
    # Analysis insights
    print_training_insights(df)

def create_training_plots(df):
    """Create training progression plots."""
    try:
        os.makedirs('plots', exist_ok=True)
        
        # Set style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Federated Learning Training Analysis', fontsize=16, fontweight='bold')
        
        # Plot 1: Model Size Progression
        axes[0, 0].plot(df['round'], df['file_size_mb'], marker='o', linewidth=2, markersize=8)
        axes[0, 0].set_title('Model Size Progression')
        axes[0, 0].set_xlabel('Training Round')
        axes[0, 0].set_ylabel('Model Size (MB)')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: Number of Trees Progression
        axes[0, 1].plot(df['round'], df['n_estimators'], marker='s', linewidth=2, markersize=8, color='orange')
        axes[0, 1].set_title('Number of Trees Progression')
        axes[0, 1].set_xlabel('Training Round')
        axes[0, 1].set_ylabel('Number of Trees')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Plot 3: Accuracy Progression (if available)
        if df['accuracy'].notna().any():
            valid_accuracy = df.dropna(subset=['accuracy'])
            axes[1, 0].plot(valid_accuracy['round'], valid_accuracy['accuracy'], 
                           marker='D', linewidth=2, markersize=8, color='green')
            axes[1, 0].set_title('Model Accuracy Progression')
            axes[1, 0].set_xlabel('Training Round')
            axes[1, 0].set_ylabel('Accuracy')
            axes[1, 0].grid(True, alpha=0.3)
            axes[1, 0].set_ylim(0, 1)
        else:
            axes[1, 0].text(0.5, 0.5, 'No accuracy data available\n(provide test dataset)', 
                           ha='center', va='center', transform=axes[1, 0].transAxes)
            axes[1, 0].set_title('Model Accuracy Progression')
        
        # Plot 4: Training Timeline
        if df['timestamp'].notna().any():
            valid_timestamps = df.dropna(subset=['timestamp'])
            axes[1, 1].plot(valid_timestamps['timestamp'], valid_timestamps['round'], 
                           marker='o', linewidth=2, markersize=8, color='purple')
            axes[1, 1].set_title('Training Timeline')
            axes[1, 1].set_xlabel('Timestamp')
            axes[1, 1].set_ylabel('Training Round')
            axes[1, 1].grid(True, alpha=0.3)
            
            # Rotate x-axis labels
            plt.setp(axes[1, 1].xaxis.get_majorticklabels(), rotation=45)
        else:
            axes[1, 1].text(0.5, 0.5, 'No timestamp data available', 
                           ha='center', va='center', transform=axes[1, 1].transAxes)
            axes[1, 1].set_title('Training Timeline')
        
        plt.tight_layout()
        plt.savefig('plots/training_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Create individual accuracy plot if data available
        if df['accuracy'].notna().any():
            plt.figure(figsize=(10, 6))
            valid_accuracy = df.dropna(subset=['accuracy'])
            plt.plot(valid_accuracy['round'], valid_accuracy['accuracy'], 
                    marker='o', linewidth=3, markersize=10, color='darkgreen')
            plt.title('Federated Learning Model Performance Progression', fontsize=14, fontweight='bold')
            plt.xlabel('Training Round', fontsize=12)
            plt.ylabel('Accuracy', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.ylim(0, 1)
            
            # Add value labels on points
            for _, row in valid_accuracy.iterrows():
                plt.annotate(f'{row["accuracy"]:.3f}', 
                           (row['round'], row['accuracy']),
                           textcoords="offset points", xytext=(0,10), ha='center')
            
            plt.savefig('plots/accuracy_progression.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        print("📈 Training analysis plots saved to plots/ directory")
        
    except Exception as e:
        print(f"⚠️ Warning: Could not create plots: {e}")

def print_training_insights(df):
    """Print insights about the training progression."""
    print("\n🔍 Training Insights:")
    print("-" * 30)
    
    # Model size growth
    if len(df) > 1:
        size_growth = df['file_size_mb'].iloc[-1] - df['file_size_mb'].iloc[0]
        print(f"📈 Model size growth: {size_growth:.1f} MB ({df['file_size_mb'].iloc[0]:.1f} → {df['file_size_mb'].iloc[-1]:.1f} MB)")
    
    # Trees growth
    if len(df) > 1:
        trees_growth = df['n_estimators'].iloc[-1] - df['n_estimators'].iloc[0]
        print(f"🌳 Trees added: {trees_growth} ({df['n_estimators'].iloc[0]} → {df['n_estimators'].iloc[-1]})")
    
    # Accuracy improvement
    if df['accuracy'].notna().any():
        valid_accuracy = df.dropna(subset=['accuracy'])
        if len(valid_accuracy) > 1:
            accuracy_improvement = valid_accuracy['accuracy'].iloc[-1] - valid_accuracy['accuracy'].iloc[0]
            print(f"🎯 Accuracy change: {accuracy_improvement:+.4f} ({valid_accuracy['accuracy'].iloc[0]:.4f} → {valid_accuracy['accuracy'].iloc[-1]:.4f})")
        
        best_round = valid_accuracy.loc[valid_accuracy['accuracy'].idxmax()]
        print(f"🏆 Best performing round: {best_round['round']} (accuracy: {best_round['accuracy']:.4f})")
    
    # Training duration
    if df['timestamp'].notna().any():
        valid_timestamps = df.dropna(subset=['timestamp'])
        if len(valid_timestamps) > 1:
            duration = valid_timestamps['timestamp'].iloc[-1] - valid_timestamps['timestamp'].iloc[0]
            print(f"⏱️ Training duration: {duration}")

def main():
    """Main function."""
    print("📊 Federated Learning Training Analysis")
    print("=" * 60)
    
    # Check for test data
    test_data_path = None
    possible_test_paths = [
        "dataset/test_data.csv",
        "dataset/validation_data.csv",
        "dataset/clients/test_data.csv"
    ]
    
    for path in possible_test_paths:
        if os.path.exists(path):
            test_data_path = path
            break
    
    if test_data_path:
        print(f"✅ Using test data: {test_data_path}")
    else:
        print("⚠️ No test data found - accuracy analysis will be skipped")
        print("   Place test data at: dataset/test_data.csv")
    
    print()
    
    # Run analysis
    analyze_training_progression(test_data_path)
    
    print(f"\n🎉 Analysis completed!")
    print(f"📈 Check plots/ directory for visualizations")

if __name__ == "__main__":
    main()
