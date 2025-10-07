# AI Email Classification - 3-Tier System Roadmap

## Overview
This document tracks the implementation of a robust 3-tier AI classification system for email management. The goal is to maximize automation while maintaining high accuracy through intelligent confidence-based routing.

**Current Status:** Phase 1 in progress  
**Last Updated:** October 2, 2025  
**Auto-Confirm Threshold:** 95% (updated from 100%)

---

## The 3-Tier System Explained

### Decision Tiers (Confidence-Driven Workflow)

**Tier 1: High-Confidence Auto-Confirm (≥95%)**
- System automatically applies the label
- No human review required
- Goal: 60-90% of emails handled automatically
- Target precision: ≥99%

**Tier 2: Medium-Confidence Human Review (70-95%)**
- Routed to review UI for human confirmation
- User sees prediction as suggestion
- Can accept or correct
- Focus area for user effort

**Tier 3: Low-Confidence Defer/Training (<70%)**
- Model is unsure
- Routed to training queue
- Sampled for careful manual labeling
- Used to improve model

### System Tiers (Lifecycle Architecture)

**Tier A: Offline Training & Calibration**
- Train models on labeled data
- Calibrate confidence scores
- Evaluate performance
- Choose optimal thresholds

**Tier B: Online Inference & Decisioning**
- Serve predictions in real-time
- Apply business rules (95% auto-confirm)
- Route to appropriate tier
- Track decisions

**Tier C: Monitoring & Feedback Loop**
- Track drift and error rates
- Capture corrections from review
- Feed corrections back to training
- Trigger retraining when needed

---

## Phase 1: Monitoring & Validation ⭐ [IN PROGRESS]

**Goal:** Validate the 95% threshold and build visibility into auto-confirmed decisions.

**Status:** In Progress  
**Effort:** 2-4 hours  
**Risk:** Very Low  
**Value:** Very High

### Tasks

- [x] Update auto-confirm threshold from 100% to 95%
  - Updated: `ai/services/email_classification_service.py`
  - Updated: `ai/views.py` (SSE endpoint)
  - Updated: `ai/templates/ai/email_review.html`
  - Documentation: `AUTO_CONFIRM_THRESHOLD_UPDATE.md`

- [x] **Build Auto-Confirmed Review Page** [COMPLETE]
  - [x] Create view: `auto_confirmed_emails_view`
  - [x] Create template: `ai/templates/ai/auto_confirmed_review.html`
  - [x] Add URL route: `/ai/emails/auto-confirmed/`
  - [x] Add navigation link in email review page
  - [x] Implement filters:
    - Date range (Last 7 days, Last 30 days, Custom)
    - Confidence bands (95-97%, 97-99%, 99%+)
  - [x] Display metrics at top:
    - Total auto-confirmed (period)
    - Corrections made
    - Error rate percentage
    - Average confidence
  - [x] Add "Flag as Incorrect" action per row
  - [x] Create correction modal (select correct label)
  - [x] Wire correction to create TrainingSample
  - Documentation: `AUTO_CONFIRMED_REVIEW_IMPLEMENTATION.md`

- [ ] **Test & Validate** [IN PROGRESS]
  - [ ] Run full classification on all emails
  - [ ] Spot-check 50-100 auto-confirmed items
  - [ ] Measure actual error rate
  - [ ] Document findings

### Success Criteria
- Auto-confirmed review page is functional
- Can filter and review auto-confirmed emails easily
- Error rate measured and documented
- Decision made: Is 95% threshold appropriate?

### Key Metrics to Track
- Auto-confirm rate: `(auto_confirmed / total_emails) × 100%`
- Error rate: `(corrections / auto_confirmed) × 100%`
- Target: Error rate < 5% (precision > 95%)

---

## Phase 2: Formalize 3-Tier System [PLANNED]

**Goal:** Implement explicit tier routing and separate workflows for each confidence band.

**Status:** Planned  
**Effort:** 4-6 hours  
**Risk:** Low  
**Value:** High  
**Prerequisites:** Phase 1 complete; threshold validated

### Tasks

- [ ] **Update Classification Service**
  - [ ] Add explicit tier assignment logic
  - [ ] Return tier with each classification
  - [ ] Store tier in Prediction model (add field if needed)
  - [ ] Log tier distribution

- [ ] **Low-Confidence Handling**
  - [ ] Create separate queue for low-confidence items (<70%)
  - [ ] Build training queue view
  - [ ] Add random sampling for manual labeling
  - [ ] Track low-confidence items separately

- [ ] **UI Updates**
  - [ ] Add tier badges (green/yellow/gray)
  - [ ] Separate tabs/filters:
    - "Needs Review" (Tier 2)
    - "Auto-Confirmed" (Tier 1)
    - "Low Confidence" (Tier 3)
  - [ ] Color coding throughout UI
  - [ ] Add confidence bar visualization
  - [ ] Update legend/help text

- [ ] **Tune Middle Threshold**
  - [ ] Analyze Phase 1 data
  - [ ] Test different thresholds (70%, 75%, 80%)
  - [ ] Choose optimal split between Tier 2/3
  - [ ] Document rationale

### Success Criteria
- Clear separation between three tiers
- Users only see Tier 2 in main review workflow
- Low-confidence items handled separately
- Tier distribution visible in metrics

### Decisions to Make (Based on Phase 1 Data)
- [ ] What is the optimal middle threshold? (70%? 75%? 80%?)
- [ ] How many low-confidence items do we get?
- [ ] Is special handling worth it?
- [ ] Should we adjust high threshold? (keep 95% or change?)

---

## Phase 3: Feedback Loop & Retraining [FUTURE]

**Goal:** Make the system self-improving through automated retraining on corrections.

**Status:** Future  
**Effort:** 8-12 hours  
**Risk:** Medium  
**Value:** Very High (long-term)  
**Prerequisites:** Phase 2 complete; 200+ corrections collected

### Tasks

- [ ] **Correction Tracking**
  - [ ] Log all corrections with metadata
  - [ ] Store: original prediction, correction, confidence, features
  - [ ] Track correction source (manual review vs auto-confirmed review)
  - [ ] Add correction count to metrics

- [ ] **Model Versioning**
  - [ ] Add model version to Prediction table
  - [ ] Store model metadata (training date, dataset size, metrics)
  - [ ] Track which model made which predictions
  - [ ] Support multiple model versions

- [ ] **Retraining Pipeline**
  - [ ] Define trigger conditions:
    - Option A: Every N corrections (e.g., 200-500)
    - Option B: Weekly/monthly schedule
    - Option C: When error rate exceeds threshold
  - [ ] Pull all corrections + existing training samples
  - [ ] Split train/validation/test sets
  - [ ] Retrain model with new data
  - [ ] Evaluate on held-out set
  - [ ] Compare to previous model
  - [ ] If metrics improve, deploy new model
  - [ ] If metrics regress, investigate and alert

- [ ] **Calibration**
  - [ ] Implement isotonic or Platt scaling
  - [ ] Ensure confidence matches empirical accuracy
  - [ ] Validate on calibration set
  - [ ] Update thresholds if needed

- [ ] **Drift Detection**
  - [ ] Monitor confidence distribution over time
  - [ ] Track prediction distribution (INVOICE vs NOT INVOICE)
  - [ ] Alert on significant shifts
  - [ ] Track error rate trends
  - [ ] Set up alerts for:
    - Average confidence drops >10%
    - Error rate increases >2×
    - Severe class imbalance

- [ ] **Admin Interface**
  - [ ] Model management page
  - [ ] View model history
  - [ ] Compare model metrics
  - [ ] Trigger manual retraining
  - [ ] View drift alerts

### Success Criteria
- System automatically improves over time
- Tier 1 coverage increases as model improves
- Drift is detected and addressed
- Model versions are tracked and comparable

### Key Metrics to Track
- Model version and training date
- Training dataset size
- Precision/recall/F1 by tier
- Tier 1 coverage over time
- Correction rate over time
- Drift indicators

---

## Optional Enhancements [BACKLOG]

These are nice-to-have features that can be added after core phases are complete.

### Explainability & Trust
- [ ] Show top predictive tokens/phrases
- [ ] Display sender/domain signals
- [ ] Add "Why this prediction?" tooltip
- [ ] Show similar past emails

### Advanced Filtering
- [ ] Filter by sender domain
- [ ] Filter by subject keywords
- [ ] Filter by date received
- [ ] Saved filter presets

### Batch Operations
- [ ] Bulk accept predictions in review
- [ ] Bulk flag as incorrect
- [ ] Bulk label for training

### Performance Optimizations
- [ ] Batch prediction commits
- [ ] Async classification with Celery
- [ ] Caching for frequent queries
- [ ] Database query optimization

### User Experience
- [ ] Keyboard shortcuts for review
- [ ] Estimated time remaining (classification)
- [ ] Pause/resume classification
- [ ] Email preview modal
- [ ] Confidence visualization (gauge/bar)

### Analytics Dashboard
- [ ] Historical trends
- [ ] Sender/domain analysis
- [ ] Time-of-day patterns
- [ ] Weekly/monthly reports

---

## Technical Decisions & Rationale

### Why 95% threshold?
- Industry standard for high-precision automation
- Balances automation (less manual work) with accuracy (fewer errors)
- Can be tuned based on observed error rate
- Target: <5% error rate on auto-confirmed items

### Why 3 tiers instead of 2?
- Low-confidence items need special handling
- Mixing uncertain items with medium-confidence items degrades review efficiency
- Dedicated training queue improves model faster
- Clear separation of concerns

### Why monitor first, then automate?
- Changing from 100% to 95% is significant
- Need empirical data to validate threshold choice
- Catch errors early before they become training data
- Build confidence in the system

### Why SSE for progress?
- Real-time visibility into long-running classification
- Better UX than batch/polling
- Simple to implement with Django StreamingHttpResponse
- Fallback to batch mode if SSE fails

---

## Migration Path

### From Current State to Phase 1
1. ✅ Update threshold to 95% (completed)
2. Build auto-confirmed review page (in progress)
3. Add navigation link from main review page
4. Run classification and collect data
5. Review and measure error rate

### From Phase 1 to Phase 2
1. Decide on middle threshold based on data
2. Add tier field to Prediction model (migration)
3. Update classification service with tier logic
4. Build low-confidence queue
5. Update UI with tier filters/badges

### From Phase 2 to Phase 3
1. Collect 200+ corrections
2. Design retraining pipeline
3. Implement model versioning
4. Add drift detection
5. Set up automated triggers

---

## Resources & References

### Documentation
- `COMBINED_CLASSIFICATION_FEATURE.md` - Combined action button and progress modal
- `SSE_GRANULAR_PROGRESS.md` - Real-time progress with Server-Sent Events
- `AUTO_CONFIRM_THRESHOLD_UPDATE.md` - 95% threshold change rationale

### Key Files
- `ai/services/email_classification_service.py` - Core classification logic
- `ai/views.py` - Web endpoints including SSE
- `ai/templates/ai/email_review.html` - Main review UI
- `ai/models.py` - EmailMessage, Prediction, TrainingSample models

### External Resources
- scikit-learn documentation
- Calibration techniques (isotonic regression)
- Drift detection methods
- Model versioning best practices

---

## Questions & Decisions Log

### October 2, 2025
**Q:** Should we implement monitoring first or jump to 3-tier system?  
**A:** Monitor first. Need to validate 95% threshold before adding more complexity.

**Q:** What should the middle threshold be (Tier 2/3 split)?  
**A:** TBD - will decide after Phase 1 data collection.

**Q:** Is low-confidence queue worth the effort?  
**A:** TBD - depends on volume and distribution from Phase 1.

---

## Notes & Observations

### What We Know
- Auto-confirm was working at 100% (too conservative)
- SSE progress works well for user experience
- UI stability matters (truncation, fixed heights)
- Users need visibility into automated decisions

### What We Need to Learn
- Actual error rate at 95% threshold
- Distribution of confidence scores
- Volume of low-confidence items
- Time savings from automation
- User comfort with auto-confirmed decisions

### Risks to Watch
- Model drift over time (new email patterns)
- Adversarial inputs (spam, phishing attempts)
- Class imbalance (too many of one type)
- Overfitting to corrections
- Calibration degradation

---

## Success Metrics (Long-term)

**Automation**
- Target: 60-90% auto-confirmed (Tier 1)
- Stretch: >80% auto-confirmed

**Accuracy**
- Target: >95% precision on auto-confirmed
- Stretch: >99% precision on auto-confirmed

**Efficiency**
- Target: <5 min/day manual review time
- Measure: Time saved vs manual classification

**Quality**
- Target: Model improves with each retraining
- Measure: F1 score increases over time

**User Experience**
- Target: Users trust auto-confirmed decisions
- Measure: Low correction rate, positive feedback

---

## Next Actions

### Immediate (This Session)
1. Create auto-confirmed review view
2. Create auto-confirmed review template
3. Add URL route and navigation
4. Test functionality

### This Week
1. Run full classification
2. Spot-check 50-100 auto-confirmed items
3. Calculate error rate
4. Document findings
5. Decide: Keep 95% or adjust?

### Next Week
1. Review Phase 1 results
2. Plan Phase 2 implementation
3. Design tier architecture
4. Choose middle threshold

---

**Status Legend:**
- ✅ Complete
- 🚧 In Progress
- 📋 Planned
- 💡 Future/Optional
- ⏸️ Blocked/On Hold
