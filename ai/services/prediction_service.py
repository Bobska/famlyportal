"""
Prediction Service
==================

Handles AI predictions, batch predictions, and prediction feedback.
"""
from typing import List, Dict, Any, Optional, Tuple
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from ai.models import Prediction, MLModel, TrainingDataset, TrainingSample


class PredictionService:
    """
    Service for making predictions and managing prediction feedback.
    """
    
    @staticmethod
    def predict(
        model_name: str,
        content_object: Any,
        save_prediction: bool = True,
        min_confidence: float = 0.0
    ) -> Tuple[Optional[str], Optional[float], Optional[Dict[str, float]]]:
        """
        Make prediction on a single object.
        
        Args:
            model_name: Name of the model to use
            content_object: Django model instance to predict on
            save_prediction: Save prediction to database
            min_confidence: Minimum confidence threshold (0.0-1.0)
            
        Returns:
            Tuple of (predicted_label, confidence, all_probabilities)
            Returns (None, None, None) if confidence below threshold
        """
        # Load model
        try:
            ml_model = MLModel.objects.get(model_name=model_name, is_active=True)
        except MLModel.DoesNotExist:
            raise ValueError(f"No active model found: {model_name}")
        
        # Initialize classifier and load model
        # This would use a classifier registry/factory in production
        # For now, return placeholder
        # classifier = get_classifier(model_name)
        # classifier.load_model()
        # predicted_label, probabilities = classifier.predict(content_object, return_probabilities=True)
        
        # Placeholder response
        predicted_label = "placeholder"
        confidence = 0.85
        probabilities = {"positive": 0.85, "negative": 0.15}
        
        # Check confidence threshold
        if confidence < min_confidence:
            return None, None, None
        
        # Save prediction if requested
        if save_prediction:
            content_type = ContentType.objects.get_for_model(content_object)
            
            Prediction.objects.create(
                model=ml_model,
                content_type=content_type,
                object_id=content_object.pk,
                predicted_label=predicted_label,
                confidence_score=confidence,
                all_predictions=probabilities,
                status='pending'
            )
        
        return predicted_label, confidence, probabilities
    
    @staticmethod
    def predict_batch(
        model_name: str,
        content_objects: List[Any],
        save_predictions: bool = True,
        min_confidence: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Batch prediction for multiple objects (more efficient).
        
        Args:
            model_name: Name of the model to use
            content_objects: List of Django model instances
            save_predictions: Save predictions to database
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of prediction dictionaries
        """
        # Load model
        try:
            ml_model = MLModel.objects.get(model_name=model_name, is_active=True)
        except MLModel.DoesNotExist:
            raise ValueError(f"No active model found: {model_name}")
        
        results = []
        predictions_to_create = []
        
        for obj in content_objects:
            # Make prediction
            # classifier.predict() would be called here
            predicted_label = "placeholder"
            confidence = 0.85
            probabilities = {"positive": 0.85, "negative": 0.15}
            
            result = {
                'object': obj,
                'predicted_label': predicted_label if confidence >= min_confidence else None,
                'confidence': confidence,
                'probabilities': probabilities,
                'meets_threshold': confidence >= min_confidence
            }
            results.append(result)
            
            # Prepare prediction for batch creation
            if save_predictions and confidence >= min_confidence:
                content_type = ContentType.objects.get_for_model(obj)
                predictions_to_create.append(
                    Prediction(
                        model=ml_model,
                        content_type=content_type,
                        object_id=obj.pk,
                        predicted_label=predicted_label,
                        confidence_score=confidence,
                        all_predictions=probabilities,
                        status='auto_applied' if confidence >= 0.9 else 'pending'
                    )
                )
        
        # Batch create predictions
        if predictions_to_create:
            Prediction.objects.bulk_create(predictions_to_create)
        
        return results
    
    @staticmethod
    def get_pending_predictions(
        model_name: Optional[str] = None,
        content_type: Optional[ContentType] = None,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None
    ) -> 'QuerySet[Prediction]':
        """
        Get all predictions awaiting review.
        
        Args:
            model_name: Filter by model name
            content_type: Filter by content type
            min_confidence: Minimum confidence filter
            max_confidence: Maximum confidence filter
            
        Returns:
            QuerySet of Prediction objects
        """
        query = Prediction.objects.filter(status='pending')
        
        if model_name:
            query = query.filter(model__model_name=model_name)
        
        if content_type:
            query = query.filter(content_type=content_type)
        
        if min_confidence is not None:
            query = query.filter(confidence_score__gte=min_confidence)
        
        if max_confidence is not None:
            query = query.filter(confidence_score__lte=max_confidence)
        
        return query.select_related('model').order_by('-confidence_score')
    
    @staticmethod
    @transaction.atomic
    def confirm_prediction(
        prediction_id: int,
        user,
        add_to_training: bool = True,
        dataset_name: Optional[str] = None
    ) -> bool:
        """
        User confirms AI prediction is correct.
        
        Args:
            prediction_id: ID of the prediction
            user: User confirming the prediction
            add_to_training: Add to training dataset
            dataset_name: Custom dataset name, or None for default
            
        Returns:
            True if successful
        """
        prediction = Prediction.objects.select_related('model').get(id=prediction_id)
        prediction.confirm(user=user)
        
        # Add to training data for future retraining
        if add_to_training:
            # Get or create dataset
            if not dataset_name:
                dataset_name = f"{prediction.model.model_name}_user_feedback"
            
            dataset, created = TrainingDataset.objects.get_or_create(
                dataset_name=dataset_name,
                model_name=prediction.model.model_name,
                defaults={
                    'data_source': 'user_feedback',
                    'created_by': user
                }
            )
            
            # Add sample
            TrainingSample.objects.create(
                dataset=dataset,
                sample_identifier=f"Prediction_{prediction.id}",
                content_type=prediction.content_type,
                object_id=prediction.object_id,
                features={},  # Features will be re-extracted during training
                label=prediction.predicted_label,
                confidence=prediction.confidence_score,
                source='ai_confirmed',
                created_by=user,
                notes=f"Confirmed prediction from {prediction.model}"
            )
            
            dataset.update_counts()
        
        return True
    
    @staticmethod
    @transaction.atomic
    def reject_prediction(
        prediction_id: int,
        correct_label: str,
        user,
        feedback_note: str = '',
        add_to_training: bool = True,
        dataset_name: Optional[str] = None
    ) -> bool:
        """
        User rejects prediction and provides correct label.
        
        Args:
            prediction_id: ID of the prediction
            correct_label: The correct label
            user: User rejecting the prediction
            feedback_note: Optional feedback note
            add_to_training: Add corrected version to training data
            dataset_name: Custom dataset name, or None for default
            
        Returns:
            True if successful
        """
        prediction = Prediction.objects.select_related('model').get(id=prediction_id)
        prediction.reject(
            correct_label=correct_label,
            user=user,
            note=feedback_note
        )
        
        # Add corrected version to training data
        if add_to_training:
            # Get or create dataset
            if not dataset_name:
                dataset_name = f"{prediction.model.model_name}_user_feedback"
            
            dataset, created = TrainingDataset.objects.get_or_create(
                dataset_name=dataset_name,
                model_name=prediction.model.model_name,
                defaults={
                    'data_source': 'user_feedback',
                    'created_by': user
                }
            )
            
            # Add corrected sample
            TrainingSample.objects.create(
                dataset=dataset,
                sample_identifier=f"Corrected_Prediction_{prediction.id}",
                content_type=prediction.content_type,
                object_id=prediction.object_id,
                features={},  # Features will be re-extracted during training
                label=correct_label,  # Use correct label
                confidence=None,
                source='ai_rejected',
                created_by=user,
                notes=f"Rejected prediction. Was: {prediction.predicted_label}. Correct: {correct_label}. {feedback_note}"
            )
            
            dataset.update_counts()
        
        return True
    
    @staticmethod
    def get_prediction_statistics(
        model_name: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get prediction statistics.
        
        Args:
            model_name: Filter by model name
            days: Number of days to include
            
        Returns:
            Dictionary with statistics
        """
        from datetime import timedelta
        
        query = Prediction.objects.all()
        
        if model_name:
            query = query.filter(model__model_name=model_name)
        
        # Filter by date
        cutoff_date = timezone.now() - timedelta(days=days)
        query = query.filter(predicted_at__gte=cutoff_date)
        
        total_predictions = query.count()
        pending = query.filter(status='pending').count()
        confirmed = query.filter(status='confirmed').count()
        rejected = query.filter(status='rejected').count()
        auto_applied = query.filter(status='auto_applied').count()
        
        # Accuracy (confirmed / (confirmed + rejected))
        accuracy = None
        if (confirmed + rejected) > 0:
            accuracy = confirmed / (confirmed + rejected)
        
        # Average confidence
        avg_confidence = query.aggregate(
            models.Avg('confidence_score')
        )['confidence_score__avg']
        
        return {
            'total_predictions': total_predictions,
            'pending': pending,
            'confirmed': confirmed,
            'rejected': rejected,
            'auto_applied': auto_applied,
            'accuracy': accuracy,
            'average_confidence': avg_confidence,
            'days': days,
            'model_name': model_name or 'all'
        }
