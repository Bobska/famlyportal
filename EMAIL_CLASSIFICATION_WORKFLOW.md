# Email Classification Workflow - Smart Classification System

## Overview
The email classification system now intelligently manages classified vs unclassified emails, prevents re-classification, and auto-confirms high-confidence predictions.

## Key Features

### 1. Classification Status Tracking
- **New Field**: `EmailMessage.is_classified` tracks whether an email has been classified
- **Classification Label**: `EmailMessage.classification_label` stores the final classification
- **Timestamp**: `EmailMessage.classified_at` records when classification occurred

### 2. Smart Classification
- **Only Unclassified**: `Classify Unclassified Emails` button only processes emails where `is_classified=False`
- **Prevents Re-classification**: Once an email is classified (confirmed/rejected), it won't be re-classified
- **Efficiency**: Avoids wasting compute on already-processed emails

### 3. Auto-Confirmation (100% Confidence)
- **Automatic Processing**: Predictions with confidence >= 1.0 (100%) are auto-confirmed
- **No Review Needed**: These skip the review page entirely
- **Training Data**: Auto-confirmed predictions create training samples immediately
- **Status**: Marked as `auto_applied` in Prediction model
- **Tracking**: Displayed in stats as "Auto-Confirmed" count

### 4. Selective Clearing
- **Smart Deletion**: `Clear Unclassified Predictions` only deletes predictions for unclassified emails
- **Preserves Classified**: Classified emails and their predictions remain untouched
- **Safe Re-classification**: Can safely clear and re-classify unclassified emails with improved models

## Workflow

### Initial Classification
```
1. Click "Classify Unclassified Emails"
   ├─> System finds all emails where is_classified=False
   ├─> Runs classifier on each unclassified email
   ├─> Creates Prediction records
   └─> Auto-confirms predictions >= 100% confidence
       ├─> Marks email.is_classified = True
       ├─> Sets email.classification_label
       ├─> Creates TrainingSample
       └─> Skips review page (status='auto_applied')

2. Review Predictions < 100%
   ├─> Pending predictions shown in review page
   ├─> User confirms (correct) or rejects (incorrect)
   └─> On confirm/reject:
       ├─> Marks email.is_classified = True
       ├─> Sets email.classification_label
       └─> Creates TrainingSample
```

### Re-classification with Improved Model
```
1. Train new model with more samples
2. Click "Clear Unclassified Predictions"
   ├─> Deletes predictions for is_classified=False emails only
   └─> Preserves all classified emails and their data

3. Click "Classify Unclassified Emails"
   ├─> Re-classifies only unclassified emails
   ├─> Uses improved model
   └─> Auto-confirms 100% predictions
```

## Database Schema Changes

### EmailMessage Model (gmail_integration)
```python
is_classified = BooleanField(default=False, db_index=True)
classification_label = CharField(max_length=50, blank=True)
classified_at = DateTimeField(null=True, blank=True)
```

### Migration
- **File**: `gmail_integration/migrations/0005_emailmessage_classification_label_and_more.py`
- **Changes**: Added 3 new fields to EmailMessage model

## API Changes

### EmailClassificationService

#### `classify_all_emails()`
**Before**: Classified ALL emails in database
**After**: Only classifies emails where `is_classified=False`
**New Behavior**: Auto-confirms predictions with confidence >= 1.0

#### `_auto_confirm_prediction(prediction_id, email_id)`
**New Method**: Handles auto-confirmation of 100% predictions
- Updates prediction status to 'auto_applied'
- Marks email as classified
- Creates training sample
- Logs auto-confirmation

#### `confirm_prediction(prediction_id, user)`
**Updated**: Now marks email as classified when user confirms
- Sets `email.is_classified = True`
- Sets `email.classification_label = prediction.predicted_label`
- Sets `email.classified_at = timezone.now()`

#### `reject_prediction(prediction_id, correct_label, user)`
**Updated**: Now marks email as classified with CORRECT label
- Sets `email.is_classified = True`
- Sets `email.classification_label = correct_label` (not predicted)
- Sets `email.classified_at = timezone.now()`

### Views

#### `clear_pending_predictions(request)`
**Before**: Deleted ALL pending predictions
**After**: Only deletes predictions for unclassified emails
- Filters by `content_type=EmailMessage`
- Filters by `object_id IN (unclassified_email_ids)`

#### `email_review_view(request)`
**Updated**: Added classification statistics
- `total_emails`: Total count
- `classified_emails`: Count where is_classified=True
- `unclassified_emails`: Total - classified
- `auto_confirmed_count`: Count of auto_applied predictions

## UI Changes

### Stats Dashboard
**New Columns**:
- **Total Emails**: Shows total/classified/unclassified breakdown
- **Auto-Confirmed**: Count of 100% predictions auto-confirmed
- **Visual Indicators**: Green for classified, yellow for unclassified

**Layout**: Changed from 4 columns to 5 columns (col-md-3 → col-md-2)

### Buttons
**Before**: "Classify All Emails"
**After**: "Classify Unclassified Emails"
- Tooltip: "X emails need classification"

**Before**: "Clear Pending Predictions"
**After**: "Clear Unclassified Predictions"
- Tooltip: "Remove X pending predictions (keeps classified)"

### Confirmation Messages
**Classification**:
- "Classify all UNCLASSIFIED emails? 100% confidence predictions will be auto-confirmed."

**Clear Predictions**:
- "Delete pending predictions for UNCLASSIFIED emails only? Classified emails will be preserved."

### Success Messages
**Classification**:
- "Success! Classified X unclassified emails. 100% predictions were auto-confirmed."

**Clear**:
- "Success! Deleted X predictions for unclassified emails. Classified emails preserved."

## Testing Checklist

### Test 1: Initial Classification
- [ ] Click "Classify Unclassified Emails"
- [ ] Verify 100% predictions auto-confirmed (don't appear in review)
- [ ] Verify <100% predictions appear in review page
- [ ] Check stats show correct auto-confirmed count
- [ ] Check classified email count increases

### Test 2: Confirm Prediction
- [ ] Click "Confirm" on a prediction
- [ ] Verify email.is_classified = True in database
- [ ] Verify email.classification_label set correctly
- [ ] Verify prediction status = 'confirmed'
- [ ] Verify TrainingSample created

### Test 3: Reject Prediction
- [ ] Click "Reject" on a prediction
- [ ] Verify email.is_classified = True
- [ ] Verify email.classification_label = correct_label (not predicted)
- [ ] Verify prediction.correct_label set
- [ ] Verify TrainingSample created with correct label

### Test 4: Re-classification Protection
- [ ] Classify all emails
- [ ] Confirm some predictions
- [ ] Click "Classify Unclassified Emails" again
- [ ] Verify only unclassified emails processed
- [ ] Verify classified emails NOT re-classified
- [ ] Check stats: classified count unchanged

### Test 5: Selective Clear
- [ ] Classify emails (some auto-confirmed, some pending)
- [ ] Click "Clear Unclassified Predictions"
- [ ] Verify only predictions for unclassified emails deleted
- [ ] Verify classified emails and their data preserved
- [ ] Check database: Prediction records for classified emails intact

### Test 6: Full Workflow
- [ ] Start with unclassified emails
- [ ] Classify → some auto-confirmed (100%)
- [ ] Review and confirm/reject remaining
- [ ] Train new model with more samples
- [ ] Clear unclassified predictions
- [ ] Re-classify unclassified with new model
- [ ] Verify classified emails untouched throughout

## Performance Benefits

1. **Reduced Compute**: Only classifies unclassified emails
2. **Faster Review**: 100% predictions skip review entirely
3. **Safe Iteration**: Can re-classify unclassified without losing work
4. **Better Training**: Auto-confirmed predictions build training data automatically

## Migration Notes

### Running Migration
```bash
python manage.py migrate gmail_integration
```

### Existing Data
- All existing emails will have `is_classified=False` by default
- First classification run will process all existing emails
- 100% predictions will be auto-confirmed immediately

## Troubleshooting

### Issue: All emails being re-classified
**Cause**: `is_classified` not set when confirming/rejecting
**Fix**: Verify confirm_prediction() and reject_prediction() set email.is_classified=True

### Issue: 100% predictions appearing in review
**Cause**: Auto-confirmation logic not working
**Fix**: Check `_auto_confirm_prediction()` is called in classify_all_emails()

### Issue: Clear deleting too many predictions
**Cause**: Not filtering by unclassified emails
**Fix**: Verify clear_pending_predictions() filters by unclassified_email_ids

---

**Created**: October 2, 2025
**Version**: 1.0
**Branch**: feature/email-classification
