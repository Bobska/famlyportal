"""
AI Hub Admin Interface
======================

Django admin configuration for AI models, datasets, and predictions.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from ai.models import MLModel, TrainingDataset, TrainingSample, Prediction
import json


@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    """Admin interface for ML Models"""
    
    list_display = [
        'model_name', 'model_version', 'model_type', 'is_active_badge',
        'accuracy_display', 'training_samples_count', 'created_at', 'created_by'
    ]
    list_filter = ['model_type', 'is_active', 'created_at']
    search_fields = ['model_name', 'model_version', 'description']
    readonly_fields = ['created_at', 'performance_metrics_display', 'feature_config_display']
    
    fieldsets = (
        ('Model Information', {
            'fields': ('model_name', 'model_version', 'model_type', 'description')
        }),
        ('Files', {
            'fields': ('model_file', 'vectorizer_file')
        }),
        ('Configuration', {
            'fields': ('feature_config_display', 'is_active')
        }),
        ('Performance', {
            'fields': ('performance_metrics_display', 'training_samples_count')
        }),
        ('Metadata', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_model', 'deactivate_model', 'compare_with_active']
    
    def is_active_badge(self, obj):
        """Display active status as badge"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">ACTIVE</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; border-radius: 3px;">inactive</span>'
        )
    is_active_badge.short_description = 'Status'
    
    def accuracy_display(self, obj):
        """Display accuracy metric"""
        accuracy = obj.get_accuracy()
        if accuracy is not None:
            return f"{accuracy:.2%}"
        return "—"
    accuracy_display.short_description = 'Accuracy'
    
    def performance_metrics_display(self, obj):
        """Pretty display of performance metrics"""
        if not obj.performance_metrics:
            return "No metrics available"
        
        metrics_html = "<table style='width: 100%; border-collapse: collapse;'>"
        for key, value in obj.performance_metrics.items():
            if key not in ['confusion_matrix', 'classification_report']:
                metrics_html += f"<tr><td style='padding: 5px; border: 1px solid #ddd;'><strong>{key}:</strong></td>"
                metrics_html += f"<td style='padding: 5px; border: 1px solid #ddd;'>{value}</td></tr>"
        metrics_html += "</table>"
        
        return mark_safe(metrics_html)
    performance_metrics_display.short_description = 'Performance Metrics'
    
    def feature_config_display(self, obj):
        """Pretty display of feature config"""
        if not obj.feature_config:
            return "No configuration"
        return mark_safe(f"<pre>{json.dumps(obj.feature_config, indent=2)}</pre>")
    feature_config_display.short_description = 'Feature Configuration'
    
    def activate_model(self, request, queryset):
        """Admin action to activate selected model"""
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one model to activate.", level='error')
            return
        
        model = queryset.first()
        from ai.utils.model_management import ModelManager
        ModelManager.promote_model(model.id)
        self.message_user(request, f"Activated model: {model}")
    activate_model.short_description = "Activate selected model (promote to production)"
    
    def deactivate_model(self, request, queryset):
        """Admin action to deactivate models"""
        count = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {count} model(s)")
    deactivate_model.short_description = "Deactivate selected models"


@admin.register(TrainingDataset)
class TrainingDatasetAdmin(admin.ModelAdmin):
    """Admin interface for Training Datasets"""
    
    list_display = [
        'dataset_name', 'model_name', 'data_source', 'total_samples',
        'positive_samples', 'negative_samples', 'is_processed', 'created_at'
    ]
    list_filter = ['model_name', 'data_source', 'is_processed', 'created_at']
    search_fields = ['dataset_name', 'model_name', 'notes']
    readonly_fields = ['created_at', 'sample_distribution_display']
    
    fieldsets = (
        ('Dataset Information', {
            'fields': ('dataset_name', 'model_name', 'data_source', 'notes')
        }),
        ('Statistics', {
            'fields': ('total_samples', 'positive_samples', 'negative_samples', 
                      'sample_distribution_display', 'is_processed')
        }),
        ('Metadata', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_processed', 'update_sample_counts']
    
    def sample_distribution_display(self, obj):
        """Visual display of sample distribution"""
        if obj.total_samples == 0:
            return "No samples"
        
        pos_pct = (obj.positive_samples / obj.total_samples) * 100
        neg_pct = (obj.negative_samples / obj.total_samples) * 100
        
        html = f"""
        <div style='width: 100%; background-color: #f8f9fa; padding: 10px; border-radius: 5px;'>
            <div style='margin-bottom: 5px;'>
                <strong>Positive:</strong> {obj.positive_samples} ({pos_pct:.1f}%)
            </div>
            <div style='width: 100%; background-color: #ddd; height: 20px; border-radius: 3px; overflow: hidden;'>
                <div style='width: {pos_pct}%; background-color: #28a745; height: 100%; float: left;'></div>
            </div>
            <div style='margin-top: 10px; margin-bottom: 5px;'>
                <strong>Negative:</strong> {obj.negative_samples} ({neg_pct:.1f}%)
            </div>
            <div style='width: 100%; background-color: #ddd; height: 20px; border-radius: 3px; overflow: hidden;'>
                <div style='width: {neg_pct}%; background-color: #dc3545; height: 100%; float: left;'></div>
            </div>
        </div>
        """
        return mark_safe(html)
    sample_distribution_display.short_description = 'Sample Distribution'
    
    def mark_as_processed(self, request, queryset):
        """Mark datasets as processed"""
        count = queryset.update(is_processed=True)
        self.message_user(request, f"Marked {count} dataset(s) as processed")
    mark_as_processed.short_description = "Mark as processed"
    
    def update_sample_counts(self, request, queryset):
        """Recalculate sample counts"""
        for dataset in queryset:
            dataset.update_counts()
        self.message_user(request, f"Updated counts for {queryset.count()} dataset(s)")
    update_sample_counts.short_description = "Update sample counts"


@admin.register(TrainingSample)
class TrainingSampleAdmin(admin.ModelAdmin):
    """Admin interface for Training Samples"""
    
    list_display = [
        'sample_identifier', 'dataset', 'label', 'source', 
        'confidence', 'created_at', 'created_by'
    ]
    list_filter = ['label', 'source', 'dataset__model_name', 'created_at']
    search_fields = ['sample_identifier', 'label', 'notes']
    readonly_fields = ['created_at', 'content_type', 'object_id', 'features_display']
    
    fieldsets = (
        ('Sample Information', {
            'fields': ('dataset', 'sample_identifier', 'label', 'source')
        }),
        ('Linked Object', {
            'fields': ('content_type', 'object_id')
        }),
        ('Features', {
            'fields': ('features_display', 'confidence')
        }),
        ('Metadata', {
            'fields': ('notes', 'created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def features_display(self, obj):
        """Pretty display of features"""
        if not obj.features:
            return "No features extracted"
        return mark_safe(f"<pre>{json.dumps(obj.features, indent=2)}</pre>")
    features_display.short_description = 'Extracted Features'


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    """Admin interface for Predictions"""
    
    list_display = [
        'predicted_label', 'confidence_badge', 'status_badge',
        'model', 'predicted_at', 'reviewed_by'
    ]
    list_filter = ['status', 'predicted_label', 'model__model_name', 'predicted_at']
    search_fields = ['predicted_label', 'feedback_note']
    readonly_fields = [
        'predicted_at', 'model', 'content_type', 'object_id',
        'predicted_label', 'confidence_score', 'all_predictions_display'
    ]
    
    fieldsets = (
        ('Prediction Details', {
            'fields': ('model', 'predicted_label', 'confidence_score', 
                      'all_predictions_display', 'predicted_at')
        }),
        ('Linked Object', {
            'fields': ('content_type', 'object_id')
        }),
        ('Review Status', {
            'fields': ('status', 'correct_label', 'feedback_note', 
                      'reviewed_at', 'reviewed_by')
        }),
    )
    
    actions = ['confirm_predictions', 'mark_as_pending']
    
    def confidence_badge(self, obj):
        """Display confidence as colored badge"""
        confidence_pct = obj.confidence_score * 100
        
        if obj.confidence_score >= 0.9:
            color = '#28a745'  # Green
        elif obj.confidence_score >= 0.75:
            color = '#007bff'  # Blue
        elif obj.confidence_score >= 0.6:
            color = '#ffc107'  # Yellow
        else:
            color = '#dc3545'  # Red
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{:.1f}%</span>',
            color, confidence_pct
        )
    confidence_badge.short_description = 'Confidence'
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'pending': '#ffc107',
            'confirmed': '#28a745',
            'rejected': '#dc3545',
            'ignored': '#6c757d',
            'auto_applied': '#17a2b8',
        }
        color = colors.get(obj.status, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    def all_predictions_display(self, obj):
        """Display all class probabilities"""
        if not obj.all_predictions:
            return "No probabilities available"
        
        html = "<table style='width: 100%;'>"
        sorted_predictions = sorted(
            obj.all_predictions.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        for label, prob in sorted_predictions:
            prob_pct = prob * 100
            html += f"""
            <tr>
                <td style='padding: 5px;'><strong>{label}:</strong></td>
                <td style='padding: 5px;'>{prob_pct:.1f}%</td>
                <td style='padding: 5px;'>
                    <div style='width: 200px; background-color: #ddd; height: 15px;'>
                        <div style='width: {prob_pct}%; background-color: #007bff; height: 100%;'></div>
                    </div>
                </td>
            </tr>
            """
        html += "</table>"
        return mark_safe(html)
    all_predictions_display.short_description = 'Class Probabilities'
    
    def confirm_predictions(self, request, queryset):
        """Bulk confirm predictions"""
        count = 0
        for prediction in queryset:
            if prediction.status == 'pending':
                prediction.confirm(user=request.user)
                count += 1
        self.message_user(request, f"Confirmed {count} prediction(s)")
    confirm_predictions.short_description = "Confirm selected predictions"
    
    def mark_as_pending(self, request, queryset):
        """Reset predictions to pending"""
        count = queryset.update(status='pending', reviewed_at=None, reviewed_by=None)
        self.message_user(request, f"Reset {count} prediction(s) to pending")
    mark_as_pending.short_description = "Mark as pending (reset review)"


# Customize admin site header
admin.site.site_header = "FamlyPortal AI Hub Administration"
admin.site.site_title = "AI Hub Admin"
admin.site.index_title = "AI & Machine Learning Management"
