# Email Classification System - Testing Guide

## Pre-Test Status ✅

### System Health Check
- ✅ Django checks: **PASS** (no issues found)
- ✅ Dependencies: scipy 1.15.3 installed
- ✅ Database: 2,872 emails available for classification
- ✅ Clean slate: 0 training samples, 0 predictions, 0 models

### Code Status
- ✅ All templates created and committed
- ✅ Bug fixes applied (field name corrected)
- ✅ Branch: `feature/email-classification`
- ✅ Remote: Pushed to GitHub

---

## Testing Workflow

### Phase 1: Manual Email Labeling (Cold Start)

**Objective**: Build initial training dataset by manually labeling emails

**Steps**:

1. **Start development server**:
   ```bash
   python manage.py runserver
   ```

2. **Navigate to manual selection page**:
   ```
   http://localhost:8000/ai/emails/manual-select/
   ```

3. **Label daycare invoices** (target: 10-15 emails):
   - Look for emails with subjects containing:
     - "Invoice", "Payment", "Tuition", "Bill", "Amount Due"
   - From daycare centers, preschools, childcare facilities
   - Often have PDF attachments
   - **Action**: Check boxes → Click "Mark as Daycare Invoices"

4. **Label non-invoices** (target: 10-15 emails):
   - Regular correspondence, newsletters, receipts from other vendors
   - Personal emails, marketing emails
   - **Action**: Check boxes → Click "Mark as NOT Invoices"

5. **Use search feature**:
   - Test search by sender or subject keywords
   - Verify pagination works (25 per page)

6. **Monitor progress widget**:
   - Watch "Total Training Samples" card update
   - Verify progress bar shows path to 20 samples
   - Check "Ready to Train" indicator activates

**Verification**:
```bash
# Check training samples created
python manage.py shell -c "from ai.models import TrainingSample; print(f'Samples: {TrainingSample.objects.count()}')"

# View sample distribution
python manage.py shell -c "from ai.models import TrainingSample; positive = TrainingSample.objects.filter(label='daycare_invoice').count(); negative = TrainingSample.objects.filter(label='not_invoice').count(); print(f'Invoices: {positive}, Not: {negative}')"
```

**Expected Results**:
- ✅ TrainingSample records created in database
- ✅ Progress widget shows accurate counts
- ✅ "Ready to Train" button enables when ≥20 samples
- ✅ UI updates in real-time after each action

---

### Phase 2: Initial Model Training

**Objective**: Train first RandomForest model with labeled samples

**Method A: UI Button** (Recommended):
1. On manual selection page, click "Train Initial Model"
2. Wait for training to complete (should take 5-10 seconds)
3. Alert should show success message with accuracy

**Method B: Management Command**:
```bash
python manage.py train_daycare_classifier --min-samples 10
```

**What Happens During Training**:
- Extracts 500 TF-IDF text features from subject + body
- Extracts 9 metadata binary features
- Trains RandomForest (100 trees, max_depth=10)
- Splits data 80/20 for training/testing
- Computes accuracy, precision, recall, F1-score
- Saves model to `ai/models/` directory as `.pkl` file
- Creates MLModel record (version 1.0.0)

**Verification**:
```bash
# Check model created
python manage.py shell -c "from ai.models import MLModel; m = MLModel.objects.filter(is_active=True).first(); print(f'Model v{m.version}: Accuracy={m.accuracy}%') if m else print('No model')"

# Check model file saved
ls ai/models/daycare_invoice_classifier_*.pkl
```

**Expected Results**:
- ✅ MLModel record created with version 1.0.0
- ✅ Model file saved to disk
- ✅ Accuracy metrics stored (typically 70-90% with 20 samples)
- ✅ `is_active=True` flag set
- ✅ Success message displayed

**Troubleshooting**:
- **Error: "Need at least 10 samples"** → Label more emails
- **Error: "Need samples of both classes"** → Ensure you have both invoice and non-invoice labels
- **Low accuracy (<60%)** → Normal with small dataset; will improve with more samples

---

### Phase 3: Batch Email Classification

**Objective**: Use trained model to classify all emails

**Method A: Management Command** (Recommended for first run):
```bash
# Classify all emails
python manage.py classify_emails --all

# Or just unclassified emails
python manage.py classify_emails --unclassified-only
```

**Method B: UI Button**:
1. Navigate to: `http://localhost:8000/ai/emails/review/`
2. Click "Classify All Emails" button
3. Wait for batch processing (may take 1-2 minutes for 2,872 emails)

**What Happens During Classification**:
- Loads active MLModel from database
- Loads model file (.pkl) from disk
- Prepares each email using EmailHelper
- Extracts features (text + metadata)
- Predicts label + confidence score
- Creates Prediction record (status='pending')
- Saves confidence scores for review

**Verification**:
```bash
# Check predictions created
python manage.py shell -c "from ai.models import Prediction; print(f'Total predictions: {Prediction.objects.count()}')"

# View confidence distribution
python manage.py shell -c "from ai.models import Prediction; from django.db.models import Avg, Min, Max; stats = Prediction.objects.aggregate(avg=Avg('confidence_score'), min=Min('confidence_score'), max=Max('confidence_score')); print(f\"Avg confidence: {stats['avg']:.2f}, Range: {stats['min']:.2f}-{stats['max']:.2f}\")"

# Count predicted invoices
python manage.py shell -c "from ai.models import Prediction; invoices = Prediction.objects.filter(predicted_label='daycare_invoice').count(); print(f'Predicted invoices: {invoices}')"
```

**Expected Results**:
- ✅ Prediction records created for all (or unclassified) emails
- ✅ Confidence scores between 0.0 and 1.0
- ✅ Mix of high and low confidence predictions
- ✅ Some emails predicted as invoices

**Performance Notes**:
- Classification speed: ~50-100 emails/second
- 2,872 emails should complete in 30-60 seconds
- Progress shown in terminal for management command

---

### Phase 4: Prediction Review & Feedback

**Objective**: Review AI predictions and provide corrective feedback

**Steps**:

1. **Navigate to review page**:
   ```
   http://localhost:8000/ai/emails/review/
   ```

2. **Review training statistics widget**:
   - Check current model accuracy
   - Verify version number (1.0.0)
   - Note sample count
   - Check retrain button

3. **Test confidence filters**:
   - Set "Min Confidence" to 0.8 (high confidence only)
   - Set "Max Confidence" to 0.6 (low confidence only)
   - Click "Apply Filters"
   - Verify predictions filtered correctly

4. **Review individual predictions**:
   - Check email subject, sender, date displayed
   - Verify AI prediction badge (green=invoice, gray=not)
   - Check confidence percentage color:
     - Green ≥80% (high confidence)
     - Yellow 60-80% (medium confidence)
     - Red <60% (low confidence)

5. **Test CONFIRM action** (AI was correct):
   - Find a correct prediction
   - Click "Confirm" button
   - Verify:
     - Row removed from table
     - Success alert appears
     - Training sample count increases

6. **Test REJECT action** (AI was wrong):
   - Find an incorrect prediction
   - Click "Reject" button
   - Modal appears asking for correct label
   - Select correct label
   - Click confirm
   - Verify:
     - Row removed from table
     - Success alert appears
     - Training sample count increases

7. **Test retrain button**:
   - Click "Retrain Model" button
   - Wait for training (5-10 seconds)
   - Verify:
     - Success alert with new accuracy
     - Model version increments (1.0.1)
     - Page reloads with updated stats

**Verification**:
```bash
# Check feedback samples added
python manage.py shell -c "from ai.models import TrainingSample; from django.utils import timezone; from datetime import timedelta; recent = TrainingSample.objects.filter(created_at__gte=timezone.now()-timedelta(minutes=10)).count(); print(f'Recent training samples: {recent}')"

# Check prediction status updates
python manage.py shell -c "from ai.models import Prediction; confirmed = Prediction.objects.filter(status='confirmed').count(); rejected = Prediction.objects.filter(status='rejected').count(); print(f'Confirmed: {confirmed}, Rejected: {rejected}')"
```

**Expected Results**:
- ✅ AJAX updates work without page reload
- ✅ Rows disappear after actions
- ✅ Training samples created from feedback
- ✅ Prediction statuses update correctly
- ✅ Alerts display success/error messages
- ✅ Manual retraining works

**UI/UX Checks**:
- Responsive design works on different screen sizes
- Confidence badges color-coded correctly
- Filter controls work smoothly
- No JavaScript console errors

---

### Phase 5: Automatic Retraining

**Objective**: Verify model automatically retrains after 20 new samples

**Steps**:

1. **Confirm/reject predictions until 20 total**:
   - Track your count (or check database)
   - The 20th confirmation/rejection should trigger auto-retraining

2. **Watch for auto-retrain**:
   - After 20th action, expect 5-10 second delay
   - Success alert should show: "Model automatically retrained!"
   - New model version created (e.g., 1.0.2 or 1.1.0)

3. **Verify version increment**:
   - Check training dashboard for new version
   - Verify accuracy potentially improved

**Configuration** (in `settings.py`):
```python
AI_EMAIL_CLASSIFIER = {
    'RETRAIN_THRESHOLD': 20,  # Auto-retrain after this many samples
    'MIN_TRAINING_SAMPLES': 10,
    'MIN_CONFIDENCE': 0.7,
}
```

**Verification**:
```bash
# Check model versions
python manage.py shell -c "from ai.models import MLModel; models = MLModel.objects.order_by('-created_at')[:3]; [print(f'v{m.version}: {m.accuracy}% - {m.trained_at}') for m in models]"

# Check training sample count
python manage.py shell -c "from ai.models import TrainingSample; print(f'Total samples: {TrainingSample.objects.count()}')"
```

**Expected Results**:
- ✅ Model automatically retrains after 20 samples
- ✅ New MLModel record created
- ✅ Version number increments
- ✅ Old model preserved (is_active=False)
- ✅ New model activated (is_active=True)
- ✅ Accuracy should improve or stay similar

**Versioning Logic**:
- Minor improvements: 1.0.0 → 1.0.1 → 1.0.2
- Major accuracy boost (>5%): 1.0.0 → 1.1.0
- (Customizable in `EmailClassificationService._increment_version()`)

---

### Phase 6: Training Dashboard

**Objective**: Verify monitoring and visualization features

**Steps**:

1. **Navigate to dashboard**:
   ```
   http://localhost:8000/ai/emails/training-dashboard/
   ```

2. **Check stat cards**:
   - Model Accuracy: Should show current active model accuracy
   - Training Samples: Total with invoice/not-invoice breakdown
   - Model Versions: Count of all MLModel records
   - Pending Feedback: Count of pending predictions

3. **Verify Chart.js visualizations**:
   
   **Accuracy Trend Chart** (Line chart):
   - X-axis: Model versions (v1.0.0, v1.0.1, etc.)
   - Y-axis: Accuracy percentage (0-100%)
   - Should show line going up over time (ideally)
   
   **Sample Distribution Chart** (Pie chart):
   - Green slice: Daycare invoices count
   - Gray slice: Not invoices count
   - Should be roughly balanced

4. **Check Top 10 Feature Importance**:
   - Visual bars showing which features matter most
   - Typical important features:
     - "invoice", "payment", "tuition" (text features)
     - "has_pdf_attachment" (metadata feature)
     - "sender_domain_edu" (daycare indicator)

5. **Review Model Version History table**:
   - Version numbers in order
   - Accuracy percentages
   - Training sample counts
   - Trained timestamps
   - Active model highlighted in green

6. **Check Recent Feedback list**:
   - Shows recent confirmations/rejections
   - Email subjects (truncated)
   - Confirmed (green badge) vs. Rejected (red badge)
   - Time since feedback ("5 minutes ago")

7. **Test advanced actions**:
   
   **Export Training Data**:
   - Click button
   - CSV file should download
   - Open and verify columns: email_id, subject, sender, label, created_at
   
   **Clear Old Predictions**:
   - Click button
   - Confirm dialog appears
   - Old predictions (>30 days) removed
   - Success alert shows count
   
   **Recompute Metrics**:
   - Click button
   - Recalculates accuracy for all models
   - Useful if you manually edited training data

8. **Test manual training button**:
   - Click "Train New Version"
   - Wait for training
   - Verify new version created
   - Check accuracy updated

**Verification**:
```bash
# Verify Chart.js loaded
# (Check browser console - should be no Chart.js errors)

# Check feature importance exists
python manage.py shell -c "from ai.services.email_classification_service import EmailClassificationService; service = EmailClassificationService(); fi = service.get_feature_importance(); print(f'Feature count: {len(fi)}') if fi else print('No features')"
```

**Expected Results**:
- ✅ All charts render correctly
- ✅ Stats accurate and real-time
- ✅ Version history complete
- ✅ Feature importance displays
- ✅ Recent feedback shows
- ✅ Advanced actions work
- ✅ No JavaScript errors in console

**Browser Compatibility**:
- Tested in Chrome/Edge (recommended)
- Should work in Firefox, Safari
- Chart.js loaded from CDN (requires internet)

---

## Complete Testing Checklist

### Functionality Tests
- [ ] Manual email labeling works (checkboxes, bulk actions)
- [ ] Search and pagination work
- [ ] Training progress indicator accurate
- [ ] Initial model training succeeds
- [ ] Batch email classification works
- [ ] Prediction review page displays correctly
- [ ] AJAX confirm action works
- [ ] AJAX reject action works
- [ ] Manual retrain button works
- [ ] Automatic retraining triggers at 20 samples
- [ ] Training dashboard displays all stats
- [ ] Chart.js visualizations render
- [ ] Feature importance shows
- [ ] Model version history accurate
- [ ] Export training data works
- [ ] Clear old predictions works
- [ ] Recompute metrics works

### Data Integrity Tests
- [ ] TrainingSample records created correctly
- [ ] Prediction records created correctly
- [ ] MLModel records versioned properly
- [ ] Old models preserved (not deleted)
- [ ] Active model flag manages correctly
- [ ] Confidence scores in valid range (0-1)
- [ ] Timestamps accurate

### UI/UX Tests
- [ ] Bootstrap 5 styling consistent
- [ ] Responsive design works on mobile
- [ ] Confidence badges color-coded correctly
- [ ] Alerts display properly
- [ ] Loading states show during AJAX
- [ ] Navigation between views works
- [ ] Back button works correctly
- [ ] No JavaScript console errors

### Performance Tests
- [ ] Classification speed acceptable (2,872 emails in <2 minutes)
- [ ] Training speed acceptable (<10 seconds for 20-50 samples)
- [ ] Page load times reasonable
- [ ] AJAX responses fast (<1 second)
- [ ] No memory leaks during long sessions

### Error Handling Tests
- [ ] Training with too few samples shows error
- [ ] Classification without model shows error
- [ ] Invalid confidence filters handled
- [ ] Network errors handled gracefully
- [ ] Database errors logged properly

---

## Common Issues & Solutions

### Issue: "No active model found"
**Cause**: Model hasn't been trained yet  
**Solution**: Go to manual selection page and train initial model

### Issue: Low accuracy (<60%)
**Cause**: Small training dataset  
**Solution**: Label more emails, aim for 50+ samples for better accuracy

### Issue: All predictions same label
**Cause**: Imbalanced training data (e.g., 18 invoices, 2 not invoices)  
**Solution**: Ensure balanced samples (roughly 50/50 split)

### Issue: Charts not rendering
**Cause**: Chart.js CDN blocked or internet issue  
**Solution**: Check browser console, verify internet connection

### Issue: AJAX actions not working
**Cause**: CSRF token issue  
**Solution**: Check browser console for CSRF errors, verify `getCookie()` function works

### Issue: Model file not found
**Cause**: Model file deleted or path incorrect  
**Solution**: Retrain model, check `ai/models/` directory exists

---

## Performance Expectations

### With 20-30 Training Samples
- **Accuracy**: 65-80%
- **Precision**: 60-85%
- **Recall**: 60-80%
- **Classification Speed**: 50-100 emails/second

### With 50-100 Training Samples
- **Accuracy**: 75-90%
- **Precision**: 75-90%
- **Recall**: 70-90%
- **Classification Speed**: Similar (feature extraction is bottleneck)

### With 200+ Training Samples
- **Accuracy**: 85-95%
- **Precision**: 85-95%
- **Recall**: 80-95%
- **Production Ready**: Yes

---

## Next Steps After Testing

### If Tests Pass ✅
1. **Commit any fixes** to `feature/email-classification`
2. **Update EMAIL_CLASSIFICATION_SUMMARY.md** with test results
3. **Create Pull Request** to merge into `develop`
4. **Deploy to staging** for real-world testing
5. **Monitor accuracy** over first week
6. **Gather user feedback** on UI/UX

### If Tests Fail ❌
1. **Document issues** in GitHub issue tracker
2. **Debug using Django logs** (`logs/django.log`)
3. **Check browser console** for JavaScript errors
4. **Fix bugs** and re-test
5. **Add unit tests** for fixed functionality

---

## Production Recommendations

### Before Going Live
- [ ] Add unit tests for classifier, service, views
- [ ] Add integration tests for full workflow
- [ ] Set up monitoring for model accuracy drift
- [ ] Configure email notifications for low accuracy
- [ ] Add admin interface for model management
- [ ] Implement model rollback functionality
- [ ] Add audit logging for predictions
- [ ] Set up scheduled retraining (weekly/monthly)

### Optimization Opportunities
- [ ] Tune RandomForest hyperparameters (n_estimators, max_depth)
- [ ] Increase TF-IDF features (500 → 1000)
- [ ] Add trigrams for better phrase detection
- [ ] Implement active learning selection (prioritize uncertain predictions)
- [ ] Add email text preprocessing (stemming, lemmatization)
- [ ] Cache feature extraction for speed
- [ ] Implement batch prediction API endpoint

### Monitoring Metrics
- Track daily: Accuracy, precision, recall
- Alert if accuracy drops below 70%
- Monitor prediction confidence distribution
- Track user feedback rate (confirms vs. rejects)
- Log feature importance changes over time

---

**Testing Date**: October 2, 2025  
**Tester**: _(Your name)_  
**Branch**: feature/email-classification  
**Commit**: 61eccf4  
**Status**: Ready for testing ✅
