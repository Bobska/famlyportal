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
    AI Hub dashboard - overview of models and predictions.
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
    
    # Add email classification statistics
    total_emails = EmailMessage.objects.count()
    classified_emails = EmailMessage.objects.filter(is_classified=True).count()
    unclassified_emails = total_emails - classified_emails
    auto_confirmed = Prediction.objects.filter(status='auto_applied').count()
    
    stats['total_emails'] = total_emails
    stats['classified_emails'] = classified_emails
    stats['unclassified_emails'] = unclassified_emails
    stats['auto_confirmed_count'] = auto_confirmed
    
    context = {
        'page_title': 'Email Classification Review',
        'predictions': enriched_predictions,
        'stats': stats,
        'pending_count': predictions.count(),
    }
    
    return render(request, 'ai/email_review.html', context)


@login_required
def auto_confirmed_emails_view(request):
    """
    Review auto-confirmed email predictions for quality assurance.
    
    Shows emails that were automatically confirmed (≥95% confidence)
    with ability to flag incorrect predictions. This helps validate
    the auto-confirm threshold and catch errors early.
    """
    from gmail_integration.models import EmailMessage
    from ai.services.email_classification_service import EmailClassificationService
    from django.contrib.contenttypes.models import ContentType
    from django.core.paginator import Paginator
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    # Get auto-confirmed predictions
    email_ct = ContentType.objects.get_for_model(EmailMessage)
    predictions = Prediction.objects.filter(
        content_type=email_ct,
        status='auto_applied'
    ).select_related().order_by('-predicted_at')
    
    # Date range filter
    date_filter = request.GET.get('date_filter', '7')  # Default: last 7 days
    if date_filter == '7':
        start_date = timezone.now() - timedelta(days=7)
        predictions = predictions.filter(predicted_at__gte=start_date)
    elif date_filter == '30':
        start_date = timezone.now() - timedelta(days=30)
        predictions = predictions.filter(predicted_at__gte=start_date)
    elif date_filter == 'custom':
        start = request.GET.get('start_date')
        end = request.GET.get('end_date')
        if start:
            predictions = predictions.filter(predicted_at__gte=start)
        if end:
            predictions = predictions.filter(predicted_at__lte=end)
    
    # Confidence band filter
    confidence_band = request.GET.get('confidence_band', 'all')
    if confidence_band == '95-97':
        predictions = predictions.filter(confidence_score__gte=0.95, confidence_score__lt=0.97)
    elif confidence_band == '97-99':
        predictions = predictions.filter(confidence_score__gte=0.97, confidence_score__lt=0.99)
    elif confidence_band == '99-100':
        predictions = predictions.filter(confidence_score__gte=0.99)
    
    # Calculate metrics
    total_auto_confirmed = predictions.count()
    
    # Count corrections (training samples created recently)
    from ai.models import TrainingSample
    if predictions.exists():
        first_prediction_date = predictions.first().predicted_at
        correction_samples = TrainingSample.objects.filter(
            created_at__gte=first_prediction_date
        )
        corrections_count = correction_samples.count()
    else:
        corrections_count = 0
    
    # Calculate error rate
    error_rate = (corrections_count / total_auto_confirmed * 100) if total_auto_confirmed > 0 else 0
    
    # Calculate average confidence
    avg_confidence = predictions.aggregate(avg=models.Avg('confidence_score'))['avg'] or 0
    avg_confidence_percent = int(avg_confidence * 100) if avg_confidence else 0
    
    # Enrich predictions with email data
    enriched_predictions = []
    for pred in predictions[:100]:  # Limit to 100 for performance
        try:
            email = EmailMessage.objects.get(id=pred.object_id)
            enriched_predictions.append({
                'prediction': pred,
                'email': email,
                'confidence_percent': int(pred.confidence_score * 100),
                'predicted_label': pred.predicted_label,
            })
        except EmailMessage.DoesNotExist:
            continue
    
    # Pagination
    paginator = Paginator(enriched_predictions, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Auto-Confirmed Emails Review',
        'predictions': page_obj,
        'total_auto_confirmed': total_auto_confirmed,
        'corrections_count': corrections_count,
        'error_rate': round(error_rate, 2),
        'avg_confidence_percent': avg_confidence_percent,
        'date_filter': date_filter,
        'confidence_band': confidence_band,
    }
    
    return render(request, 'ai/auto_confirmed_review.html', context)


@login_required
@require_http_methods(["POST"])
def flag_auto_confirmed_view(request, prediction_id):
    """
    Flag an auto-confirmed prediction as incorrect and create a correction training sample.
    
    This helps identify errors in auto-confirmed decisions and feeds corrections
    back into the training pipeline.
    """
    from gmail_integration.models import EmailMessage
    from ai.services.email_classification_service import EmailClassificationService
    from django.contrib import messages
    import json
    
    try:
        prediction = get_object_or_404(Prediction, id=prediction_id, status='auto_applied')
        email = EmailMessage.objects.get(id=prediction.object_id)
        
        # Get the correct label from request
        data = json.loads(request.body)
        correct_label = data.get('correct_label')
        note = data.get('note', '')
        
        if not correct_label or correct_label not in ['INVOICE', 'NOT_INVOICE']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid label. Must be INVOICE or NOT_INVOICE.'
            }, status=400)
        
        # Create correction training sample
        is_daycare_invoice = (correct_label == 'INVOICE')
        EmailClassificationService.add_manual_training_sample(
            email_id=prediction.object_id,
            is_daycare_invoice=is_daycare_invoice,
            user=request.user
        )
        
        # Update the email's classification
        email.is_classified = True
        email.save()
        
        # Update prediction status to indicate it was corrected
        prediction.status = 'corrected'
        prediction.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Flagged as incorrect and added correction training sample.',
            'correct_label': correct_label
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error flagging auto-confirmed prediction {prediction_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


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
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"POST request received: action={action}, email_ids={email_ids}")
        
        if not email_ids:
            from django.contrib import messages
            messages.warning(request, "No emails selected. Please select at least one email to label.")
            return redirect('ai:manual_selection')
        
        if action in ['mark_invoice', 'mark_not_invoice']:
            is_invoice = (action == 'mark_invoice')
            success_count = 0
            error_count = 0
            
            for email_id in email_ids:
                try:
                    EmailClassificationService.add_manual_training_sample(
                        int(email_id),
                        is_invoice,
                        request.user
                    )
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error labeling email {email_id}: {e}")
            
            from django.contrib import messages
            if success_count > 0:
                label_type = "Daycare Invoices" if is_invoice else "NOT Invoices"
                messages.success(request, f"✅ Successfully labeled {success_count} email(s) as {label_type}")
            if error_count > 0:
                messages.error(request, f"❌ Failed to label {error_count} email(s)")
            
            return redirect('ai:manual_selection')
    
    # Get emails for display
    from django.contrib.contenttypes.models import ContentType
    from ai.models import TrainingSample
    
    # Get IDs of already-labeled emails
    email_content_type = ContentType.objects.get_for_model(EmailMessage)
    labeled_email_ids = TrainingSample.objects.filter(
        content_type=email_content_type
    ).values_list('object_id', flat=True)
    
    # Filter option: show labeled emails?
    show_labeled = request.GET.get('show_labeled', 'false') == 'true'
    
    if show_labeled:
        # Show only labeled emails
        emails = EmailMessage.objects.filter(id__in=labeled_email_ids).order_by('-sent_date')
    else:
        # Exclude labeled emails (default behavior)
        emails = EmailMessage.objects.exclude(id__in=labeled_email_ids).order_by('-sent_date')
    
    # Search filter
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
    
    # Enrich emails with their label information
    enriched_emails = []
    for email in page_obj:
        # Check if this email has been labeled and get its label
        email_samples = TrainingSample.objects.filter(
            content_type=email_content_type,
            object_id=email.id
        )
        
        label_info = None
        if email_samples.exists():
            latest_sample = email_samples.order_by('-created_at').first()
            label_info = {
                'label': latest_sample.label,
                'created_at': latest_sample.created_at,
                'created_by': latest_sample.created_by,
                'source': latest_sample.source,
                'is_invoice': latest_sample.label == 'daycare_invoice'
            }
        
        enriched_emails.append({
            'email': email,
            'label_info': label_info
        })
    
    # Get training statistics
    stats = EmailClassificationService.get_training_statistics()
    
    # Check if ready to train
    ready_to_train = stats['total_samples'] >= 20
    min_samples_needed = max(0, 20 - stats['total_samples'])
    
    # Count labeled vs unlabeled emails
    total_emails = EmailMessage.objects.count()
    labeled_count = len(labeled_email_ids)
    unlabeled_count = total_emails - labeled_count
    
    context = {
        'page_title': 'Manual Email Labeling',
        'enriched_emails': enriched_emails,
        'page_obj': page_obj,
        'stats': stats,
        'ready_to_train': ready_to_train,
        'min_samples_needed': min_samples_needed,
        'show_labeled': show_labeled,
        'labeled_count': labeled_count,
        'unlabeled_count': unlabeled_count,
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
        auto_confirmed_count = sum(1 for r in results if r.get('auto_confirmed', False))
        
        return JsonResponse({
            'success': True,
            'total': len(results),
            'success_count': success_count,
            'error_count': error_count,
            'auto_confirmed_count': auto_confirmed_count,
            'message': f'Classified {success_count} emails successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["GET"])
def classify_all_emails_sse_view(request):
    """Server-Sent Events endpoint for real-time classification progress."""
    from django.http import StreamingHttpResponse
    from ai.services.email_classification_service import EmailClassificationService
    from gmail_integration.models import EmailMessage
    import json
    import time
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("SSE classify_all_emails_sse_view called")
    
    def progress_generator():
        """Generator function that yields SSE-formatted progress updates."""
        logger.info("Starting SSE progress generator")
        try:
            # Send a test event immediately to verify connection
            test_event = {'phase': 'test', 'message': 'SSE connection established'}
            yield f"data: {json.dumps(test_event)}\n\n".encode('utf-8')
            logger.info("Sent test event")
            time.sleep(0.1)
            
            # Get total count first
            emails = EmailMessage.objects.filter(is_classified=False)
            total = emails.count()
            logger.info(f"Found {total} unclassified emails")
            
            # Send initial event
            yield f"data: {json.dumps({'phase': 'starting', 'progress': 0, 'total': total})}\n\n".encode('utf-8')
            logger.info(f"Sent starting event with total={total}")
            time.sleep(0.1)  # Small delay for UI to catch up
            
            # Counter for tracking
            processed = 0
            auto_confirmed = 0
            errors = 0
            
            # Process each email
            for email in emails:
                try:
                    # Classify the email
                    result = EmailClassificationService.classify_email(
                        email.id,
                        save_prediction=True
                    )
                    
                    # Auto-confirm if confidence is 95% or higher
                    if result.get('confidence', 0) >= 0.95:
                        prediction_id = result.get('prediction_id')
                        if prediction_id:
                            EmailClassificationService._auto_confirm_prediction(
                                prediction_id,
                                email.id
                            )
                            result['auto_confirmed'] = True
                            auto_confirmed += 1
                    
                    processed += 1
                    
                    # Calculate progress (30-95% range for classification phase)
                    progress = 30 + int((processed / total) * 65) if total > 0 else 95
                    
                    # Send progress update
                    progress_data = {
                        'phase': 'classifying',
                        'progress': progress,
                        'current': processed,
                        'total': total,
                        'email_id': email.id,
                        'email_subject': email.subject[:40] if email.subject else 'No subject',
                        'prediction': result.get('prediction'),
                        'confidence': result.get('confidence', 0),
                        'auto_confirmed': result.get('auto_confirmed', False),
                        'auto_confirmed_count': auto_confirmed,
                        'error_count': errors
                    }
                    yield f"data: {json.dumps(progress_data)}\n\n".encode('utf-8')
                    
                except Exception as e:
                    errors += 1
                    processed += 1
                    
                    progress = 30 + int((processed / total) * 65) if total > 0 else 95
                    
                    # Send error update
                    error_data = {
                        'phase': 'classifying',
                        'progress': progress,
                        'current': processed,
                        'total': total,
                        'email_id': email.id,
                        'error': str(e),
                        'error_count': errors
                    }
                    yield f"data: {json.dumps(error_data)}\n\n".encode('utf-8')
            
            # Send completion event
            complete_data = {
                'phase': 'complete',
                'progress': 100,
                'total': total,
                'processed': processed,
                'auto_confirmed_count': auto_confirmed,
                'error_count': errors
            }
            yield f"data: {json.dumps(complete_data)}\n\n".encode('utf-8')
            
        except Exception as e:
            # Send error event
            error_event = {'phase': 'error', 'error': str(e)}
            yield f"data: {json.dumps(error_event)}\n\n".encode('utf-8')
    
    response = StreamingHttpResponse(
        progress_generator(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


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


@login_required
@require_http_methods(["POST"])
def clear_pending_predictions(request):
    """AJAX endpoint to delete pending predictions for UNCLASSIFIED emails only."""
    try:
        from gmail_integration.models import EmailMessage
        from django.contrib.contenttypes.models import ContentType
        
        # Get ContentType for EmailMessage
        email_content_type = ContentType.objects.get_for_model(EmailMessage)
        
        # Get IDs of all unclassified emails
        unclassified_email_ids = EmailMessage.objects.filter(
            is_classified=False
        ).values_list('id', flat=True)
        
        # Delete only pending predictions for unclassified emails
        deleted_count, _ = Prediction.objects.filter(
            status='pending',
            content_type=email_content_type,
            object_id__in=unclassified_email_ids
        ).delete()
        
        return JsonResponse({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Successfully deleted {deleted_count} pending predictions for unclassified emails.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
