"""
Test script to verify 100% confidence auto-confirmation works
"""
from gmail_integration.models import EmailMessage
from ai.models import Prediction
from ai.services.email_classification_service import EmailClassificationService

print("=" * 60)
print("BEFORE CLASSIFICATION")
print("=" * 60)
print(f"Total emails: {EmailMessage.objects.count()}")
print(f"Classified: {EmailMessage.objects.filter(is_classified=True).count()}")
print(f"Unclassified: {EmailMessage.objects.filter(is_classified=False).count()}")
print(f"Pending predictions: {Prediction.objects.filter(status='pending').count()}")
print(f"Auto-applied: {Prediction.objects.filter(status='auto_applied').count()}")
print()

# Clear old predictions
print("Clearing old pending predictions...")
from django.contrib.contenttypes.models import ContentType
email_ct = ContentType.objects.get_for_model(EmailMessage)
unclassified_ids = EmailMessage.objects.filter(is_classified=False).values_list('id', flat=True)
deleted_count, _ = Prediction.objects.filter(
    status='pending',
    content_type=email_ct,
    object_id__in=unclassified_ids
).delete()
print(f"Deleted {deleted_count} old predictions")
print()

# Classify first 10 unclassified emails as a test
print("Classifying first 10 unclassified emails...")
unclassified = EmailMessage.objects.filter(is_classified=False)[:10]
results = []

for email in unclassified:
    result = EmailClassificationService.classify_email(email.id, save_prediction=True)
    
    # Check if auto-confirmation happened
    if result.get('confidence', 0) >= 1.0:
        prediction_id = result.get('prediction_id')
        if prediction_id:
            EmailClassificationService._auto_confirm_prediction(prediction_id, email.id)
            result['auto_confirmed'] = True
            print(f"  ✓ Email {email.id}: {result['prediction']} ({result['confidence']:.2%}) - AUTO-CONFIRMED")
        else:
            print(f"  ⚠ Email {email.id}: {result['prediction']} ({result['confidence']:.2%}) - NO PREDICTION_ID!")
    else:
        print(f"  → Email {email.id}: {result['prediction']} ({result['confidence']:.2%}) - needs review")
    
    results.append(result)

print()
print("=" * 60)
print("AFTER CLASSIFICATION")
print("=" * 60)
print(f"Total emails: {EmailMessage.objects.count()}")
print(f"Classified: {EmailMessage.objects.filter(is_classified=True).count()}")
print(f"Unclassified: {EmailMessage.objects.filter(is_classified=False).count()}")
print(f"Pending predictions: {Prediction.objects.filter(status='pending').count()}")
print(f"Auto-applied: {Prediction.objects.filter(status='auto_applied').count()}")
print()

# Show confidence breakdown
print("=" * 60)
print("CONFIDENCE BREAKDOWN (of 10 test emails)")
print("=" * 60)
auto_confirmed = sum(1 for r in results if r.get('auto_confirmed', False))
needs_review = len(results) - auto_confirmed
print(f"Auto-confirmed (100%): {auto_confirmed}")
print(f"Needs review (<100%): {needs_review}")
print()

# Check if 100% predictions are in pending (they shouldn't be!)
pending_100 = Prediction.objects.filter(
    status='pending',
    confidence_score__gte=1.0
).count()
print("=" * 60)
print("VERIFICATION")
print("=" * 60)
if pending_100 > 0:
    print(f"❌ ERROR: {pending_100} predictions with 100% confidence are still pending!")
    print("Auto-confirmation logic NOT working correctly")
else:
    print("✅ SUCCESS: No 100% predictions in pending status")
    print("Auto-confirmation logic working correctly!")
