# AI Invoice Learning System Documentation

## Overview
The FamlyPortal AI system learns invoice patterns from user feedback **without hard-coding every format**. This allows it to adapt to new daycare providers automatically.

## How AI Learns Invoice Structures

### 1. Initial Extraction (Rule-Based)
When an email arrives, the system uses flexible regex patterns to extract:
- Provider name
- Invoice number
- Reference number (child ID)
- Issue date
- Due date (or calculates as issue_date + 7 days)
- **Line items breakdown** (debits, credits, discounts, previous balance)
- Current invoice total (new charges only)
- Amount due (including previous balance)

### 2. User Verification (Training Data)
When you verify an extraction:
- Creates a `TrainingSample` with the correct values
- Stores the raw email text + PDF text
- Stores all extracted fields including line items structure
- Labels it as 'invoice' for classification

### 3. Machine Learning (Future)
After 20-30 verified samples:
- Train ML model on verified extractions
- Learn patterns: "Where providers put invoice numbers", "How discounts are formatted", etc.
- Auto-extract from **new providers** without manual rules
- Confidence scoring: Low = human review, High = auto-create invoice

## Example: Active Explorers Invoice

### Invoice Structure
```
Previous Balance           $160.88
1. Under 3 Fee            $331.50  (debit)
2. Fee Discount (75%)    -$248.63  (discount)
─────────────────────────────────
Current Invoice Total      $82.87  (new charges only)
Amount Due                $243.75  (inc. previous balance)
```

### What Gets Stored
```json
{
  "provider_name": "Active Explorers Ashburton",
  "invoice_number": "7896993",
  "reference_number": "SG300",
  "issue_date": "2025-09-29",
  "due_date": "2025-10-06",
  "current_invoice_total": 82.87,
  "amount": 243.75,
  "line_items": [
    {"type": "previous_balance", "description": "Previous Balance", "amount": 160.88},
    {"type": "debit", "description": "Under 3 Fee May 2025...", "amount": 331.50},
    {"type": "discount", "description": "Fee Discount of 75.00%", "amount": -248.63}
  ]
}
```

## Key Differences: Current Invoice vs Amount Due

| Field | What It Means | Active Explorers Example |
|-------|---------------|--------------------------|
| **current_invoice_total** | New charges this period (fees - discounts) | $82.87 |
| **amount** | What you owe NOW (current + previous balance) | $243.75 |

**Use Cases:**
- **Budgeting**: Use `current_invoice_total` to track this period's costs
- **Payment**: Use `amount` for how much to pay
- **Accounting**: Line items show the full breakdown for reconciliation

## Why This Approach Works

### ✅ Advantages
1. **No hard-coding**: Works with ANY invoice format after training
2. **Learns patterns**: "Discount keywords", "Previous balance location", etc.
3. **Adapts to changes**: If provider changes format, retrain with 5-10 new samples
4. **Confidence scoring**: System knows when it's uncertain
5. **Structured data**: Line items captured for detailed reporting

### 🔄 Learning Workflow
```
Email Arrives → Rule-Based Extract → Show to User → User Verifies → Store Training Sample
                                                                              ↓
After 20-30 samples ← Train ML Model ← Accumulate Verified Data ←────────────┘
                            ↓
                    AI Auto-Extracts from New Providers
```

### 📊 Current Status
- **Phase 1**: ✅ Rule-based extraction (Active Explorers format working)
- **Phase 2**: ✅ Line items breakdown and learning infrastructure
- **Phase 3**: 🔄 Accumulate 20-30 verified samples
- **Phase 4**: 📋 Train ML model for auto-extraction

## Field Definitions

### Core Fields
- `provider_name`: Daycare/provider name
- `invoice_number`: Unique invoice identifier
- `reference_number`: Child/customer reference (e.g., "SG300")
- `issue_date`: When invoice was issued
- `due_date`: Payment deadline (auto-calculated if not specified)

### Financial Fields
- `amount`: **Total amount due** (what you pay)
- `current_invoice_total`: **New charges only** (for budgeting/tracking)
- `currency`: Currency code (USD, AUD, etc.)

### Line Items Structure
```python
[
    {
        "type": "previous_balance" | "debit" | "credit" | "discount",
        "description": "Human-readable description",
        "amount": float (negative for credits/discounts)
    }
]
```

### Metadata
- `confidence`: 0.0-1.0 score (how sure AI is)
- `status`: draft | complete | error
- `raw_fields`: Debug info (PDF text samples, diagnostics)

## Next Steps for Full AI Learning

1. **Verify 20-30 invoices** from Active Explorers (builds training dataset)
2. **Add invoices from 2-3 other providers** (generalizes patterns)
3. **Train ML model** using scikit-learn or spaCy
4. **Deploy trained model** for auto-extraction
5. **Monitor confidence scores** and flag low-confidence for review

## Technical Details

### Database Schema
```python
class InvoiceExtraction(models.Model):
    # Link to EmailMessage
    content_type = ForeignKey(ContentType)
    object_id = PositiveIntegerField()
    
    # Extracted fields
    provider_name = CharField(max_length=255)
    invoice_number = CharField(max_length=100)
    reference_number = CharField(max_length=100)
    due_date = DateField()
    amount = DecimalField()  # Total amount due
    current_invoice_total = DecimalField()  # New charges only
    
    # AI learning data
    line_items = JSONField()  # Structured breakdown
    confidence = FloatField()
    raw_fields = JSONField()  # Debug/traceability
```

### Training Sample Storage
```python
class TrainingSample(models.Model):
    dataset = ForeignKey(TrainingDataset)
    content_type = ForeignKey(ContentType)
    object_id = PositiveIntegerField()
    
    features = JSONField()  # All extracted fields + line items
    label = CharField()  # 'invoice' for classification
    source = CharField()  # 'user_feedback'
```

## Conclusion

**You don't need to hard-code every format!** The system:
1. Uses flexible rules for initial extraction
2. Learns from your corrections via training samples
3. Will auto-extract from new providers after 20-30 samples
4. Tracks both current charges AND total due for accurate accounting

The more you verify, the smarter it gets! 🚀
