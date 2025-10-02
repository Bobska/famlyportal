"""
Training Service
================

Manages training datasets, samples, and triggers model training.
"""
from typing import List, Dict, Any, Optional
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from ai.models import TrainingDataset, TrainingSample, MLModel


class TrainingService:
    """
    Service for managing training data and triggering model training.
    """
    
    @staticmethod
    def create_dataset(
        name: str,
        model_name: str,
        data_source: str = 'manual',
        user=None,
        notes: str = ''
    ) -> TrainingDataset:
        """
        Create a new training dataset.
        
        Args:
            name: Dataset name
            model_name: Associated model name
            data_source: Source of data ('manual', 'user_feedback', etc.)
            user: User creating the dataset
            notes: Optional notes
            
        Returns:
            TrainingDataset instance
        """
        dataset = TrainingDataset.objects.create(
            dataset_name=name,
            model_name=model_name,
            data_source=data_source,
            created_by=user,
            notes=notes
        )
        print(f"Created dataset: {dataset}")
        return dataset
    
    @staticmethod
    @transaction.atomic
    def add_samples_to_dataset(
        dataset_id: int,
        samples: List[Dict[str, Any]],
        user=None
    ) -> int:
        """
        Add training samples to existing dataset.
        
        Args:
            dataset_id: ID of the dataset
            samples: List of sample dicts with keys:
                - content_object: Django model instance
                - label: Ground truth label
                - identifier: Human-readable identifier
                - features: Optional pre-extracted features
                - confidence: Optional confidence score
                - source: Optional source ('manual', 'ai_confirmed', etc.)
            user: User adding the samples
            
        Returns:
            Number of samples added
        """
        dataset = TrainingDataset.objects.get(id=dataset_id)
        
        created_count = 0
        for sample_data in samples:
            content_object = sample_data['content_object']
            content_type = ContentType.objects.get_for_model(content_object)
            
            # Check if sample already exists
            exists = TrainingSample.objects.filter(
                dataset=dataset,
                content_type=content_type,
                object_id=content_object.pk
            ).exists()
            
            if not exists:
                TrainingSample.objects.create(
                    dataset=dataset,
                    sample_identifier=sample_data.get('identifier', str(content_object)),
                    content_type=content_type,
                    object_id=content_object.pk,
                    features=sample_data.get('features', {}),
                    label=sample_data['label'],
                    confidence=sample_data.get('confidence'),
                    source=sample_data.get('source', 'manual'),
                    created_by=user
                )
                created_count += 1
        
        # Update dataset counts
        dataset.update_counts()
        
        print(f"Added {created_count} samples to dataset {dataset}")
        return created_count
    
    @staticmethod
    def get_training_data(
        dataset_id: Optional[int] = None,
        model_name: Optional[str] = None,
        include_features: bool = True
    ) -> tuple:
        """
        Retrieve training data for model training.
        
        Args:
            dataset_id: Specific dataset ID, or None for all datasets
            model_name: Filter by model name
            include_features: If False, return objects instead of features
            
        Returns:
            Tuple of (data_list, labels_list)
        """
        # Build query
        query = TrainingSample.objects.all()
        
        if dataset_id:
            query = query.filter(dataset_id=dataset_id)
        elif model_name:
            query = query.filter(dataset__model_name=model_name)
        
        query = query.select_related('content_type', 'dataset')
        
        # Extract data and labels
        data_list = []
        labels_list = []
        
        for sample in query:
            if include_features:
                # Use pre-extracted features if available
                if sample.features:
                    data_list.append(sample.features)
                else:
                    # Otherwise use the content object (classifier will extract features)
                    data_list.append(sample.content_object)
            else:
                # Return the actual objects
                data_list.append(sample.content_object)
            
            labels_list.append(sample.label)
        
        print(f"Retrieved {len(data_list)} training samples")
        return data_list, labels_list
    
    @staticmethod
    def trigger_training(
        model_name: str,
        dataset_id: Optional[int] = None,
        version: str = '1.0.0',
        description: str = '',
        user=None
    ) -> Dict[str, Any]:
        """
        Trigger model training with specified dataset.
        
        Args:
            model_name: Name of model to train
            dataset_id: Specific dataset to use, or None for all data
            version: Version number for new model
            description: Model description
            user: User triggering training
            
        Returns:
            Dictionary with training results and metrics
        """
        # Get training data
        data_list, labels_list = TrainingService.get_training_data(
            dataset_id=dataset_id,
            model_name=model_name,
            include_features=False  # Let classifier extract features
        )
        
        if len(data_list) < 10:
            raise ValueError(f"Not enough training samples ({len(data_list)}). Need at least 10.")
        
        # Import and initialize classifier
        # This assumes a registry or factory pattern for classifiers
        # For now, return info about what would be trained
        result = {
            'model_name': model_name,
            'version': version,
            'training_samples': len(data_list),
            'unique_labels': len(set(labels_list)),
            'status': 'ready_for_training',
            'message': 'Call classifier.train() with this data'
        }
        
        # Mark datasets as processed
        if dataset_id:
            dataset = TrainingDataset.objects.get(id=dataset_id)
            dataset.is_processed = True
            dataset.save()
        
        return result
    
    @staticmethod
    def should_retrain(
        model_name: str,
        threshold: int = 20
    ) -> tuple:
        """
        Check if model should be retrained based on new samples.
        
        Args:
            model_name: Name of the model
            threshold: Number of new samples needed to trigger retraining
            
        Returns:
            Tuple of (should_retrain: bool, new_samples_count: int, reason: str)
        """
        try:
            # Get active model
            model = MLModel.objects.get(model_name=model_name, is_active=True)
            
            # Count new samples since model was created
            new_samples = TrainingSample.objects.filter(
                dataset__model_name=model_name,
                created_at__gt=model.created_at,
                dataset__is_processed=False
            ).count()
            
            should_retrain = new_samples >= threshold
            
            if should_retrain:
                reason = f"{new_samples} new samples available (threshold: {threshold})"
            else:
                reason = f"Only {new_samples} new samples (need {threshold - new_samples} more)"
            
            return should_retrain, new_samples, reason
            
        except MLModel.DoesNotExist:
            # No active model, should train initial model
            total_samples = TrainingSample.objects.filter(
                dataset__model_name=model_name
            ).count()
            
            if total_samples >= threshold:
                return True, total_samples, f"No active model, {total_samples} samples available for initial training"
            else:
                return False, total_samples, f"Need {threshold - total_samples} more samples for initial training"
    
    @staticmethod
    def get_dataset_statistics(model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about training datasets.
        
        Args:
            model_name: Filter by model name, or None for all
            
        Returns:
            Dictionary with statistics
        """
        query = TrainingDataset.objects.all()
        if model_name:
            query = query.filter(model_name=model_name)
        
        total_datasets = query.count()
        total_samples = TrainingSample.objects.filter(dataset__in=query).count()
        processed_datasets = query.filter(is_processed=True).count()
        unprocessed_samples = TrainingSample.objects.filter(
            dataset__in=query,
            dataset__is_processed=False
        ).count()
        
        # Label distribution
        label_counts = {}
        for sample in TrainingSample.objects.filter(dataset__in=query):
            label_counts[sample.label] = label_counts.get(sample.label, 0) + 1
        
        return {
            'total_datasets': total_datasets,
            'total_samples': total_samples,
            'processed_datasets': processed_datasets,
            'unprocessed_datasets': total_datasets - processed_datasets,
            'unprocessed_samples': unprocessed_samples,
            'label_distribution': label_counts,
            'model_name': model_name or 'all'
        }
