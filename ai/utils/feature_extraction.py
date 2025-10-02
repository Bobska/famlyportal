"""
Feature Extraction Utilities
=============================

Utilities for extracting features from text, metadata, and combined sources.
"""
from typing import Dict, List, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
import re


class FeatureExtractor:
    """
    Utility class for extracting features from various data sources.
    """
    
    @staticmethod
    def extract_text_features(
        text: str,
        config: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """
        Extract features from text using TF-IDF or Count Vectorizer.
        
        Args:
            text: Input text
            config: Configuration dict with keys:
                - method: 'tfidf' or 'count' (default: 'tfidf')
                - max_features: Maximum number of features (default: 1000)
                - ngram_range: Tuple like (1, 2) for unigrams and bigrams
                - min_df: Minimum document frequency (default: 1)
                - max_df: Maximum document frequency (default: 1.0)
                - stop_words: 'english' or None (default: 'english')
                
        Returns:
            Feature vector as numpy array
        """
        if config is None:
            config = {}
        
        method = config.get('method', 'tfidf')
        max_features = config.get('max_features', 1000)
        ngram_range = config.get('ngram_range', (1, 2))
        min_df = config.get('min_df', 1)
        max_df = config.get('max_df', 1.0)
        stop_words = config.get('stop_words', 'english')
        
        # Initialize vectorizer
        if method == 'tfidf':
            vectorizer = TfidfVectorizer(
                max_features=max_features,
                ngram_range=ngram_range,
                min_df=min_df,
                max_df=max_df,
                stop_words=stop_words
            )
        else:
            vectorizer = CountVectorizer(
                max_features=max_features,
                ngram_range=ngram_range,
                min_df=min_df,
                max_df=max_df,
                stop_words=stop_words
            )
        
        # Transform text
        try:
            features = vectorizer.fit_transform([text]).toarray()[0]
        except Exception as e:
            # Fallback to empty features
            print(f"Feature extraction failed: {e}")
            features = np.zeros(max_features)
        
        return features
    
    @staticmethod
    def extract_metadata_features(
        metadata_dict: Dict[str, Any],
        feature_keys: Optional[List[str]] = None
    ) -> np.ndarray:
        """
        Extract features from structured metadata.
        
        Args:
            metadata_dict: Dictionary of metadata
            feature_keys: List of keys to extract, or None for all
            
        Returns:
            Feature vector as numpy array
        """
        if feature_keys is None:
            feature_keys = list(metadata_dict.keys())
        
        features = []
        
        for key in feature_keys:
            value = metadata_dict.get(key)
            
            # Convert to numeric
            if value is None:
                features.append(0.0)
            elif isinstance(value, bool):
                features.append(1.0 if value else 0.0)
            elif isinstance(value, (int, float)):
                features.append(float(value))
            elif isinstance(value, str):
                # Hash string to number
                features.append(float(hash(value) % 10000) / 10000)
            else:
                features.append(0.0)
        
        return np.array(features)
    
    @staticmethod
    def combine_features(
        text_features: np.ndarray,
        metadata_features: np.ndarray
    ) -> np.ndarray:
        """
        Combine multiple feature types into single vector.
        
        Args:
            text_features: Text feature vector
            metadata_features: Metadata feature vector
            
        Returns:
            Combined feature vector
        """
        return np.concatenate([text_features, metadata_features])
    
    @staticmethod
    def extract_keyword_features(
        text: str,
        keywords: List[str],
        case_sensitive: bool = False
    ) -> Dict[str, float]:
        """
        Extract keyword-based features from text.
        
        Args:
            text: Input text
            keywords: List of keywords to look for
            case_sensitive: Whether matching is case-sensitive
            
        Returns:
            Dictionary of keyword: count
        """
        if not case_sensitive:
            text = text.lower()
            keywords = [k.lower() for k in keywords]
        
        features = {}
        for keyword in keywords:
            # Count occurrences
            count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
            features[keyword] = float(count)
        
        return features
    
    @staticmethod
    def extract_email_features(email_object: Any) -> Dict[str, Any]:
        """
        Extract features specific to email objects.
        
        Args:
            email_object: Email model instance
            
        Returns:
            Dictionary of features
        """
        features = {}
        
        # Text features
        if hasattr(email_object, 'subject'):
            features['subject_length'] = len(email_object.subject or '')
            features['has_subject'] = bool(email_object.subject)
        
        if hasattr(email_object, 'body_text'):
            features['body_length'] = len(email_object.body_text or '')
            features['has_body'] = bool(email_object.body_text)
        
        # Sender features
        if hasattr(email_object, 'sender_email'):
            sender = email_object.sender_email or ''
            features['sender_domain'] = sender.split('@')[-1] if '@' in sender else ''
        
        # Attachment features
        if hasattr(email_object, 'has_attachments'):
            features['has_attachments'] = float(email_object.has_attachments)
        
        if hasattr(email_object, 'attachment_count'):
            features['attachment_count'] = float(email_object.attachment_count or 0)
        
        # Label features
        if hasattr(email_object, 'labels'):
            labels = email_object.labels or []
            features['label_count'] = float(len(labels))
            features['is_important'] = float('IMPORTANT' in labels)
            features['is_starred'] = float('STARRED' in labels)
        
        return features
    
    @staticmethod
    def normalize_features(features: np.ndarray) -> np.ndarray:
        """
        Normalize features to 0-1 range.
        
        Args:
            features: Feature vector
            
        Returns:
            Normalized feature vector
        """
        min_val = features.min()
        max_val = features.max()
        
        if max_val - min_val == 0:
            return np.zeros_like(features)
        
        return (features - min_val) / (max_val - min_val)
    
    @staticmethod
    def get_text_statistics(text: str) -> Dict[str, float]:
        """
        Get statistical features from text.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary of text statistics
        """
        words = text.split()
        sentences = text.split('.')
        
        return {
            'char_count': float(len(text)),
            'word_count': float(len(words)),
            'sentence_count': float(len(sentences)),
            'avg_word_length': float(np.mean([len(w) for w in words]) if words else 0),
            'avg_sentence_length': float(np.mean([len(s) for s in sentences]) if sentences else 0),
            'uppercase_ratio': float(sum(1 for c in text if c.isupper()) / len(text) if text else 0),
            'digit_ratio': float(sum(1 for c in text if c.isdigit()) / len(text) if text else 0),
            'punctuation_ratio': float(sum(1 for c in text if c in '.,!?;:') / len(text) if text else 0),
        }
