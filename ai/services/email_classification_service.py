"""
Email Classification Service
============================

Main service for classifying emails using the daycare invoice classifier.
Handles predictions, training data management, and active learning workflow.
"""
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from ai.models import MLModel, TrainingDataset, TrainingSample, Prediction
from ai.classifiers.email_classifier import DaycareInvoiceClassifier
from gmail_integration.models import EmailMessage
from gmail_integration.services_pkg.email_helper import EmailHelper

logger = logging.getLogger(__name__)


class EmailClassificationService:
    """
    Service for email classification operations.
    
    Provides high-level interface for:
    - Classifying individual and batch emails
    - Managing training data from user feedback
    - Training and retraining models
    - Active learning feedback loop
    """
    
    MODEL_NAME = 'daycare_invoice_classifier'
    DATASET_NAME = 'daycare_invoice_manual'
    
    @staticmethod
    def classify_email(email_id: int, save_prediction: bool = True) -> Dict[str, Any]:
        """
        Classify a single email as daycare invoice or not.
        
        Args:
            email_id: ID of EmailMessage to classify
            save_prediction: If True, save Prediction record to database
        
        Returns:
            Dictionary with:
                - email_id: Email ID
                - prediction: 'daycare_invoice' or 'not_invoice'
                - confidence: float 0.0-1.0
                - probabilities: dict of class probabilities
                - model_version: version of model used
        
        Raises:
            EmailMessage.DoesNotExist: If email not found
            ValueError: If no trained model available
        """
        try:
            # Load email
            email = EmailMessage.objects.get(id=email_id)
            
            # Get active model
            model = EmailClassificationService._get_or_create_model()
            if not model.is_active or not model.model_file:
                raise ValueError("No trained model available. Please train the model first.")
            
            # Load classifier
            classifier = DaycareInvoiceClassifier()
            model_path = os.path.join(settings.MEDIA_ROOT, model.model_file.name)
            model_path_without_ext = model_path.replace('.joblib', '')
            classifier.load_model(model_path_without_ext)
            
            # Prepare email data
            email_data = EmailHelper.prepare_email_for_classification(email)
            
            # Make prediction
            result = classifier.predict(email_data, return_probabilities=True)
            
            # Add metadata
            result['email_id'] = email_id
            result['model_version'] = model.version
            
            # Save prediction to database
            if save_prediction:
                content_type = ContentType.objects.get_for_model(EmailMessage)
                
                Prediction.objects.create(
                    model=model,
                    content_type=content_type,
                    object_id=email_id,
                    predicted_label=result['prediction'],
                    confidence_score=result['confidence'],
                    prediction_data=result,
                    status='pending'
                )
                
                logger.info(f"Classified email {email_id}: {result['prediction']} "
                           f"(confidence: {result['confidence']:.2f})")
            
            return result
            
        except EmailMessage.DoesNotExist:
            logger.error(f"Email {email_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error classifying email {email_id}: {e}")
            raise
    
    @staticmethod
    def classify_all_emails() -> List[Dict[str, Any]]:
        """
        Classify all emails in the database.
        
        Returns:
            List of classification results for each email
        """
        results = []
        emails = EmailMessage.objects.all()
        
        logger.info(f"Starting batch classification of {emails.count()} emails")
        
        for email in emails:
            try:
                result = EmailClassificationService.classify_email(
                    email.id,
                    save_prediction=True
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to classify email {email.id}: {e}")
                results.append({
                    'email_id': email.id,
                    'error': str(e),
                    'prediction': None
                })
        
        logger.info(f"Batch classification complete: {len(results)} emails processed")
        return results
    
    @staticmethod
    def add_manual_training_sample(
        email_id: int,
        is_daycare_invoice: bool,
        user
    ) -> TrainingSample:
        """
        Manually label an email for training (user feedback).
        
        This is the primary way to build initial training data and
        provide corrections during active learning.
        
        Args:
            email_id: ID of EmailMessage to label
            is_daycare_invoice: True if email is daycare invoice, False otherwise
            user: User providing the label
        
        Returns:
            Created TrainingSample instance
        """
        try:
            # Load email
            email = EmailMessage.objects.get(id=email_id)
            
            # Get or create dataset
            dataset, _ = TrainingDataset.objects.get_or_create(
                model_name=EmailClassificationService.MODEL_NAME,
                defaults={
                    'description': 'Manual labels for daycare invoice classification',
                    'created_by': user
                }
            )
            
            # Prepare email data
            email_data = EmailHelper.prepare_email_for_classification(email)
            
            # Create label
            label = 'daycare_invoice' if is_daycare_invoice else 'not_invoice'
            
            # Extract features for storage
            classifier = DaycareInvoiceClassifier()
            try:
                features = classifier.extract_features(email_data)
                features_dict = {
                    'text_features': features[0][:500].tolist() if len(features[0]) > 500 else features[0].tolist(),
                    'metadata_features': features[0][-9:].tolist()  # Last 9 are metadata
                }
            except:
                # If feature extraction fails (no trained model), store raw data
                features_dict = email_data
            
            # Create training sample
            content_type = ContentType.objects.get_for_model(EmailMessage)
            
            sample = TrainingSample.objects.create(
                dataset=dataset,
                content_type=content_type,
                object_id=email_id,
                label=label,
                features=features_dict,
                source='manual',
                created_by=user
            )
            
            # Update dataset statistics
            dataset.update_sample_counts()
            
            logger.info(f"Added training sample: email {email_id} labeled as '{label}'")
            
            return sample
            
        except EmailMessage.DoesNotExist:
            logger.error(f"Email {email_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error adding training sample for email {email_id}: {e}")
            raise
    
    @staticmethod
    def confirm_prediction(prediction_id: int, user) -> Prediction:
        """
        User confirms AI prediction was correct.
        
        This adds the confirmed prediction to training data
        and may trigger automatic retraining.
        
        Args:
            prediction_id: ID of Prediction to confirm
            user: User confirming the prediction
        
        Returns:
            Updated Prediction instance
        """
        try:
            prediction = Prediction.objects.get(id=prediction_id)
            
            # Update prediction status
            prediction.status = 'confirmed'
            prediction.reviewed_by = user
            prediction.reviewed_at = timezone.now()
            prediction.save()
            
            # Add to training data
            email_id = prediction.object_id
            is_daycare_invoice = (prediction.predicted_label == 'daycare_invoice')
            
            EmailClassificationService.add_manual_training_sample(
                email_id,
                is_daycare_invoice,
                user
            )
            
            # Check if should retrain
            EmailClassificationService._check_and_retrain()
            
            logger.info(f"Prediction {prediction_id} confirmed by {user.username}")
            
            return prediction
            
        except Prediction.DoesNotExist:
            logger.error(f"Prediction {prediction_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error confirming prediction {prediction_id}: {e}")
            raise
    
    @staticmethod
    def reject_prediction(prediction_id: int, correct_label: str, user) -> Prediction:
        """
        User rejects AI prediction and provides correct label.
        
        This is critical for active learning - the model learns
        from its mistakes.
        
        Args:
            prediction_id: ID of Prediction to reject
            correct_label: Correct label ('daycare_invoice' or 'not_invoice')
            user: User providing correction
        
        Returns:
            Updated Prediction instance
        """
        try:
            prediction = Prediction.objects.get(id=prediction_id)
            
            # Update prediction status
            prediction.status = 'rejected'
            prediction.reviewed_by = user
            prediction.reviewed_at = timezone.now()
            prediction.actual_label = correct_label
            prediction.save()
            
            # Add corrected label to training data
            email_id = prediction.object_id
            is_daycare_invoice = (correct_label == 'daycare_invoice')
            
            EmailClassificationService.add_manual_training_sample(
                email_id,
                is_daycare_invoice,
                user
            )
            
            # Check if should retrain (rejections are more important)
            EmailClassificationService._check_and_retrain()
            
            logger.info(f"Prediction {prediction_id} rejected by {user.username}, "
                       f"correct label: {correct_label}")
            
            return prediction
            
        except Prediction.DoesNotExist:
            logger.error(f"Prediction {prediction_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error rejecting prediction {prediction_id}: {e}")
            raise
    
    @staticmethod
    def train_from_samples(min_samples: int = 10, user=None) -> Dict[str, Any]:
        """
        Train classifier from training samples in database.
        
        Args:
            min_samples: Minimum number of samples required to train
            user: User triggering training (optional)
        
        Returns:
            Dictionary with training results and metrics
        
        Raises:
            ValueError: If insufficient training samples
        """
        try:
            # Get dataset
            dataset = TrainingDataset.objects.filter(
                model_name=EmailClassificationService.MODEL_NAME
            ).first()
            
            if not dataset:
                raise ValueError("No training dataset found")
            
            # Get samples
            samples = TrainingSample.objects.filter(dataset=dataset)
            
            if samples.count() < min_samples:
                raise ValueError(
                    f"Insufficient training samples. Need {min_samples}, "
                    f"have {samples.count()}"
                )
            
            # Prepare training data
            training_data = []
            labels = []
            
            for sample in samples:
                try:
                    # Get email
                    email = EmailMessage.objects.get(id=sample.object_id)
                    email_data = EmailHelper.prepare_email_for_classification(email)
                    training_data.append(email_data)
                    labels.append(sample.label)
                except EmailMessage.DoesNotExist:
                    logger.warning(f"Email {sample.object_id} not found, skipping")
                    continue
            
            if len(training_data) < min_samples:
                raise ValueError(
                    f"After filtering, only {len(training_data)} valid samples available"
                )
            
            # Train classifier
            logger.info(f"Training classifier with {len(training_data)} samples")
            classifier = DaycareInvoiceClassifier()
            metrics = classifier.train(training_data, labels)
            
            # Save model
            model_dir = os.path.join(settings.MEDIA_ROOT, 'ai', 'models')
            os.makedirs(model_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            model_filename = f"{EmailClassificationService.MODEL_NAME}_{timestamp}"
            model_path = os.path.join(model_dir, model_filename)
            
            classifier.save_model(model_path)
            
            # Create or update MLModel record
            model, created = MLModel.objects.get_or_create(
                model_name=EmailClassificationService.MODEL_NAME,
                defaults={
                    'model_type': 'classification',
                    'description': 'Daycare invoice email classifier using Random Forest',
                    'created_by': user
                }
            )
            
            # Deactivate previous version
            if not created:
                old_version = model.version
                model.is_active = False
                model.save()
                
                # Create new version
                model.pk = None  # Create new instance
                model.is_active = True
                model.version = EmailClassificationService._increment_version(old_version)
            
            # Update model info
            model.model_file = f"ai/models/{model_filename}.joblib"
            model.performance_metrics = metrics
            model.training_samples_count = len(training_data)
            model.last_trained = timezone.now()
            model.save()
            
            # Mark dataset as processed
            dataset.is_processed = True
            dataset.processed_at = timezone.now()
            dataset.save()
            
            logger.info(f"Model training complete. Version: {model.version}, "
                       f"Accuracy: {metrics.get('accuracy', 0):.3f}")
            
            return {
                'success': True,
                'model_version': model.version,
                'metrics': metrics,
                'samples_used': len(training_data),
                'model_id': model.id
            }
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise
    
    @staticmethod
    def get_training_statistics() -> Dict[str, Any]:
        """
        Get statistics about training data and model performance.
        
        Returns:
            Dictionary with:
                - total_samples: Total training samples
                - positive_samples: Daycare invoice samples
                - negative_samples: Not invoice samples
                - model_accuracy: Current model accuracy
                - last_trained: When model was last trained
                - needs_retraining: Boolean if retraining recommended
        """
        stats = {
            'total_samples': 0,
            'positive_samples': 0,
            'negative_samples': 0,
            'model_accuracy': None,
            'last_trained': None,
            'needs_retraining': False,
            'model_version': None
        }
        
        try:
            # Get dataset stats
            dataset = TrainingDataset.objects.filter(
                model_name=EmailClassificationService.MODEL_NAME
            ).first()
            
            if dataset:
                stats['total_samples'] = dataset.total_samples
                stats['positive_samples'] = dataset.positive_samples
                stats['negative_samples'] = dataset.negative_samples
            
            # Get model stats
            model = MLModel.objects.filter(
                model_name=EmailClassificationService.MODEL_NAME,
                is_active=True
            ).first()
            
            if model:
                stats['model_version'] = model.version
                stats['last_trained'] = model.last_trained
                
                if model.performance_metrics:
                    stats['model_accuracy'] = model.performance_metrics.get('accuracy')
            
            # Check if retraining needed
            if dataset and model:
                # Get samples added since last training
                new_samples = TrainingSample.objects.filter(
                    dataset=dataset,
                    created_at__gt=model.last_trained
                ).count()
                
                retrain_threshold = getattr(
                    settings, 'AI_EMAIL_CLASSIFIER', {}
                ).get('RETRAIN_THRESHOLD', 20)
                
                stats['needs_retraining'] = (new_samples >= retrain_threshold)
                stats['new_samples_since_training'] = new_samples
        
        except Exception as e:
            logger.error(f"Error getting training statistics: {e}")
        
        return stats
    
    @staticmethod
    def _get_or_create_model() -> MLModel:
        """Get active model or create placeholder."""
        model, created = MLModel.objects.get_or_create(
            model_name=EmailClassificationService.MODEL_NAME,
            defaults={
                'model_type': 'classification',
                'description': 'Daycare invoice email classifier',
                'version': '1.0.0',
                'is_active': False
            }
        )
        return model
    
    @staticmethod
    def _check_and_retrain():
        """Check if automatic retraining should be triggered."""
        try:
            config = getattr(settings, 'AI_EMAIL_CLASSIFIER', {})
            retrain_threshold = config.get('RETRAIN_THRESHOLD', 20)
            
            stats = EmailClassificationService.get_training_statistics()
            
            if stats.get('needs_retraining'):
                logger.info(f"Automatic retraining triggered "
                           f"({stats.get('new_samples_since_training')} new samples)")
                EmailClassificationService.train_from_samples(min_samples=10)
        except Exception as e:
            logger.error(f"Error in automatic retraining: {e}")
    
    @staticmethod
    def _increment_version(version: str) -> str:
        """Increment semantic version string."""
        try:
            parts = version.split('.')
            parts[-1] = str(int(parts[-1]) + 1)
            return '.'.join(parts)
        except:
            return '1.0.1'
    
    @staticmethod
    def _get_confidence_class(confidence: float) -> str:
        """Get CSS class based on confidence score."""
        if confidence >= 0.8:
            return 'success'  # High confidence - green
        elif confidence >= 0.6:
            return 'warning'  # Medium confidence - yellow
        else:
            return 'danger'  # Low confidence - red

