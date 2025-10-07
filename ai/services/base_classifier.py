"""
Base Classifier Service
=======================

Abstract base class for all ML classifiers in the AI hub.
Provides common interface for training, prediction, model management.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, 
    f1_score, confusion_matrix, classification_report
)
from django.core.files.base import ContentFile
from django.conf import settings
import os
import json


class BaseClassifier(ABC):
    """
    Abstract base class for all ML classifiers.
    
    Subclasses must implement:
    - extract_features(): Feature extraction logic
    
    Provides:
    - train(): Training with metrics calculation
    - predict(): Single prediction
    - predict_batch(): Batch predictions
    - save_model(): Save to database
    - load_model(): Load from database
    - evaluate(): Model evaluation
    """
    
    def __init__(self, model_name: str):
        """
        Initialize classifier with model name.
        
        Args:
            model_name: Unique identifier for this model
        """
        self.model_name = model_name
        self.model = None
        self.vectorizer = None
        self.feature_config = {}
        self.classes_ = None
        
    @abstractmethod
    def extract_features(self, data: Any) -> np.ndarray:
        """
        Extract features from raw data.
        Must be implemented by subclass.
        
        Args:
            data: Raw input data (text, dict, object, etc.)
            
        Returns:
            Feature vector as numpy array
        """
        pass
    
    def train(
        self, 
        training_data: List[Any], 
        labels: List[str],
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """
        Train the model with provided data.
        
        Args:
            training_data: List of raw training samples
            labels: List of corresponding labels
            test_size: Proportion for test set (default 0.2)
            random_state: Random seed for reproducibility
            
        Returns:
            Dictionary with training metrics
        """
        if not self.model:
            raise ValueError("Model not initialized. Set self.model in subclass.")
        
        # Extract features
        print(f"Extracting features for {len(training_data)} samples...")
        X = np.array([self.extract_features(sample) for sample in training_data])
        y = np.array(labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        # Train model
        print(f"Training {self.model.__class__.__name__}...")
        self.model.fit(X_train, y_train)
        self.classes_ = self.model.classes_
        
        # Evaluate on test set
        y_pred = self.model.predict(X_test)
        
        # Calculate metrics
        metrics = {
            'accuracy': float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
            'recall': float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
            'f1_score': float(f1_score(y_test, y_pred, average='weighted', zero_division=0)),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
            'classification_report': classification_report(y_test, y_pred, output_dict=True),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'classes': self.classes_.tolist() if hasattr(self.classes_, 'tolist') else list(self.classes_),
        }
        
        print(f"Training complete! Accuracy: {metrics['accuracy']:.2%}")
        return metrics
    
    def predict(
        self, 
        data: Any, 
        return_probabilities: bool = False
    ) -> Tuple[str, Optional[Dict[str, float]]]:
        """
        Make prediction on single sample.
        
        Args:
            data: Raw input data
            return_probabilities: If True, return class probabilities
            
        Returns:
            Tuple of (predicted_label, probabilities_dict or None)
        """
        if not self.model:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        # Extract features
        features = self.extract_features(data)
        features = features.reshape(1, -1)  # Reshape for single sample
        
        # Predict
        prediction = self.model.predict(features)[0]
        
        # Get probabilities if requested
        probabilities = None
        if return_probabilities and hasattr(self.model, 'predict_proba'):
            proba = self.model.predict_proba(features)[0]
            probabilities = {
                class_: float(prob) 
                for class_, prob in zip(self.classes_, proba)
            }
        
        return prediction, probabilities
    
    def predict_batch(
        self, 
        data_list: List[Any],
        return_probabilities: bool = False
    ) -> List[Tuple[str, Optional[Dict[str, float]]]]:
        """
        Predict multiple samples at once (more efficient).
        
        Args:
            data_list: List of raw input data
            return_probabilities: If True, return class probabilities
            
        Returns:
            List of (predicted_label, probabilities_dict or None) tuples
        """
        if not self.model:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        # Extract features for all samples
        features = np.array([self.extract_features(data) for data in data_list])
        
        # Predict
        predictions = self.model.predict(features)
        
        # Get probabilities if requested
        results = []
        if return_probabilities and hasattr(self.model, 'predict_proba'):
            probabilities = self.model.predict_proba(features)
            for pred, proba in zip(predictions, probabilities):
                proba_dict = {
                    class_: float(prob) 
                    for class_, prob in zip(self.classes_, proba)
                }
                results.append((pred, proba_dict))
        else:
            results = [(pred, None) for pred in predictions]
        
        return results
    
    def save_model(
        self, 
        version: str,
        description: str = '',
        user=None
    ) -> 'MLModel':
        """
        Save trained model to database.
        
        Args:
            version: Semantic version string (e.g., '1.0.0')
            description: Model description/notes
            user: User who created this model version
            
        Returns:
            MLModel instance
        """
        from ai.models import MLModel
        
        if not self.model:
            raise ValueError("No model to save. Train model first.")
        
        # Serialize model
        model_bytes = joblib.dumps(self.model)
        model_file = ContentFile(model_bytes, name=f'{self.model_name}_v{version}.pkl')
        
        # Serialize vectorizer if exists
        vectorizer_file = None
        if self.vectorizer:
            vectorizer_bytes = joblib.dumps(self.vectorizer)
            vectorizer_file = ContentFile(
                vectorizer_bytes, 
                name=f'{self.model_name}_vectorizer_v{version}.pkl'
            )
        
        # Get performance metrics (if available from last training)
        # This should be called after train() to have metrics available
        metrics = getattr(self, '_last_metrics', {})
        
        # Create MLModel instance
        ml_model = MLModel.objects.create(
            model_name=self.model_name,
            model_version=version,
            model_type='classification',  # Can be overridden in subclass
            model_file=model_file,
            vectorizer_file=vectorizer_file,
            feature_config=self.feature_config,
            performance_metrics=metrics,
            training_samples_count=metrics.get('train_samples', 0) + metrics.get('test_samples', 0),
            description=description,
            created_by=user,
            is_active=False  # Manually activate later
        )
        
        print(f"Model saved: {ml_model}")
        return ml_model
    
    def load_model(self, version: Optional[str] = None) -> bool:
        """
        Load model from database.
        
        Args:
            version: Specific version to load, or None for active version
            
        Returns:
            True if loaded successfully
        """
        from ai.models import MLModel
        
        try:
            if version:
                ml_model = MLModel.objects.get(
                    model_name=self.model_name,
                    model_version=version
                )
            else:
                ml_model = MLModel.objects.get(
                    model_name=self.model_name,
                    is_active=True
                )
            
            # Load model
            self.model = joblib.loads(ml_model.model_file.read())
            
            # Load vectorizer if exists
            if ml_model.vectorizer_file:
                self.vectorizer = joblib.loads(ml_model.vectorizer_file.read())
            
            # Load config and classes
            self.feature_config = ml_model.feature_config
            self.classes_ = self.model.classes_
            
            print(f"Loaded model: {ml_model}")
            return True
            
        except MLModel.DoesNotExist:
            print(f"Model not found: {self.model_name} (version: {version or 'active'})")
            return False
    
    def evaluate(
        self, 
        test_data: List[Any], 
        test_labels: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluate model performance on test data.
        
        Args:
            test_data: List of test samples
            test_labels: True labels
            
        Returns:
            Dictionary with evaluation metrics
        """
        if not self.model:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        # Extract features
        X_test = np.array([self.extract_features(sample) for sample in test_data])
        y_test = np.array(test_labels)
        
        # Predict
        y_pred = self.model.predict(X_test)
        
        # Calculate metrics
        metrics = {
            'accuracy': float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
            'recall': float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
            'f1_score': float(f1_score(y_test, y_pred, average='weighted', zero_division=0)),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
            'classification_report': classification_report(y_test, y_pred, output_dict=True),
            'test_samples': len(X_test),
        }
        
        return metrics
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """
        Get feature importance if model supports it.
        
        Returns:
            Dictionary of feature: importance or None
        """
        if not self.model:
            return None
        
        if hasattr(self.model, 'feature_importances_'):
            # Tree-based models
            importances = self.model.feature_importances_
            return {
                f'feature_{i}': float(imp) 
                for i, imp in enumerate(importances)
            }
        elif hasattr(self.model, 'coef_'):
            # Linear models
            coefficients = self.model.coef_[0] if len(self.model.coef_.shape) > 1 else self.model.coef_
            return {
                f'feature_{i}': float(coef) 
                for i, coef in enumerate(coefficients)
            }
        
        return None
