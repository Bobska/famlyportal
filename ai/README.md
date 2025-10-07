# AI Hub - Centralised Machine Learning for FamlyPortal

## Overview

The AI Hub is a reusable Django app that provides a centralized system for managing machine learning models, training datasets, predictions, and active learning workflows across the entire FamlyPortal project.

### Key Features

- ✅ **Model Management**: Version control, activation, rollback, and comparison
- ✅ **Generic Training System**: Works with any Django model via ContentType
- ✅ **Active Learning**: User feedback loop for continuous improvement
- ✅ **Prediction Tracking**: Full audit trail of AI predictions and reviews
- ✅ **Reusable Architecture**: Easy to extend for new ML tasks
- ✅ **Admin Interface**: Comprehensive Django admin with custom actions
- ✅ **Performance Metrics**: Track accuracy, precision, recall, F1, etc.

---

## Installation & Setup

### 1. Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'ai',
    # ...
]
```

### 2. Add URL Configuration

```python
# urls.py
urlpatterns = [
    # ...
    path('ai/', include('ai.urls')),
    # ...
]
```

### 3. Install Dependencies

```bash
pip install scikit-learn>=1.3.0 pandas>=2.0.0 numpy>=1.24.0 joblib>=1.3.0
```

Or add to `requirements.txt`:
```
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
joblib>=1.3.0
```

### 4. Run Migrations

```bash
python manage.py makemigrations ai
python manage.py migrate ai
```

### 5. Configure Settings (Optional)

```python
# settings.py
AI_CONFIG = {
    'MODEL_STORAGE_PATH': 'ai/models/',
    'DEFAULT_CLASSIFIER': 'LogisticRegression',
    'RETRAIN_THRESHOLD': 20,  # New samples needed before retrain
    'MIN_CONFIDENCE': 0.7,  # Minimum confidence for auto-classification
}
```

---

## Core Models

### MLModel
Stores ML model metadata, files, and performance metrics.

**Key Fields:**
- `model_name`: Unique identifier (e.g., 'email_daycare_classifier')
- `model_version`: Semantic versioning (e.g., '1.0.0', '2.1.3')
- `model_file`: Pickled scikit-learn model
- `is_active`: Currently deployed model flag
- `performance_metrics`: JSON with accuracy, precision, recall, etc.

### TrainingDataset
Collection of training samples for a specific model.

**Key Fields:**
- `dataset_name`: Descriptive name
- `model_name`: Associated model
- `total_samples`, `positive_samples`, `negative_samples`: Statistics
- `is_processed`: Used for training flag

### TrainingSample
Individual training sample with generic foreign key.

**Key Fields:**
- `content_type` + `object_id`: GenericForeignKey to any model
- `label`: Ground truth classification
- `features`: Extracted features (JSON)
- `source`: 'manual', 'ai_confirmed', 'ai_rejected'

### Prediction
AI prediction on any object with review tracking.

**Key Fields:**
- `content_type` + `object_id`: GenericForeignKey
- `predicted_label`: AI classification
- `confidence_score`: 0.0-1.0
- `status`: 'pending', 'confirmed', 'rejected', 'auto_applied'
- `reviewed_by`: User who reviewed prediction

---

## Creating a New Classifier

### Step 1: Create Classifier Class

Create a new file in your app (e.g., `gmail_integration/classifiers.py`):

```python
from ai.services import BaseClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np


class DaycareEmailClassifier(BaseClassifier):
    """Classifier for detecting daycare-related emails"""
    
    def __init__(self):
        super().__init__(model_name='email_daycare_classifier')
        # Initialize your ML model
        self.model = LogisticRegression(max_iter=1000)
        self.vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
        
        # Feature configuration
        self.feature_config = {
            'vectorizer': 'TfidfVectorizer',
            'max_features': 1000,
            'ngram_range': (1, 2)
        }
    
    def extract_features(self, email_object):
        """Extract features from email object"""
        # Combine subject and body
        text = f"{email_object.subject or ''} {email_object.body_text or ''}"
        
        # First training: fit vectorizer
        if not hasattr(self.vectorizer, 'vocabulary_'):
            # This is during training, vectorizer will be fit in train()
            return text
        
        # Transform text to features
        features = self.vectorizer.transform([text]).toarray()[0]
        return features
    
    def train(self, training_data, labels, **kwargs):
        """Override train to fit vectorizer first"""
        # Extract text from all training samples
        texts = [self.extract_features(sample) for sample in training_data]
        
        # Fit vectorizer
        X = self.vectorizer.fit_transform(texts).toarray()
        y = np.array(labels)
        
        # Now train the model
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.model.fit(X_train, y_train)
        self.classes_ = self.model.classes_
        
        # Calculate metrics
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        y_pred = self.model.predict(X_test)
        
        metrics = {
            'accuracy': float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred, average='weighted')),
            'recall': float(recall_score(y_test, y_pred, average='weighted')),
            'f1_score': float(f1_score(y_test, y_pred, average='weighted')),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
        }
        
        self._last_metrics = metrics
        return metrics
```

### Step 2: Create Training Dataset

```python
from ai.services import TrainingService
from gmail_integration.models import EmailMessage

# Create dataset
dataset = TrainingService.create_dataset(
    name="Initial Daycare Emails",
    model_name="email_daycare_classifier",
    data_source='manual',
    user=request.user
)

# Add samples
samples = []
for email in EmailMessage.objects.filter(manually_labeled=True):
    samples.append({
        'content_object': email,
        'label': 'daycare' if email.is_daycare else 'not_daycare',
        'identifier': email.subject,
        'source': 'manual'
    })

TrainingService.add_samples_to_dataset(
    dataset_id=dataset.id,
    samples=samples,
    user=request.user
)
```

### Step 3: Train Model

```python
from gmail_integration.classifiers import DaycareEmailClassifier
from ai.services import TrainingService

# Initialize classifier
classifier = DaycareEmailClassifier()

# Get training data
data_list, labels_list = TrainingService.get_training_data(
    model_name='email_daycare_classifier',
    include_features=False
)

# Train
metrics = classifier.train(data_list, labels_list)
print(f"Accuracy: {metrics['accuracy']:.2%}")

# Save model
ml_model = classifier.save_model(
    version='1.0.0',
    description='Initial model trained on 100 manually labeled emails',
    user=request.user
)

# Activate model
from ai.utils import ModelManager
ModelManager.promote_model(ml_model.id)
```

### Step 4: Make Predictions

```python
from ai.services import PredictionService

# Single prediction
label, confidence, probabilities = PredictionService.predict(
    model_name='email_daycare_classifier',
    content_object=email,
    save_prediction=True
)

if confidence and confidence >= 0.75:
    print(f"Predicted: {label} ({confidence:.2%} confidence)")

# Batch predictions
new_emails = EmailMessage.objects.filter(needs_classification=True)
results = PredictionService.predict_batch(
    model_name='email_daycare_classifier',
    content_objects=list(new_emails),
    save_predictions=True,
    min_confidence=0.7
)
```

### Step 5: Handle User Feedback

```python
from ai.services import PredictionService

# User confirms prediction
PredictionService.confirm_prediction(
    prediction_id=prediction.id,
    user=request.user,
    add_to_training=True  # Adds to training dataset
)

# User rejects and corrects prediction
PredictionService.reject_prediction(
    prediction_id=prediction.id,
    correct_label='daycare',
    user=request.user,
    feedback_note='This is clearly from the daycare',
    add_to_training=True  # Adds corrected version to training data
)
```

---

## Management Commands

### Train Model

```bash
# Train with specific dataset
python manage.py train_model email_daycare_classifier --dataset 1 --version 1.0.0

# Train with all available data
python manage.py train_model email_daycare_classifier --version 2.0.0

# Activate after training
python manage.py train_model email_daycare_classifier --dataset 1 --version 1.1.0 --activate

# Check if retraining is needed
python manage.py train_model email_daycare_classifier --check-only
```

---

## API Reference

### Training Service

```python
from ai.services import TrainingService

# Create dataset
dataset = TrainingService.create_dataset(name, model_name, data_source, user)

# Add samples
count = TrainingService.add_samples_to_dataset(dataset_id, samples, user)

# Get training data
data_list, labels_list = TrainingService.get_training_data(dataset_id, model_name)

# Trigger training
result = TrainingService.trigger_training(model_name, dataset_id, version, user)

# Check if retraining needed
should_retrain, new_samples, reason = TrainingService.should_retrain(model_name, threshold=20)

# Get statistics
stats = TrainingService.get_dataset_statistics(model_name)
```

### Prediction Service

```python
from ai.services import PredictionService

# Single prediction
label, confidence, probs = PredictionService.predict(model_name, content_object, save_prediction=True)

# Batch prediction
results = PredictionService.predict_batch(model_name, content_objects, save_predictions=True)

# Get pending predictions
pending = PredictionService.get_pending_predictions(model_name, min_confidence=0.6)

# Confirm prediction
PredictionService.confirm_prediction(prediction_id, user, add_to_training=True)

# Reject prediction
PredictionService.reject_prediction(prediction_id, correct_label, user, feedback_note)

# Get statistics
stats = PredictionService.get_prediction_statistics(model_name, days=30)
```

### Model Manager

```python
from ai.utils import ModelManager

# Get active model
model = ModelManager.get_active_model(model_name)

# Get all versions
versions = ModelManager.get_all_versions(model_name)

# Promote model to active
model = ModelManager.promote_model(model_id)

# Rollback to previous version
previous = ModelManager.rollback_model(model_name)

# Compare two models
comparison = ModelManager.compare_models(model_id1, model_id2)

# Get model history
history = ModelManager.get_model_history(model_name)

# Get best performing model
best = ModelManager.get_best_model(model_name, metric='f1_score')

# Delete old versions
count = ModelManager.delete_old_versions(model_name, keep_count=3)

# Get statistics
stats = ModelManager.get_model_statistics()
```

### Feature Extractor

```python
from ai.utils import FeatureExtractor

# Extract text features
features = FeatureExtractor.extract_text_features(text, config)

# Extract metadata features
features = FeatureExtractor.extract_metadata_features(metadata_dict)

# Combine features
combined = FeatureExtractor.combine_features(text_features, metadata_features)

# Extract keyword features
keyword_features = FeatureExtractor.extract_keyword_features(text, keywords)

# Extract email-specific features
email_features = FeatureExtractor.extract_email_features(email_object)

# Get text statistics
stats = FeatureExtractor.get_text_statistics(text)
```

---

## Admin Interface

The AI Hub provides a comprehensive Django admin interface:

### MLModel Admin
- List view with active status badges and accuracy display
- Performance metrics pretty display
- Actions: Activate, Deactivate models
- Feature configuration viewer

### TrainingDataset Admin
- Sample distribution visualization
- Actions: Mark as processed, Update counts
- Filter by model name and data source

### TrainingSample Admin
- Link to source objects
- Features display
- Filter by label and source

### Prediction Admin
- Confidence and status badges
- Class probability visualization
- Actions: Confirm, Reject predictions
- Filter by status and model

---

## Testing Views

Access the AI Hub dashboard:
```
http://localhost:8000/ai/
```

Available views:
- `/ai/` - Dashboard with statistics
- `/ai/models/` - List all models
- `/ai/models/<id>/` - Model detail
- `/ai/datasets/` - List datasets
- `/ai/predictions/` - List predictions
- `/ai/statistics/` - Analytics and statistics

---

## Best Practices

### 1. Model Versioning
Use semantic versioning (MAJOR.MINOR.PATCH):
- MAJOR: Incompatible changes, new feature extraction
- MINOR: New training data, performance improvements
- PATCH: Bug fixes, minor adjustments

### 2. Training Data Quality
- Aim for balanced datasets (similar positive/negative samples)
- Minimum 50-100 samples for initial training
- Add 20+ samples before retraining

### 3. Confidence Thresholds
- High confidence (>0.9): Auto-apply predictions
- Medium confidence (0.7-0.9): Request user review
- Low confidence (<0.7): Don't apply, use for manual review only

### 4. Active Learning Workflow
1. Start with manually labeled data
2. Train initial model
3. Make predictions on new data
4. Users review and correct predictions
5. Corrected predictions added to training data
6. Retrain when threshold reached
7. Repeat

### 5. Model Evaluation
- Always split data (80% train, 20% test)
- Monitor multiple metrics (accuracy, precision, recall, F1)
- Compare new models with previous versions before activation
- Keep rollback capability (don't delete old versions immediately)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         AI Hub                               │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   MLModel    │  │Training      │  │  Prediction  │     │
│  │              │  │Dataset       │  │              │     │
│  │ - Version    │  │              │  │ - Status     │     │
│  │ - Metrics    │  │ - Samples    │  │ - Confidence │     │
│  │ - Active     │  │ - Processed  │  │ - Review     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Services Layer                         │    │
│  │  - TrainingService                                  │    │
│  │  - PredictionService                                │    │
│  │  - BaseClassifier (Abstract)                        │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Utilities Layer                        │    │
│  │  - ModelManager                                     │    │
│  │  - FeatureExtractor                                 │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
                   GenericForeignKey
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Your Django Apps                          │
│                                                              │
│  EmailMessage  │  Document  │  Transaction  │  Any Model    │
└─────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Issue: "No active model found"
**Solution:** Activate a model using Admin or ModelManager.promote_model()

### Issue: "Not enough training samples"
**Solution:** Add more training samples (minimum 10, recommended 50+)

### Issue: "Model not loaded"
**Solution:** Call classifier.load_model() before making predictions

### Issue: "Features shape mismatch"
**Solution:** Ensure vectorizer is fitted during training and saved with model

---

## Contributing

To extend the AI Hub:

1. Create new classifier by extending `BaseClassifier`
2. Implement `extract_features()` method
3. Add to your app's classifiers.py
4. Follow training workflow documentation

---

## License

Part of FamlyPortal project - Internal use only.

---

## Support

For issues or questions:
- Check this README
- Review example classifiers
- Check Django admin interface
- Review code comments
