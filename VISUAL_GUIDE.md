# Visual Guide: 3-Tier AI Email Classification System

**Quick Reference for Understanding the System**

---

## The Big Picture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EMAIL CLASSIFICATION FLOW                     │
└─────────────────────────────────────────────────────────────────┘

                         ┌──────────────┐
                         │ New Email(s) │
                         └──────┬───────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  AI Classification    │
                    │  (scikit-learn model) │
                    └───────────┬───────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
        ┌───────────┐   ┌──────────┐   ┌──────────┐
        │  TIER 1   │   │  TIER 2  │   │  TIER 3  │
        │  ≥95%     │   │  70-95%  │   │  <70%    │
        └─────┬─────┘   └────┬─────┘   └────┬─────┘
              │              │               │
              ▼              ▼               ▼
      ┌──────────────┐  ┌────────┐   ┌──────────────┐
      │ Auto-Confirm │  │ Review │   │ Training     │
      │ & File Away  │  │ Queue  │   │ Queue/Skip   │
      └──────────────┘  └────────┘   └──────────────┘
```

---

## The Three Tiers Explained

### 🟢 TIER 1: High-Confidence Auto-Confirm (≥95%)

**What Happens:**
- AI predicts with ≥95% confidence
- System automatically applies label
- Email marked as classified
- Training sample created
- User NEVER sees this in main review

**User Experience:**
- Invisible automation
- Can review via special page (validation)
- Can flag if incorrect

**Goal:**
- Handle 60-90% of emails automatically
- Maintain >95% precision
- Reduce manual work dramatically

**Example:**
```
Email: "Your child's daycare invoice for March 2025"
Confidence: 99.2%
Action: Auto-labeled as INVOICE
Status: Filed away, ready for processing
```

---

### 🟡 TIER 2: Medium-Confidence Human Review (70-95%)

**What Happens:**
- AI predicts with 70-95% confidence
- System creates pending prediction
- Shows in main review queue
- User confirms or corrects
- Becomes training data

**User Experience:**
- Appears in review list
- Shows AI's suggestion
- Quick confirm/reject buttons
- Focused on uncertain items

**Goal:**
- Handle 10-30% of emails with human input
- Leverage AI suggestion to speed decision
- Catch edge cases and improve model

**Example:**
```
Email: "Receipt for monthly care services"
Confidence: 87.3%
AI Suggests: INVOICE
User Action: Confirm (correct) or Reject (incorrect)
```

---

### 🔴 TIER 3: Low-Confidence Defer/Training (<70%)

**What Happens:**
- AI predicts with <70% confidence
- System marks as uncertain
- Kept separate from main review
- Optionally sampled for careful labeling
- Used to improve model

**User Experience:**
- Not in main review queue (reduces noise)
- Appears in training queue
- Can sample randomly for labeling
- Focus on expanding model coverage

**Goal:**
- Handle 0-10% of emails (after model matures)
- Avoid overwhelming user with hard cases
- Strategically improve model on edge cases

**Example:**
```
Email: "Quick question about pickup time"
Confidence: 42.1%
AI Suggests: NOT INVOICE (but unsure)
Action: Skip main review, add to training queue
```

---

## Current State (Phase 1)

```
┌────────────────────────────────────────────────────────────┐
│                    CURRENT IMPLEMENTATION                   │
└────────────────────────────────────────────────────────────┘

  TIER 1 (≥95%)          TIER 2 (<95%)         TIER 3
  ✅ IMPLEMENTED         ✅ IMPLEMENTED        ⏸️ PENDING
  
  Auto-confirmed         Review queue          Not separated yet
  Special review page    Main review page      (grouped with Tier 2)
  Flag/correction        Confirm/reject
  Error rate tracking    Training samples
```

### What You Have Right Now:

1. **Tier 1 (≥95%):**
   - ✅ Auto-confirmation working
   - ✅ Review page to validate
   - ✅ Flag incorrect predictions
   - ✅ Metrics tracking (error rate)

2. **Tier 2 (All <95%):**
   - ✅ Main review queue
   - ✅ Confirm/reject workflow
   - ✅ Training sample creation

3. **Tier 3 (<70%):**
   - ⏸️ Not separated yet
   - ⏸️ Currently mixed with Tier 2
   - 📋 Planned for Phase 2

---

## Phase 2 Target State

```
┌────────────────────────────────────────────────────────────┐
│                    PHASE 2 GOAL                             │
└────────────────────────────────────────────────────────────┘

  TIER 1 (≥95%)          TIER 2 (70-95%)       TIER 3 (<70%)
  ✅ IMPLEMENTED         🔄 REFINED            ⭐ NEW
  
  Auto-confirmed         Review queue          Training queue
  Validation page        Filtered view         Sampling interface
  Error tracking         Quick actions         Careful labeling
```

### Phase 2 Will Add:

1. **Explicit Tier Assignment:**
   - Each prediction tagged with tier (1, 2, or 3)
   - Stored in database
   - Used for routing

2. **Separate Low-Confidence Queue:**
   - Tier 3 items don't clutter main review
   - Random sampling for labeling
   - Track coverage expansion

3. **Enhanced UI:**
   - Tier badges on all items
   - Separate tabs/filters
   - Color coding throughout
   - Clear separation of concerns

---

## User Experience Journey

### Before Classification
```
📬 Inbox: 1,247 emails
❓ Status: Unknown
⏳ Effort Required: High (manual review all)
```

### After Classification (Current Phase 1)
```
✅ Classified: 1,050 (84%)
   └─ Auto-confirmed (≥95%): ~840 (67%)
   └─ Needs review (<95%): ~210 (17%)
❓ Unclassified: 197 (16%)
⏳ Effort Required: Medium (review 210 items)
```

### After Phase 2 (Target)
```
✅ Classified: 1,050 (84%)
   ├─ Tier 1 (≥95%): ~840 (67%) → Auto-filed
   ├─ Tier 2 (70-95%): ~150 (12%) → Quick review
   └─ Tier 3 (<70%): ~60 (5%) → Training queue
❓ Unclassified: 197 (16%)
⏳ Effort Required: Low (review 150 items, sample 10-20 from Tier 3)
```

---

## Where You Are Now (Visual Map)

```
┌─────────────────────────────────────────────────────────────┐
│                     YOUR PROGRESS MAP                        │
└─────────────────────────────────────────────────────────────┘

Phase 1: Monitoring & Validation
├─ ✅ Update threshold to 95%
├─ ✅ Build auto-confirmed review page
├─ ✅ Add flag/correction workflow
├─ ✅ Wire up navigation
├─ ✅ Django checks passed
└─ 🔄 Test and validate (YOUR NEXT STEP)

Phase 2: Formalize 3-Tier System
├─ ⏸️ Add tier field to Prediction model
├─ ⏸️ Separate Tier 3 items
├─ ⏸️ Build training queue interface
├─ ⏸️ Add tier badges to UI
└─ ⏸️ Tune middle threshold (70%?)

Phase 3: Feedback Loop & Retraining
├─ ⏸️ Collect 200+ corrections
├─ ⏸️ Build retraining pipeline
├─ ⏸️ Add model versioning
├─ ⏸️ Implement drift detection
└─ ⏸️ Automated retraining triggers
```

---

## Decision Tree: What Should You Do?

```
┌─────────────────────────────────────────────────────────────┐
│                   DECISION TREE                              │
└─────────────────────────────────────────────────────────────┘

Start: You've built Phase 1
│
├─ Step 1: Run classification
│  └─ Note: How many auto-confirmed?
│
├─ Step 2: Spot-check 50-100 auto-confirmed items
│  ├─ Use new review page
│  ├─ Flag any errors
│  └─ Calculate: Errors / Checked = Error Rate
│
└─ Step 3: Check error rate
   │
   ├─ Error Rate < 3%? (Excellent!)
   │  └─ Consider: Lower threshold to 90%
   │     (More automation, still safe)
   │
   ├─ Error Rate 3-5%? (Good!)
   │  └─ Keep: 95% threshold
   │     └─ Next: Plan Phase 2
   │
   ├─ Error Rate 5-7%? (Acceptable)
   │  └─ Options:
   │     ├─ Keep 95% and monitor
   │     └─ Raise to 97% (safer)
   │
   └─ Error Rate > 7%? (Investigate!)
      └─ Actions:
         ├─ Raise threshold to 97-98%
         ├─ Check model quality
         └─ Review feature engineering
```

---

## Metrics Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│            AUTO-CONFIRMED REVIEW PAGE                        │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ METRICS SUMMARY                                              │
├────────────┬────────────┬────────────┬────────────────────────┤
│ Total      │ Corrections│ Error Rate │ Avg Confidence         │
│ Auto-Conf  │ Made       │            │                        │
├────────────┼────────────┼────────────┼────────────────────────┤
│    840     │     12     │   1.43%    │      97%               │
│            │            │  🟢 Green  │                        │
└────────────┴────────────┴────────────┴────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ FILTERS                                                      │
├──────────────────────────────────────────────────────────────┤
│ Date Range: [Last 7 Days ▼]  Confidence: [All (≥95%) ▼]    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ RESULTS TABLE                                                │
├────────┬─────────────────────┬─────────┬────────┬────────────┤
│ Date   │ Subject             │ Predict │ Conf   │ Actions    │
├────────┼─────────────────────┼─────────┼────────┼────────────┤
│ Oct 1  │ Daycare Invoice...  │ INVOICE │ 99% 🟢 │ [Flag]     │
│ Oct 1  │ Monthly Statement..│ INVOICE │ 97% 🔵 │ [Flag]     │
│ Sep 30 │ Payment Reminder...│ INVOICE │ 96% 🟡 │ [Flag]     │
└────────┴─────────────────────┴─────────┴────────┴────────────┘
```

Legend:
- 🟢 99-100%: Highest confidence
- 🔵 97-99%: High confidence  
- 🟡 95-97%: Medium-high confidence

---

## Key Concepts Visual

### Confidence vs. Tier Mapping

```
Confidence Score          Tier             Action
───────────────────────────────────────────────────
100% ─┐
      │
 99%  ├─────────────────> TIER 1  ────> Auto-Confirm
      │                   (≥95%)        (File Away)
 98%  │
      │
 97%  │
      │
 96%  │
      │
 95% ─┤
───────────────────────────────────────────────────
 94%  │
      │
 93%  │
      ├─────────────────> TIER 2  ────> Human Review
 92%  │                   (70-95%)      (Quick Decision)
 ...  │
      │
 71%  │
 70% ─┤
───────────────────────────────────────────────────
 69%  │
      │
 68%  ├─────────────────> TIER 3  ────> Training Queue
 ...  │                   (<70%)        (Careful Labeling)
      │
 50%  │
───────────────────────────────────────────────────
```

### Error Rate Health Check

```
Error Rate Range     Status        Action
─────────────────────────────────────────────────
 0-3%       🟢      Excellent    Consider lowering threshold
 3-5%       🟢      Good         Keep current threshold
 5-7%       🟡      Acceptable   Monitor closely
 7-10%      🟠      Warning      Consider raising threshold
 >10%       🔴      Critical     Investigate model/raise threshold
```

---

## File Navigation Guide

```
📁 famlyportal/
│
├─ 📄 AI_CLASSIFICATION_ROADMAP.md
│  └─ Purpose: Master plan for 3-tier system
│     When to use: Planning, decision-making, tracking progress
│
├─ 📄 AUTO_CONFIRMED_REVIEW_IMPLEMENTATION.md
│  └─ Purpose: Technical details of review page
│     When to use: Understanding implementation, troubleshooting
│
├─ 📄 SESSION_SUMMARY.md
│  └─ Purpose: Quick recap and next steps
│     When to use: Getting oriented, knowing what's done
│
├─ 📄 THIS FILE (VISUAL_GUIDE.md)
│  └─ Purpose: Visual reference and conceptual understanding
│     When to use: Learning the system, explaining to others
│
└─ 📁 ai/
   ├─ views.py (auto_confirmed_emails_view, flag_auto_confirmed_view)
   ├─ urls.py (routes)
   └─ templates/ai/auto_confirmed_review.html (UI)
```

---

## Quick Commands Reference

### Access Auto-Confirmed Review Page
```
1. Navigate to: http://127.0.0.1:8000/ai/emails/review/
2. Click: "Review Auto-Confirmed" button (green, top right)
3. Or direct: http://127.0.0.1:8000/ai/emails/auto-confirmed/
```

### Run Classification
```
1. Navigate to: http://127.0.0.1:8000/ai/emails/review/
2. Click: "Classify Unclassified Emails" button
3. Watch: SSE progress modal
4. Check: Auto-confirmed count in final summary
```

### Flag Incorrect Prediction
```
1. Find item in auto-confirmed review table
2. Click: "Flag as Incorrect" button (red)
3. Select: Correct label (INVOICE or NOT INVOICE)
4. Optional: Add note explaining why
5. Submit: Item disappears, metrics update
```

---

## The Flywheel Effect

```
┌─────────────────────────────────────────────────────────────┐
│              CONTINUOUS IMPROVEMENT CYCLE                    │
└─────────────────────────────────────────────────────────────┘

    1. Classify Emails
           │
           ▼
    2. Auto-Confirm High Confidence (Tier 1)
           │
           ▼
    3. User Reviews Medium Confidence (Tier 2)
           │
           ▼
    4. Corrections Collected
           │
           ▼
    5. Retrain Model with Corrections
           │
           ▼
    6. Model Improves (Higher Confidence)
           │
           └──────> BACK TO STEP 1 (More Auto-Confirms)

Result: Over time, Tier 1 expands, Tier 2 shrinks, less work!
```

---

## Success Visualization

### Month 0 (Now)
```
Tier 1: ████████████████████████████░░░░░░░░░░░░  67%
Tier 2: ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  17%
Tier 3: ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   5%
Unclass: ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  16%

Manual Effort: 210 emails to review
```

### Month 3 (After Retraining)
```
Tier 1: ███████████████████████████████████░░░░░  80%
Tier 2: ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  10%
Tier 3: █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   3%
Unclass: ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   7%

Manual Effort: 120 emails to review (-43% effort!)
```

### Month 6 (Mature System)
```
Tier 1: ████████████████████████████████████████░  90%
Tier 2: █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   6%
Tier 3: ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   2%
Unclass: ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   2%

Manual Effort: 70 emails to review (-67% effort!)
```

---

## Remember

### The Core Philosophy

1. **Automate the obvious** (Tier 1: ≥95%)
2. **Assist with the uncertain** (Tier 2: 70-95%)
3. **Learn from the edge cases** (Tier 3: <70%)
4. **Improve continuously** (Feedback loop)

### The Key Metrics

- **Auto-confirm Rate:** % of emails handled automatically (target: 60-90%)
- **Error Rate:** % of auto-confirms that were wrong (target: <5%)
- **Review Efficiency:** Time spent per email in Tier 2 (should decrease)
- **Coverage:** % of emails classified (vs. skipped)

### The Success Criteria

- ✅ Less manual work over time
- ✅ High accuracy maintained (>95% precision)
- ✅ User trust in automation
- ✅ Continuous model improvement

---

**You are here:** Phase 1 complete, validation pending 🎯  
**Next milestone:** 50 items spot-checked, error rate measured 📊  
**End goal:** Self-improving system handling 80-90% automatically 🚀
