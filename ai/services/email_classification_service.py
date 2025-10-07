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
            result['model_version'] = model.model_version
            
            # Save prediction to database
            if save_prediction:
                content_type = ContentType.objects.get_for_model(EmailMessage)
                
                prediction = Prediction.objects.create(
                    model=model,
                    content_type=content_type,
                    object_id=email_id,
                    predicted_label=result['prediction'],
                    confidence_score=result['confidence'],
                    all_predictions=result.get('probabilities', {}),
                    status='pending'
                )
                
                # Add prediction_id to result for auto-confirmation
                result['prediction_id'] = prediction.id
                
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
        Classify all UNCLASSIFIED emails in the database.
        Skips emails that have already been classified/confirmed.
        Auto-confirms predictions with 100% confidence.
        
        Returns:
            List of classification results for each email
        """
        results = []
        # Only classify emails that haven't been classified yet
        emails = EmailMessage.objects.filter(is_classified=False)
        
        logger.info(f"Starting batch classification of {emails.count()} unclassified emails")
        
        for email in emails:
            try:
                result = EmailClassificationService.classify_email(
                    email.id,
                    save_prediction=True
                )
                
                # Auto-confirm if confidence is 95% or higher (>= 0.95)
                if result.get('confidence', 0) >= 0.95:
                    prediction_id = result.get('prediction_id')
                    if prediction_id:
                        # Auto-confirm this prediction without creating review record
                        EmailClassificationService._auto_confirm_prediction(
                            prediction_id,
                            email.id
                        )
                        result['auto_confirmed'] = True
                        logger.info(f"Auto-confirmed email {email.id} with 95%+ confidence")
                
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
    def _auto_confirm_prediction(prediction_id: int, email_id: int) -> None:
        """
        Auto-confirm a 100% confidence prediction without user review.
        Marks the email as classified and creates training sample.
        
        Args:
            prediction_id: ID of Prediction to auto-confirm
            email_id: ID of EmailMessage
        """
        try:
            from django.utils import timezone
            
            # Get prediction and email
            prediction = Prediction.objects.get(id=prediction_id)
            email = EmailMessage.objects.get(id=email_id)
            
            # Mark prediction as auto-applied (skip pending review)
            prediction.status = 'auto_applied'
            prediction.reviewed_at = timezone.now()
            prediction.save()
            
            # Mark email as classified
            email.is_classified = True
            email.classification_label = prediction.predicted_label
            email.classified_at = timezone.now()
            email.save()
            
            # Create training sample from this auto-confirmed prediction
            email_data = EmailHelper.prepare_email_for_classification(email)
            content_type = ContentType.objects.get_for_model(EmailMessage)
            
            # Convert datetime to string for JSON serialization
            date_value = email_data.get('date')
            features_dict = {
                'subject': email_data.get('subject', ''),
                'sender': email_data.get('sender', ''),
                'body': email_data.get('body', '')[:1000],  # Limit body length
                'has_attachment': email_data.get('has_attachment', False),
                'has_pdf_attachment': email_data.get('has_pdf_attachment', False),
                'date': date_value.isoformat() if date_value else None,
                'auto_confirmed': True,
                'confidence': float(prediction.confidence_score)
            }
            
            # Get or create dataset for auto-confirmed samples
            dataset, _ = TrainingDataset.objects.get_or_create(
                model_name=EmailClassificationService.MODEL_NAME,
                dataset_name='Daycare Invoice Training Data',
                defaults={
                    'notes': 'Training data from manual labels and auto-confirmed predictions',
                    'data_source': 'mixed',
                    'created_by': None
                }
            )
            
            TrainingSample.objects.create(
                dataset=dataset,
                label=prediction.predicted_label,
                features=features_dict,
                content_type=content_type,
                object_id=email.id,
                confidence=prediction.confidence_score,
                source='auto_confirmed',
                created_by=None
            )
            
            logger.info(f"Auto-confirmed prediction {prediction_id} for email {email_id}")
            
        except Exception as e:
            logger.error(f"Error auto-confirming prediction {prediction_id}: {e}")
            raise
    
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
                dataset_name='Daycare Invoice Training Data',
                defaults={
                    'notes': 'Manual labels for daycare invoice classification',
                    'data_source': 'manual',
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
            except Exception as e:
                # If feature extraction fails (no trained model), store raw data
                # Convert datetime to string for JSON serialization
                date_value = email_data.get('date')
                features_dict = {
                    'subject': email_data.get('subject', ''),
                    'sender': email_data.get('sender', ''),
                    'body': email_data.get('body', '')[:1000],  # Limit body length
                    'has_attachment': email_data.get('has_attachment', False),
                    'has_pdf_attachment': email_data.get('has_pdf_attachment', False),
                    'date': date_value.isoformat() if date_value else None
                }
                logger.debug(f"Feature extraction failed, storing raw data: {e}")
            
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
            dataset.update_counts()
            
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
        and may trigger automatic retraining. Also marks the
        email as classified.
        
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
            
            # Mark email as classified
            email = EmailMessage.objects.get(id=prediction.object_id)
            email.is_classified = True
            email.classification_label = prediction.predicted_label
            email.classified_at = timezone.now()
            email.save()
            
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
            prediction.correct_label = correct_label
            prediction.save()
            
            # Mark email as classified with CORRECT label (not predicted)
            email = EmailMessage.objects.get(id=prediction.object_id)
            email.is_classified = True
            email.classification_label = correct_label  # Use correct label
            email.classified_at = timezone.now()
            email.save()
            
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
            
            # The actual saved file has .joblib extension
            model_file_path = f"{model_filename}.joblib"
            
            # Get existing active model or find latest
            existing_model = MLModel.objects.filter(
                model_name=EmailClassificationService.MODEL_NAME,
                is_active=True
            ).first()
            
            if not existing_model:
                existing_model = MLModel.objects.filter(
                    model_name=EmailClassificationService.MODEL_NAME
                ).order_by('-created_at').first()
            
            # Deactivate previous version if exists
            if existing_model:
                old_version = existing_model.model_version
                existing_model.is_active = False
                existing_model.save()
                
                # Create new version
                new_version = EmailClassificationService._increment_version(old_version)
            else:
                new_version = '1.0.0'
            
            # Create new model instance with model file path
            model = MLModel.objects.create(
                model_name=EmailClassificationService.MODEL_NAME,
                model_version=new_version,
                model_type='classification',
                model_file=f'ai/models/{model_file_path}',
                description='Daycare invoice email classifier using Random Forest',
                created_by=user,
                is_active=True,
                performance_metrics=metrics,
                training_samples_count=len(training_data)
            )
            
            # Mark dataset as processed
            dataset.is_processed = True
            dataset.save()
            
            logger.info(f"Model training complete. Version: {model.model_version}, "
                       f"Accuracy: {metrics.get('accuracy', 0):.3f}")
            
            return {
                'success': True,
                'model_version': model.model_version,
                'metrics': metrics,
                'samples_used': len(training_data),
                'model_id': model.pk
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
                stats['model_version'] = model.model_version
                stats['last_trained'] = model.created_at
                
                if model.performance_metrics:
                    stats['model_accuracy'] = model.performance_metrics.get('accuracy')
            
            # Check if retraining needed
            if dataset and model:
                # Get samples added since last training
                new_samples = TrainingSample.objects.filter(
                    dataset=dataset,
                    created_at__gt=model.created_at
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
        # First try to get the active model
        model = MLModel.objects.filter(
            model_name=EmailClassificationService.MODEL_NAME,
            is_active=True
        ).first()
        
        if model:
            return model
        
        # If no active model, get the latest one
        model = MLModel.objects.filter(
            model_name=EmailClassificationService.MODEL_NAME
        ).order_by('-created_at').first()
        
        if model:
            return model
        
        # If no model exists at all, create a placeholder
        model = MLModel.objects.create(
            model_name=EmailClassificationService.MODEL_NAME,
            model_version='1.0.0',
            model_type='classification',
            description='Daycare invoice email classifier',
            is_active=False
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

