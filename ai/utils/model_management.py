"""
Model Management Utilities
===========================

Utilities for managing model versions, activation, rollback, and comparison.
"""
from typing import Dict, Any, Optional, List, Tuple
from django.db import transaction
from ai.models import MLModel


class ModelManager:
    """
    Utility class for managing ML models and versions.
    """
    
    @staticmethod
    def get_active_model(model_name: str) -> Optional[MLModel]:
        """
        Get currently active model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            MLModel instance or None if no active model
        """
        try:
            return MLModel.objects.get(model_name=model_name, is_active=True)
        except MLModel.DoesNotExist:
            return None
    
    @staticmethod
    def get_latest_model(model_name: str) -> Optional[MLModel]:
        """
        Get latest model version (regardless of active status).
        
        Args:
            model_name: Name of the model
            
        Returns:
            MLModel instance or None
        """
        return MLModel.objects.filter(
            model_name=model_name
        ).order_by('-created_at').first()
    
    @staticmethod
    def get_all_versions(model_name: str) -> List[MLModel]:
        """
        Get all versions of a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            List of MLModel instances
        """
        return list(MLModel.objects.filter(
            model_name=model_name
        ).order_by('-created_at'))
    
    @staticmethod
    @transaction.atomic
    def promote_model(model_id: int) -> MLModel:
        """
        Set a model version as active (promotes it to production).
        Deactivates all other versions of the same model.
        
        Args:
            model_id: ID of the model to promote
            
        Returns:
            Promoted MLModel instance
        """
        model = MLModel.objects.get(id=model_id)
        
        # Deactivate all other versions
        MLModel.objects.filter(
            model_name=model.model_name,
            is_active=True
        ).exclude(id=model_id).update(is_active=False)
        
        # Activate this version
        model.is_active = True
        model.save()
        
        print(f"Promoted model: {model}")
        return model
    
    @staticmethod
    @transaction.atomic
    def rollback_model(model_name: str) -> Optional[MLModel]:
        """
        Rollback to previous model version.
        Deactivates current active model and activates the previous one.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Previous MLModel instance that was activated, or None if no previous version
        """
        # Get current active model
        try:
            current_model = MLModel.objects.get(
                model_name=model_name,
                is_active=True
            )
        except MLModel.DoesNotExist:
            print(f"No active model to rollback: {model_name}")
            return None
        
        # Get previous version (by created_at)
        previous_model = MLModel.objects.filter(
            model_name=model_name,
            created_at__lt=current_model.created_at
        ).order_by('-created_at').first()
        
        if not previous_model:
            print(f"No previous version to rollback to: {model_name}")
            return None
        
        # Deactivate current
        current_model.is_active = False
        current_model.save()
        
        # Activate previous
        previous_model.is_active = True
        previous_model.save()
        
        print(f"Rolled back from {current_model} to {previous_model}")
        return previous_model
    
    @staticmethod
    def compare_models(
        model_id1: int,
        model_id2: int
    ) -> Dict[str, Any]:
        """
        Compare performance metrics of two models.
        
        Args:
            model_id1: First model ID
            model_id2: Second model ID
            
        Returns:
            Dictionary with comparison results
        """
        model1 = MLModel.objects.get(id=model_id1)
        model2 = MLModel.objects.get(id=model_id2)
        
        if model1.model_name != model2.model_name:
            raise ValueError(f"Cannot compare different models: {model1.model_name} vs {model2.model_name}")
        
        # Extract metrics
        metrics1 = model1.performance_metrics
        metrics2 = model2.performance_metrics
        
        comparison = {
            'model1': {
                'version': model1.model_version,
                'created_at': model1.created_at.isoformat(),
                'is_active': model1.is_active,
                'training_samples': model1.training_samples_count,
                'metrics': metrics1
            },
            'model2': {
                'version': model2.model_version,
                'created_at': model2.created_at.isoformat(),
                'is_active': model2.is_active,
                'training_samples': model2.training_samples_count,
                'metrics': metrics2
            },
            'differences': {}
        }
        
        # Compare key metrics
        for metric in ['accuracy', 'precision', 'recall', 'f1_score']:
            if metric in metrics1 and metric in metrics2:
                val1 = metrics1[metric]
                val2 = metrics2[metric]
                diff = val2 - val1
                comparison['differences'][metric] = {
                    'model1': val1,
                    'model2': val2,
                    'difference': diff,
                    'improvement': diff > 0
                }
        
        # Determine which is better
        if 'accuracy' in comparison['differences']:
            comparison['better_model'] = 'model2' if comparison['differences']['accuracy']['improvement'] else 'model1'
        
        return comparison
    
    @staticmethod
    def get_model_history(model_name: str) -> List[Dict[str, Any]]:
        """
        Get version history for a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            List of version info dictionaries
        """
        versions = MLModel.objects.filter(
            model_name=model_name
        ).order_by('-created_at')
        
        history = []
        for model in versions:
            history.append({
                'id': model.id,
                'version': model.model_version,
                'created_at': model.created_at.isoformat(),
                'created_by': model.created_by.username if model.created_by else None,
                'is_active': model.is_active,
                'training_samples': model.training_samples_count,
                'accuracy': model.get_accuracy(),
                'f1_score': model.get_f1_score(),
                'description': model.description
            })
        
        return history
    
    @staticmethod
    def get_best_model(
        model_name: str,
        metric: str = 'accuracy'
    ) -> Optional[MLModel]:
        """
        Get model with best performance on specified metric.
        
        Args:
            model_name: Name of the model
            metric: Metric to optimize ('accuracy', 'f1_score', etc.)
            
        Returns:
            Best performing MLModel instance or None
        """
        models = MLModel.objects.filter(model_name=model_name)
        
        best_model = None
        best_score = -1
        
        for model in models:
            score = model.performance_metrics.get(metric)
            if score and score > best_score:
                best_score = score
                best_model = model
        
        return best_model
    
    @staticmethod
    def delete_old_versions(
        model_name: str,
        keep_count: int = 3,
        keep_active: bool = True
    ) -> int:
        """
        Delete old model versions, keeping only the most recent ones.
        
        Args:
            model_name: Name of the model
            keep_count: Number of versions to keep
            keep_active: Always keep active model regardless of count
            
        Returns:
            Number of models deleted
        """
        models = MLModel.objects.filter(
            model_name=model_name
        ).order_by('-created_at')
        
        to_keep_ids = []
        
        # Always keep active model
        if keep_active:
            active_model = ModelManager.get_active_model(model_name)
            if active_model:
                to_keep_ids.append(active_model.id)
        
        # Keep most recent versions
        for model in models[:keep_count]:
            if model.id not in to_keep_ids:
                to_keep_ids.append(model.id)
        
        # Delete the rest
        models_to_delete = MLModel.objects.filter(
            model_name=model_name
        ).exclude(id__in=to_keep_ids)
        
        count = models_to_delete.count()
        models_to_delete.delete()
        
        print(f"Deleted {count} old versions of {model_name}")
        return count
    
    @staticmethod
    def get_model_statistics() -> Dict[str, Any]:
        """
        Get overall statistics about all models.
        
        Returns:
            Dictionary with statistics
        """
        from django.db.models import Count, Avg
        
        total_models = MLModel.objects.count()
        active_models = MLModel.objects.filter(is_active=True).count()
        
        # Models per name
        models_by_name = MLModel.objects.values('model_name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Average metrics (for active models)
        active_models_qs = MLModel.objects.filter(is_active=True)
        avg_accuracy = None
        if active_models_qs.exists():
            accuracies = [
                m.get_accuracy() for m in active_models_qs 
                if m.get_accuracy() is not None
            ]
            avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else None
        
        return {
            'total_models': total_models,
            'active_models': active_models,
            'unique_model_names': len(models_by_name),
            'models_by_name': list(models_by_name),
            'average_accuracy': avg_accuracy,
        }
