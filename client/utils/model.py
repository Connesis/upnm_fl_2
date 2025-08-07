"""
Random Forest model implementation for cardiovascular disease prediction.
"""
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from typing import Tuple, Dict, Any
import pandas as pd
from .federated_utils import get_model_parameters, set_model_parameters


class CVDModel:
    """Random Forest model for cardiovascular disease prediction."""
    
    def __init__(self,
                 n_estimators: int = 100,  # Number of trees per client (configurable)
                 max_depth: int = 10,
                 min_samples_leaf: int = 5,
                 random_state: int = 42):
        """
        Initialize the Random Forest model with specified hyperparameters.
        
        Args:
            n_estimators: Number of trees in the forest
            max_depth: Maximum depth of the tree
            min_samples_leaf: Minimum number of samples required to be at a leaf node
            random_state: Random state for reproducibility
        """
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_leaf=min_samples_leaf,
            random_state=random_state
        )
        
    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        """
        Train the Random Forest model.
        
        Args:
            X: Features DataFrame
            y: Target Series
        """
        self.model.fit(X, y)
        
    def predict(self, X: pd.DataFrame) -> pd.Series:
        """
        Make predictions using the trained model.
        
        Args:
            X: Features DataFrame
            
        Returns:
            Predictions Series
        """
        return self.model.predict(X)
        
    def predict_proba(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Predict class probabilities.
        
        Args:
            X: Features DataFrame
            
        Returns:
            Probabilities DataFrame
        """
        return self.model.predict_proba(X)
        
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """
        Evaluate the model performance.

        Args:
            X: Features DataFrame
            y: Target Series

        Returns:
            Dictionary with evaluation metrics
        """
        y_pred = self.predict(X)
        accuracy = accuracy_score(y, y_pred)

        # Get classification report as string for logging
        report_str = classification_report(y, y_pred)
        print(f"Classification Report:\n{report_str}")

        return {
            'accuracy': float(accuracy)
        }
        
    def save_model(self, file_path: str) -> None:
        """
        Save the trained model to a file.
        
        Args:
            file_path: Path to save the model
        """
        joblib.dump(self.model, file_path)
        
    @classmethod
    def load_model(cls, file_path: str) -> 'CVDModel':
        """
        Load a trained model from a file.

        Args:
            file_path: Path to the saved model

        Returns:
            CVDModel instance with loaded model
        """
        instance = cls()
        instance.model = joblib.load(file_path)
        return instance

    def get_federated_parameters(self) -> np.ndarray:
        """
        Get model parameters for federated learning.

        Returns:
            Numpy array containing model parameters
        """
        if not hasattr(self.model, 'estimators_'):
            # Model not trained yet, return empty parameters
            return np.array([], dtype=np.uint8)

        return get_model_parameters(self.model)

    def set_federated_parameters(self, parameters_array: np.ndarray) -> None:
        """
        Set model parameters from federated learning.

        Args:
            parameters_array: Numpy array containing model parameters
        """
        if len(parameters_array) > 0:
            self.model = set_model_parameters(self.model, parameters_array)

    def is_trained(self) -> bool:
        """
        Check if the model has been trained.

        Returns:
            True if model is trained, False otherwise
        """
        return hasattr(self.model, 'estimators_') and len(self.model.estimators_) > 0