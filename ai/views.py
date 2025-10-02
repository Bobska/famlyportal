"""
AI Hub Views
============

Test views for the AI hub - model management, testing, statistics.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
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
