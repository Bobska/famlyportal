"""
AI Hub Views
============

Test views for the AI hub - model management, testing, statistics.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import models
from ai.models import MLModel, TrainingDataset, TrainingSample, Prediction
from ai.services import TrainingService, PredictionService
from ai.utils import ModelManager


@login_required
def dashboard(request):
    """
    AI Hub dashboard - overview of models, datasets, and predictions.
    """
    # Model statistics
    active_models = MLModel.objects.filter(is_active=True)
    all_models = MLModel.objects.all()
    
    # Dataset statistics
    datasets = TrainingDataset.objects.all()
    total_samples = TrainingSample.objects.count()
    
    # Prediction statistics
    pending_predictions = Prediction.objects.filter(status='pending').count()
    total_predictions = Prediction.objects.count()
    
    # Model performance summary
    model_summaries = []
    for model in active_models:
        model_summaries.append({
            'name': model.model_name,
            'version': model.model_version,
            'accuracy': model.get_accuracy(),
            'f1_score': model.get_f1_score(),
            'training_samples': model.training_samples_count,
        })
    
    context = {
        'page_title': 'AI Hub Dashboard',
        'active_models_count': active_models.count(),
        'total_models_count': all_models.count(),
        'datasets_count': datasets.count(),
        'total_samples': total_samples,
        'pending_predictions': pending_predictions,
        'total_predictions': total_predictions,
        'model_summaries': model_summaries,
    }
    
    return render(request, 'ai/dashboard.html', context)


@login_required
def model_list(request):
    """
    List all ML models with filtering.
    """
    models = MLModel.objects.all().order_by('-created_at')
    
    # Filter by model name
    model_name = request.GET.get('model_name')
    if model_name:
        models = models.filter(model_name=model_name)
    
    # Filter by active status
    is_active = request.GET.get('is_active')
    if is_active == 'true':
        models = models.filter(is_active=True)
    elif is_active == 'false':
        models = models.filter(is_active=False)
    
    # Get unique model names for filter
    model_names = MLModel.objects.values_list('model_name', flat=True).distinct()
    
    context = {
        'page_title': 'ML Models',
        'models': models,
        'model_names': model_names,
        'current_filter': model_name,
    }
    
    return render(request, 'ai/model_list.html', context)


@login_required
def model_detail(request, model_id):
    """
    Detailed view of a single model with metrics and history.
    """
    model = get_object_or_404(MLModel, id=model_id)
    
    # Get other versions of this model
    other_versions = MLModel.objects.filter(
        model_name=model.model_name
    ).exclude(id=model_id).order_by('-created_at')
    
    # Get predictions made by this model
    recent_predictions = Prediction.objects.filter(
        model=model
    ).order_by('-predicted_at')[:10]
    
    context = {
        'page_title': f'Model: {model.model_name} v{model.model_version}',
        'model': model,
        'other_versions': other_versions,
        'recent_predictions': recent_predictions,
    }
    
    return render(request, 'ai/model_detail.html', context)


@login_required
def dataset_list(request):
    """
    List training datasets.
    """
    datasets = TrainingDataset.objects.all().order_by('-created_at')
    
    # Filter by model name
    model_name = request.GET.get('model_name')
    if model_name:
        datasets = datasets.filter(model_name=model_name)
    
    context = {
        'page_title': 'Training Datasets',
        'datasets': datasets,
    }
    
    return render(request, 'ai/dataset_list.html', context)


@login_required
def prediction_list(request):
    """
    List predictions with filtering.
    """
    predictions = Prediction.objects.all().order_by('-predicted_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        predictions = predictions.filter(status=status)
    
    # Filter by model
    model_name = request.GET.get('model_name')
    if model_name:
        predictions = predictions.filter(model__model_name=model_name)
    
    context = {
        'page_title': 'AI Predictions',
        'predictions': predictions[:100],  # Limit to 100 for performance
        'status_choices': Prediction.STATUS_CHOICES,
    }
    
    return render(request, 'ai/prediction_list.html', context)


@login_required
@require_http_methods(["POST"])
def confirm_prediction(request, prediction_id):
    """
    Confirm a prediction (AJAX endpoint).
    """
    try:
        PredictionService.confirm_prediction(
            prediction_id=prediction_id,
            user=request.user,
            add_to_training=True
        )
        return JsonResponse({'success': True, 'message': 'Prediction confirmed'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def reject_prediction(request, prediction_id):
    """
    Reject a prediction with correct label (AJAX endpoint).
    """
    correct_label = request.POST.get('correct_label')
    feedback_note = request.POST.get('feedback_note', '')
    
    if not correct_label:
        return JsonResponse({'success': False, 'error': 'Correct label required'}, status=400)
    
    try:
        PredictionService.reject_prediction(
            prediction_id=prediction_id,
            correct_label=correct_label,
            user=request.user,
            feedback_note=feedback_note,
            add_to_training=True
        )
        return JsonResponse({'success': True, 'message': 'Prediction rejected and corrected'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def activate_model(request, model_id):
    """
    Activate a model version (AJAX endpoint).
    """
    try:
        model = ModelManager.promote_model(model_id)
        return JsonResponse({
            'success': True, 
            'message': f'Activated {model.model_name} v{model.model_version}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def statistics(request):
    """
    AI Hub statistics and analytics.
    """
    # Model statistics
    model_stats = ModelManager.get_model_statistics()
    
    # Dataset statistics
    dataset_stats = TrainingService.get_dataset_statistics()
    
    # Prediction statistics (last 30 days)
    prediction_stats = PredictionService.get_prediction_statistics(days=30)
    
    context = {
        'page_title': 'AI Hub Statistics',
        'model_stats': model_stats,
        'dataset_stats': dataset_stats,
        'prediction_stats': prediction_stats,
    }
    
    return render(request, 'ai/statistics.html', context)


# ==========================
# EMAIL CLASSIFICATION VIEWS
# ==========================

@login_required
def email_review_view(request):
    """
    Review AI predictions for emails - confirm or reject.
    
    Shows pending predictions with options to confirm (correct)
    or reject (incorrect) each prediction. This is the active
    learning interface.
    """
    from gmail_integration.models import EmailMessage
    from ai.services.email_classification_service import EmailClassificationService
    from django.contrib.contenttypes.models import ContentType
    
    # Get pending predictions
    email_ct = ContentType.objects.get_for_model(EmailMessage)
    predictions = Prediction.objects.filter(
        content_type=email_ct,
        status='pending'
    ).order_by('-confidence_score', '-predicted_at')
    
    # Filter by confidence threshold if provided
    min_confidence = request.GET.get('min_confidence')
    max_confidence = request.GET.get('max_confidence')
    
    if min_confidence:
        predictions = predictions.filter(confidence_score__gte=float(min_confidence))
    if max_confidence:
        predictions = predictions.filter(confidence_score__lte=float(max_confidence))
    
    # Enrich predictions with email data
    enriched_predictions = []
    for pred in predictions[:50]:  # Limit to 50 for performance
        try:
            email = EmailMessage.objects.get(id=pred.object_id)
            enriched_predictions.append({
                'prediction': pred,
                'email': email,
                'confidence_percent': int(pred.confidence_score * 100),
                'confidence_class': EmailClassificationService._get_confidence_class(pred.confidence_score)
            })
        except EmailMessage.DoesNotExist:
            continue
    
    # Get training statistics
    stats = EmailClassificationService.get_training_statistics()
    
    context = {
        'page_title': 'Email Classification Review',
        'predictions': enriched_predictions,
        'stats': stats,
        'pending_count': predictions.count(),
    }
    
    return render(request, 'ai/email_review.html', context)


@login_required
def manual_selection_view(request):
    """
    Manual email labeling interface for building initial training data.
    
    Allows bulk selection and labeling of emails as daycare invoices
    or not invoices. This is the "cold start" interface.
    """
    from gmail_integration.models import EmailMessage
    from ai.services.email_classification_service import EmailClassificationService
    from django.core.paginator import Paginator
    
    # Handle bulk labeling POST request
    if request.method == 'POST':
        action = request.POST.get('action')
        email_ids = request.POST.getlist('email_ids')
        
        if action in ['mark_invoice', 'mark_not_invoice']:
            is_invoice = (action == 'mark_invoice')
            
            for email_id in email_ids:
                try:
                    EmailClassificationService.add_manual_training_sample(
                        int(email_id),
                        is_invoice,
                        request.user
                    )
                except Exception as e:
                    # Log error but continue with other emails
                    import logging
                    logging.getLogger(__name__).error(f"Error labeling email {email_id}: {e}")
            
            from django.contrib import messages
            messages.success(request, f"Labeled {len(email_ids)} emails successfully")
            
            return redirect('ai:manual_selection')
    
    # Get emails for display
    emails = EmailMessage.objects.all().order_by('-sent_date')
    
    # Filter options
    search = request.GET.get('search')
    if search:
        emails = emails.filter(
            models.Q(subject__icontains=search) |
            models.Q(sender_email__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(emails, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get training statistics
    stats = EmailClassificationService.get_training_statistics()
    
    # Check if ready to train
    ready_to_train = stats['total_samples'] >= 20
    min_samples_needed = max(0, 20 - stats['total_samples'])
    
    context = {
        'page_title': 'Manual Email Labeling',
        'page_obj': page_obj,
        'stats': stats,
        'ready_to_train': ready_to_train,
        'min_samples_needed': min_samples_needed,
    }
    
    return render(request, 'ai/manual_selection.html', context)


@login_required
def training_dashboard_view(request):
    """
    Model training dashboard - monitor training history and performance.
    
    Shows model versions, accuracy over time, sample distribution,
    and feature importance.
    """
    from ai.services.email_classification_service import EmailClassificationService
    
    # Get all model versions
    models = MLModel.objects.filter(
        model_name=EmailClassificationService.MODEL_NAME
    ).order_by('-created_at')
    
    # Get training statistics
    stats = EmailClassificationService.get_training_statistics()
    
    # Get training dataset info
    from ai.models import TrainingDataset
    dataset = TrainingDataset.objects.filter(
        model_name=EmailClassificationService.MODEL_NAME
    ).first()
    
    # Sample distribution data for chart
    chart_data = {
        'labels': ['Daycare Invoices', 'Not Invoices'],
        'data': [stats.get('positive_samples', 0), stats.get('negative_samples', 0)]
    }
    
    # Model accuracy history
    accuracy_history = []
    for model in models[:10]:  # Last 10 versions
        if model.performance_metrics:
            accuracy_history.append({
                'version': model.model_version,
                'accuracy': model.performance_metrics.get('accuracy', 0) * 100,
                'date': model.created_at
            })
    
    context = {
        'page_title': 'Training Dashboard',
        'models': models[:10],
        'current_model': models.first() if models.exists() else None,
        'stats': stats,
        'dataset': dataset,
        'chart_data': chart_data,
        'accuracy_history': accuracy_history,
    }
    
    return render(request, 'ai/training_dashboard.html', context)


# =========================
# EMAIL CLASSIFICATION AJAX
# =========================

@login_required
@require_http_methods(["POST"])
def confirm_email_prediction(request, prediction_id):
    """AJAX endpoint to confirm an email prediction."""
    from ai.services.email_classification_service import EmailClassificationService
    
    try:
        prediction = EmailClassificationService.confirm_prediction(
            prediction_id,
            request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Prediction confirmed and added to training data',
            'status': prediction.status
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def reject_email_prediction(request, prediction_id):
    """AJAX endpoint to reject an email prediction with correct label."""
    from ai.services.email_classification_service import EmailClassificationService
    import json
    
    try:
        data = json.loads(request.body)
        correct_label = data.get('correct_label')
        
        if not correct_label:
            return JsonResponse({
                'success': False,
                'error': 'correct_label is required'
            }, status=400)
        
        prediction = EmailClassificationService.reject_prediction(
            prediction_id,
            correct_label,
            request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Prediction rejected, correct label added to training',
            'status': prediction.status
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def classify_single_email(request, email_id):
    """AJAX endpoint to classify a single email."""
    from ai.services.email_classification_service import EmailClassificationService
    
    try:
        result = EmailClassificationService.classify_email(email_id, save_prediction=True)
        
        return JsonResponse({
            'success': True,
            'result': result
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def classify_all_emails_view(request):
    """AJAX endpoint to classify all emails in batch."""
    from ai.services.email_classification_service import EmailClassificationService
    
    try:
        results = EmailClassificationService.classify_all_emails()
        
        success_count = sum(1 for r in results if 'prediction' in r and r['prediction'])
        error_count = len(results) - success_count
        
        return JsonResponse({
            'success': True,
            'total': len(results),
            'success_count': success_count,
            'error_count': error_count,
            'message': f'Classified {success_count} emails successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def train_model_view(request):
    """AJAX endpoint to trigger model training."""
    from ai.services.email_classification_service import EmailClassificationService
    import json
    
    try:
        data = json.loads(request.body) if request.body else {}
        min_samples = data.get('min_samples', 10)
        
        result = EmailClassificationService.train_from_samples(
            min_samples=min_samples,
            user=request.user
        )
        
        return JsonResponse({
            'success': True,
            'result': result,
            'message': f'Model trained successfully. Version: {result["model_version"]}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
