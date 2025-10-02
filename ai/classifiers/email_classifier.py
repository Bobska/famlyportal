"""
Daycare Invoice Email Classifier
=================================

Machine learning classifier for identifying daycare invoice emails
using TF-IDF text analysis and metadata features with Random Forest.
"""
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
from typing import Dict, List, Tuple, Any
import logging

from ai.services.base_classifier import BaseClassifier

logger = logging.getLogger(__name__)


class DaycareInvoiceClassifier(BaseClassifier):
    """
    Classifier for identifying daycare invoice emails.
    
    Uses combination of:
    - TF-IDF text features from subject and body
    - Metadata features (sender, attachments, keywords)
    - Random Forest classifier for robust predictions
    """
    
    def __init__(self):
        """Initialize the classifier with vectorizer and model."""
        super().__init__()
        
        # TF-IDF vectorizer for text features
        # Using 1-2 word phrases (unigrams and bigrams) captures patterns like "amount due"
        self.vectorizer = TfidfVectorizer(
            max_features=500,  # Top 500 most important features
            ngram_range=(1, 2),  # 1-word and 2-word phrases
            stop_words='english',  # Remove common English words
            min_df=2,  # Word must appear in at least 2 documents
            lowercase=True,
            strip_accents='unicode'
        )
        
        # StandardScaler for metadata features
        self.scaler = StandardScaler()
        
        # Random Forest Classifier
        # Random Forest is robust to overfitting and works well with mixed feature types
        self.model = RandomForestClassifier(
            n_estimators=100,  # Number of decision trees
            max_depth=10,  # Limit depth to prevent overfitting
            min_samples_split=5,  # Minimum samples to split a node
            min_samples_leaf=2,  # Minimum samples in leaf nodes
            random_state=42,  # For reproducibility
            class_weight='balanced'  # Handle imbalanced datasets
        )
        
        # Feature names for debugging and interpretation
        self.text_feature_names = []
        self.metadata_feature_names = [
            'sender_contains_daycare',
            'sender_is_edu',
            'subject_has_invoice_keywords',
            'subject_has_currency',
            'body_has_invoice_keywords',
            'body_has_currency',
            'body_has_daycare_keywords',
            'has_attachments',
            'has_pdf_attachments'
        ]
        
    def extract_features(self, email_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract features from email data.
        
        Args:
            email_data: Dict with keys:
                - subject: Email subject line
                - sender: Sender email address
                - body: Email body text
                - has_attachment: Boolean if email has attachments
                - has_pdf_attachment: Boolean if email has PDF attachments
                - date: Email date (optional)
        
        Returns:
            numpy array of combined text and metadata features
        """
        # Extract text features
        text = self._prepare_text(email_data)
        text_features = self.vectorizer.transform([text]).toarray()
        
        # Extract metadata features
        metadata_features = self._extract_metadata_features(email_data)
        
        # Combine features
        combined_features = np.hstack([text_features, metadata_features.reshape(1, -1)])
        
        return combined_features
    
    def _prepare_text(self, email_data: Dict[str, Any]) -> str:
        """
        Prepare text for TF-IDF vectorization.
        
        Combines subject and body, giving more weight to subject line.
        
        Args:
            email_data: Email data dictionary
            
        Returns:
            Combined text string for analysis
        """
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        
        # Give subject line more weight by repeating it
        # Subject lines often contain the most important classification keywords
        combined_text = f"{subject} {subject} {body}"
        
        return combined_text
    
    def _extract_metadata_features(self, email_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract binary metadata features from email.
        
        These features capture patterns that text analysis might miss:
        - Sender characteristics (domain, keywords)
        - Presence of financial keywords
        - Attachment information
        
        Args:
            email_data: Email data dictionary
            
        Returns:
            numpy array of binary features (1/0)
        """
        sender = email_data.get('sender', '').lower()
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        
        features = []
        
        # Sender Analysis Features
        # Does sender email contain daycare-related terms?
        daycare_sender_keywords = ['daycare', 'childcare', 'child care', 'childminding']
        sender_contains_daycare = any(kw in sender for kw in daycare_sender_keywords)
        features.append(1 if sender_contains_daycare else 0)
        
        # Is sender from educational domain?
        sender_is_edu = '.edu' in sender
        features.append(1 if sender_is_edu else 0)
        
        # Subject Line Analysis Features
        # Invoice-related keywords
        invoice_keywords = ['invoice', 'bill', 'billing', 'payment', 'statement', 'receipt']
        subject_has_invoice = any(kw in subject for kw in invoice_keywords)
        features.append(1 if subject_has_invoice else 0)
        
        # Currency symbols in subject
        currency_symbols = ['$', '£', '€', '¥']
        subject_has_currency = any(symbol in subject for symbol in currency_symbols)
        features.append(1 if subject_has_currency else 0)
        
        # Email Body Analysis Features
        # Invoice terminology
        body_invoice_terms = [
            'invoice', 'total', 'amount due', 'due date', 'due by',
            'payment due', 'balance due', 'please pay', 'remit payment'
        ]
        body_has_invoice = any(term in body for term in body_invoice_terms)
        features.append(1 if body_has_invoice else 0)
        
        # Currency symbols in body
        body_has_currency = any(symbol in body for symbol in currency_symbols)
        features.append(1 if body_has_currency else 0)
        
        # Daycare-specific terminology
        daycare_terms = [
            'tuition', 'weekly rate', 'daily rate', 'childcare',
            'daycare', 'enrollment', 'care services'
        ]
        body_has_daycare = any(term in body for term in daycare_terms)
        features.append(1 if body_has_daycare else 0)
        
        # Attachment Analysis Features
        has_attachments = email_data.get('has_attachment', False)
        features.append(1 if has_attachments else 0)
        
        # PDF attachments specifically (invoices often sent as PDFs)
        has_pdf = email_data.get('has_pdf_attachment', False)
        features.append(1 if has_pdf else 0)
        
        return np.array(features)
    
    def train(self, training_data: List[Dict[str, Any]], labels: List[str]) -> Dict[str, float]:
        """
        Train the classifier on labeled email data.
        
        Args:
            training_data: List of email data dictionaries
            labels: List of labels ('daycare_invoice' or 'not_invoice')
        
        Returns:
            Dictionary containing training metrics:
                - accuracy, precision, recall, f1_score
                - train_accuracy, test_accuracy (if enough samples for split)
        """
        logger.info(f"Training DaycareInvoiceClassifier with {len(training_data)} samples")
        
        if len(training_data) < 10:
            raise ValueError(f"Need at least 10 training samples, got {len(training_data)}")
        
        # Convert labels to binary (1 = daycare_invoice, 0 = not_invoice)
        binary_labels = np.array([1 if label == 'daycare_invoice' else 0 for label in labels])
        
        # Check for class imbalance
        positive_count = np.sum(binary_labels)
        negative_count = len(binary_labels) - positive_count
        logger.info(f"Class distribution - Positive: {positive_count}, Negative: {negative_count}")
        
        # Prepare text for TF-IDF
        texts = [self._prepare_text(email) for email in training_data]
        
        # Fit TF-IDF vectorizer
        text_features = self.vectorizer.fit_transform(texts).toarray()
        self.text_feature_names = self.vectorizer.get_feature_names_out().tolist()
        
        # Extract and scale metadata features
        metadata_features = np.array([
            self._extract_metadata_features(email) for email in training_data
        ])
        scaled_metadata = self.scaler.fit_transform(metadata_features)
        
        # Combine all features
        X = np.hstack([text_features, scaled_metadata])
        y = binary_labels
        
        # Split data if we have enough samples
        metrics = {}
        if len(training_data) >= 20:
            # Use 20% for testing
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Train model
            self.model.fit(X_train, y_train)
            
            # Calculate metrics
            train_predictions = self.model.predict(X_train)
            test_predictions = self.model.predict(X_test)
            
            metrics['train_accuracy'] = accuracy_score(y_train, train_predictions)
            metrics['test_accuracy'] = accuracy_score(y_test, test_predictions)
            metrics['accuracy'] = metrics['test_accuracy']
            metrics['precision'] = precision_score(y_test, test_predictions, zero_division=0)
            metrics['recall'] = recall_score(y_test, test_predictions, zero_division=0)
            metrics['f1_score'] = f1_score(y_test, test_predictions, zero_division=0)
            
            logger.info(f"Training complete - Test Accuracy: {metrics['accuracy']:.3f}")
        else:
            # Not enough data for split, train on all data
            self.model.fit(X, y)
            predictions = self.model.predict(X)
            
            metrics['accuracy'] = accuracy_score(y, predictions)
            metrics['precision'] = precision_score(y, predictions, zero_division=0)
            metrics['recall'] = recall_score(y, predictions, zero_division=0)
            metrics['f1_score'] = f1_score(y, predictions, zero_division=0)
            
            logger.info(f"Training complete - Accuracy: {metrics['accuracy']:.3f}")
        
        return metrics
    
    def predict(self, email_data: Dict[str, Any], return_probabilities: bool = True) -> Dict[str, Any]:
        """
        Predict if email is a daycare invoice.
        
        Args:
            email_data: Email data dictionary
            return_probabilities: If True, include probability scores
        
        Returns:
            Dictionary containing:
                - prediction: 'daycare_invoice' or 'not_invoice'
                - confidence: float between 0.0 and 1.0
                - probabilities: dict with class probabilities (if return_probabilities=True)
                - feature_importance: dict of most important features (optional)
        """
        # Extract features
        features = self.extract_features(email_data)
        
        # Make prediction
        prediction_binary = self.model.predict(features)[0]
        prediction_label = 'daycare_invoice' if prediction_binary == 1 else 'not_invoice'
        
        # Get probability scores
        probabilities = self.model.predict_proba(features)[0]
        confidence = float(probabilities[prediction_binary])
        
        result = {
            'prediction': prediction_label,
            'confidence': confidence
        }
        
        if return_probabilities:
            result['probabilities'] = {
                'not_invoice': float(probabilities[0]),
                'daycare_invoice': float(probabilities[1])
            }
        
        return result
    
    def get_feature_importance(self, top_n: int = 20) -> List[Tuple[str, float]]:
        """
        Get the most important features for classification.
        
        Useful for understanding what the model learned and debugging.
        
        Args:
            top_n: Number of top features to return
        
        Returns:
            List of (feature_name, importance_score) tuples
        """
        if not hasattr(self.model, 'feature_importances_'):
            return []
        
        # Get all feature names
        all_feature_names = self.text_feature_names + self.metadata_feature_names
        
        # Get importance scores
        importances = self.model.feature_importances_
        
        # Create (name, score) pairs and sort
        feature_importance = list(zip(all_feature_names, importances))
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        
        return feature_importance[:top_n]
    
    def save_model(self, filepath: str):
        """
        Save trained model and vectorizer to disk.
        
        Args:
            filepath: Path to save model (without extension)
        """
        model_data = {
            'model': self.model,
            'vectorizer': self.vectorizer,
            'scaler': self.scaler,
            'text_feature_names': self.text_feature_names,
            'metadata_feature_names': self.metadata_feature_names
        }
        
        joblib.dump(model_data, f"{filepath}.joblib")
        logger.info(f"Model saved to {filepath}.joblib")
    
    def load_model(self, filepath: str):
        """
        Load trained model and vectorizer from disk.
        
        Args:
            filepath: Path to load model from (without extension)
        """
        model_data = joblib.load(f"{filepath}.joblib")
        
        self.model = model_data['model']
        self.vectorizer = model_data['vectorizer']
        self.scaler = model_data['scaler']
        self.text_feature_names = model_data['text_feature_names']
        self.metadata_feature_names = model_data['metadata_feature_names']
        
        logger.info(f"Model loaded from {filepath}.joblib")
