# Week 3, Day 3 (Sun, Dec 22) - Action Recommender ✅

**Status:** COMPLETE

**Objective:** Generate actionable recommendations for identified problems

## What Was Built

### Files Created

1. **`agents/narrative_generator/workers/action_recommender.py`**
   - Main ActionRecommender worker implementation
   - 4 recommendation methods (one per problem type):
     - `recommend_for_anomalies()`: Actions to handle unusual values
     - `recommend_for_missing_data()`: Strategies to handle incomplete data
     - `recommend_for_prediction()`: Ways to improve model confidence
     - `recommend_for_distribution()`: Techniques to normalize data
   - 1 integration method:
     - `recommend_for_all_problems()`: Generate recommendations for all + rank
   - Time estimation based on effort and magnitude
   - Specific, actionable recommendations (not generic)

2. **`agents/narrative_generator/workers/__init__.py`** (Updated)
   - Added ActionRecommender import
   - Exports: InsightExtractor, ProblemIdentifier, ActionRecommender

3. **`tests/test_action_recommender.py`**
   - 22 comprehensive tests
   - Test categories:
     - Anomaly recommendations (3 tests)
     - Missing data recommendations (3 tests)
     - Prediction recommendations (3 tests)
     - Distribution recommendations (3 tests)
     - Effort and priority (2 tests)
     - Integration (3 tests)
     - Specificity (1 test)
     - Error handling (2 tests)
     - Edge cases (2 tests)

## Recommendation Structure

```python
{
  'action': str,           # What to do
  'detail': str,          # How to do it (specific, not generic)
  'impact': str,          # Why it matters
  'effort': str,          # low/medium/high
  'priority': int,        # 1-5 (5 = highest)
  'time_estimate': str,   # How long it will take
  'problem_type': str     # Type of problem (in list context)
}
```

## Recommendation Rules by Problem Type

**Anomalies:**
- Critical (>15%) → "Immediately investigate and handle" (Priority 5, Medium effort)
- High (10-15%) → "Review and handle significant anomalies" (Priority 4, Medium effort)
- Medium (5-10%) → "Document anomalies and update rules" (Priority 3, Low effort)
- Low (<5%) → "Monitor anomalies in future" (Priority 1, Low effort)

**Missing Data:**
- Critical (>15%) → "Implement handling strategy" (Priority 5, High effort)
- High (10-15%) → "Address critical columns" (Priority 4, Medium effort)
- Medium (5-10%) → "Impute remaining values" (Priority 2, Low effort)
- Low (<5%) → "Document patterns" (Priority 1, Low effort)

**Prediction Confidence:**
- Critical (<50%) → "Retrain model" (Priority 5, High effort)
- High (50-65%) → "Feature engineering" (Priority 4, Medium effort)
- Medium (65-75%) → "Hyperparameter tuning" (Priority 3, Medium effort)
- Low (>75%) → "Monitor performance" (Priority 1, Low effort)

**Distribution Skew:**
- Critical (CV >2.0) → "Apply transformation" (Priority 5, Medium effort)
- High (CV 1.5-2.0) → "Normalize features" (Priority 4, Low effort)
- Medium (CV 1.0-1.5) → "Consider scaling" (Priority 2, Low effort)
- Low (CV <1.0) → "Monitor distribution" (Priority 1, Low effort)

## Key Features

✅ **Specific, Not Generic:**
- Includes actual numbers/percentages in recommendations
- Examples: "Remove 42 anomalies from North region"
- NOT: "Fix your data"

✅ **Ranked by Priority:**
- Recommendations sorted by severity (Priority 5 to 1)
- User knows what to do first

✅ **Effort-Aware:**
- Easy fixes have low effort
- Hard fixes have high effort
- User can plan accordingly

✅ **Impact-Focused:**
- Each recommendation explains why it matters
- Quantifies improvement ("Improves accuracy by ~5-7%")
- Motivates action

✅ **Time-Estimated:**
- Effort + magnitude → Time estimate
- User knows "< 1 hour" vs "1-2 days"
- Helps with planning

## Tests Status: ✅ 22 Passing

- Anomaly recommendations (critical/high/low) ✓
- Missing data recommendations (critical/high/low) ✓
- Prediction recommendations (critical/high/low) ✓
- Distribution recommendations (critical/high/low) ✓
- Effort levels assigned correctly ✓
- Time estimates vary by magnitude ✓
- Multiple recommendations ranked ✓
- Critical problems always priority 5 ✓
- Specific details included (not generic) ✓
- Error handling for invalid types ✓
- Recommendation structure validation ✓

## Architecture Flow

```
Problem Identifier
       ↓
  [Problem Dict]
       ↓
Action Recommender
       ↓
[Recommendation Dict]
       ↓
  Ranked by Priority
```

## Ready for Day 4

Next: **StoryBuilder** (Monday, Dec 23)
- Convert recommendations into readable narrative
- Create compelling explanation
- Organize by priority
- Add supporting context

## Summary

- ✅ 3 files created/updated
- ✅ 22 tests passing
- ✅ 4 recommendation types
- ✅ Specific, actionable recommendations
- ✅ Priority-ranked output
- ✅ Time-estimated actions
- ✅ Code follows architecture pattern

**Status:** Ready for Day 4 ➡️
