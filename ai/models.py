"""
AI Hub Models
=============

Core database models for ML model management, training datasets,
training samples, and predictions.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import os

User = get_user_model()


class MLModel(models.Model):
    """
    Stores ML model metadata, file, and performance metrics.
    Supports versioning and multiple model types.
    """
    MODEL_TYPE_CHOICES = [
        ('classification', 'Classification'),
        ('regression', 'Regression'),
        ('clustering', 'Clustering'),
        ('ranking', 'Ranking'),
        ('other', 'Other'),
    ]
    
    model_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Unique identifier for the model (e.g., 'email_daycare_classifier')"
    )
    model_version = models.CharField(
        max_length=20,
        help_text="Semantic version (e.g., '1.0.0', '2.1.3')"
    )
    model_type = models.CharField(
        max_length=20,
        choices=MODEL_TYPE_CHOICES,
        default='classification'
    )
    model_file = models.FileField(
        upload_to='ai/models/',
        help_text="Pickled model file (scikit-learn, joblib, etc.)"
    )
    vectorizer_file = models.FileField(
        upload_to='ai/vectorizers/',
        null=True,
        blank=True,
        help_text="Pickled vectorizer/transformer (if applicable)"
    )
    feature_config = models.JSONField(
        default=dict,
        help_text="Feature extraction configuration and settings"
    )
    performance_metrics = models.JSONField(
        default=dict,
        help_text="Accuracy, precision, recall, F1, confusion matrix, etc."
    )
    is_active = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Currently deployed/active model version"
    )
    training_samples_count = models.IntegerField(
        default=0,
        help_text="Number of samples used for training"
    )
    description = models.TextField(
        blank=True,
        help_text="Model description, notes, changes from previous version"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ml_models'
    )
    
    class Meta:
        ordering = ['-created_at']
        unique_together = [['model_name', 'model_version']]
        indexes = [
            models.Index(fields=['model_name', 'is_active']),
            models.Index(fields=['model_type', 'is_active']),
        ]
        verbose_name = 'ML Model'
        verbose_name_plural = 'ML Models'
    
    def __str__(self):
        status = "ACTIVE" if self.is_active else "inactive"
        return f"{self.model_name} v{self.model_version} ({status})"
    
    def save(self, *args, **kwargs):
        """
        Ensure only one model version is active per model_name
        """
        if self.is_active:
            # Deactivate other versions of this model
            MLModel.objects.filter(
                model_name=self.model_name,
                is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
    
    def get_accuracy(self):
        """Get accuracy metric if available"""
        return self.performance_metrics.get('accuracy', None)
    
    def get_f1_score(self):
        """Get F1 score if available"""
        return self.performance_metrics.get('f1_score', None)
    
    def delete(self, *args, **kwargs):
        """Delete model files when model is deleted"""
        if self.model_file:
            if os.path.isfile(self.model_file.path):
                os.remove(self.model_file.path)
        if self.vectorizer_file:
            if os.path.isfile(self.vectorizer_file.path):
                os.remove(self.vectorizer_file.path)
        super().delete(*args, **kwargs)


class TrainingDataset(models.Model):
    """
    Collection of training samples for a specific model.
    Supports multiple data sources and tracking.
    """
    DATA_SOURCE_CHOICES = [
        ('manual', 'Manual Selection'),
        ('user_feedback', 'User Feedback'),
        ('imported', 'Imported Dataset'),
        ('auto_labeled', 'Auto-Labeled'),
        ('active_learning', 'Active Learning'),
    ]
    
    dataset_name = models.CharField(
        max_length=200,
        help_text="Descriptive name for this dataset"
    )
    model_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Associated model name (e.g., 'email_daycare_classifier')"
    )
    data_source = models.CharField(
        max_length=20,
        choices=DATA_SOURCE_CHOICES,
        default='manual'
    )
    total_samples = models.IntegerField(
        default=0,
        help_text="Total number of samples in this dataset"
    )
    positive_samples = models.IntegerField(
        default=0,
        help_text="Number of positive class samples"
    )
    negative_samples = models.IntegerField(
        default=0,
        help_text="Number of negative class samples"
    )
    is_processed = models.BooleanField(
        default=False,
        help_text="Has this dataset been used for training"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='training_datasets'
    )
    notes = models.TextField(
        blank=True,
        help_text="Dataset notes, collection method, quality notes"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['model_name', 'is_processed']),
        ]
        verbose_name = 'Training Dataset'
        verbose_name_plural = 'Training Datasets'
    
    def __str__(self):
        return f"{self.dataset_name} ({self.total_samples} samples)"
    
    def update_counts(self):
        """Recalculate sample counts from related TrainingSamples"""
        samples = self.samples.all()
        self.total_samples = samples.count()
        self.positive_samples = samples.filter(
            label__in=['daycare_invoice', 'positive', 'yes', 'true', '1', 'daycare']
        ).count()
        self.negative_samples = samples.filter(
            label__in=['not_invoice', 'negative', 'no', 'false', '0', 'not_daycare']
        ).count()
        self.save()


class TrainingSample(models.Model):
    """
    Individual training sample with generic foreign key support.
    Can link to any Django model (EmailMessage, Document, etc.)
    """
    SOURCE_CHOICES = [
        ('manual', 'Manual Label'),
        ('ai_confirmed', 'AI Prediction Confirmed'),
        ('ai_rejected', 'AI Prediction Rejected'),
        ('imported', 'Imported'),
    ]
    
    dataset = models.ForeignKey(
        TrainingDataset,
        on_delete=models.CASCADE,
        related_name='samples'
    )
    sample_identifier = models.CharField(
        max_length=200,
        help_text="Human-readable identifier (e.g., email subject)"
    )
    
    # Generic Foreign Key to any model
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="Type of object this sample references"
    )
    object_id = models.PositiveIntegerField(
        help_text="ID of the referenced object"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    features = models.JSONField(
        default=dict,
        help_text="Extracted features for this sample"
    )
    label = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Ground truth label/classification"
    )
    confidence = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confidence if from AI prediction (0.0-1.0)"
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='manual'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_samples'
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about this sample"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['label', 'source']),
        ]
        verbose_name = 'Training Sample'
        verbose_name_plural = 'Training Samples'
    
    def __str__(self):
        return f"{self.sample_identifier} → {self.label}"
    
    def save(self, *args, **kwargs):
        """Update dataset counts when sample is saved"""
        super().save(*args, **kwargs)
        if self.dataset:
            self.dataset.update_counts()


class Prediction(models.Model):
    """
    AI prediction on any object with review/feedback tracking.
    Supports active learning workflow.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('confirmed', 'Confirmed by User'),
        ('rejected', 'Rejected by User'),
        ('ignored', 'Ignored'),
        ('auto_applied', 'Auto-Applied'),
    ]
    
    model = models.ForeignKey(
        MLModel,
        on_delete=models.CASCADE,
        related_name='predictions'
    )
    
    # Generic Foreign Key to any model
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="Type of object this prediction is for"
    )
    object_id = models.PositiveIntegerField(
        help_text="ID of the predicted object"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    predicted_label = models.CharField(
        max_length=50,
        db_index=True,
        help_text="AI-predicted classification"
    )
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Prediction confidence (0.0-1.0)"
    )
    all_predictions = models.JSONField(
        default=dict,
        help_text="All class probabilities {class: probability}"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    predicted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user reviewed this prediction"
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_predictions'
    )
    feedback_note = models.TextField(
        blank=True,
        help_text="User feedback or correction notes"
    )
    correct_label = models.CharField(
        max_length=50,
        blank=True,
        help_text="Correct label if prediction was rejected"
    )
    
    class Meta:
        ordering = ['-predicted_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['status', 'confidence_score']),
            models.Index(fields=['model', 'status']),
        ]
        verbose_name = 'AI Prediction'
        verbose_name_plural = 'AI Predictions'
    
    def __str__(self):
        return f"{self.predicted_label} ({self.confidence_score:.2%}) - {self.status}"
    
    def confirm(self, user=None):
        """User confirms prediction is correct"""
        self.status = 'confirmed'
        self.reviewed_at = timezone.now()
        self.reviewed_by = user
        self.save()
        
        # TODO: Optionally add to training dataset
        return True
    
    def reject(self, correct_label, user=None, note=''):
        """User rejects prediction and provides correct label"""
        self.status = 'rejected'
        self.correct_label = correct_label
        self.reviewed_at = timezone.now()
        self.reviewed_by = user
        self.feedback_note = note
        self.save()
        
        # TODO: Add corrected version to training dataset
        return True
    
    def get_confidence_level(self):
        """Return human-readable confidence level"""
        if self.confidence_score >= 0.9:
            return 'Very High'
        elif self.confidence_score >= 0.75:
            return 'High'
        elif self.confidence_score >= 0.6:
            return 'Medium'
        else:
            return 'Low'
