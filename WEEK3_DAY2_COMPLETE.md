# Week 3, Day 2 (Sat, Dec 21) - Problem Identifier ✅

**Status:** COMPLETE

**Objective:** Identify what's wrong with the data

## What Was Built

### Files Created

1. **`agents/narrative_generator/workers/problem_identifier.py`**
   - Main ProblemIdentifier worker implementation
   - 4 problem detection methods:
     - `identify_anomaly_problems()`: Unusual values in data
     - `identify_missing_data_problems()`: Incomplete records
     - `identify_prediction_problems()`: Low model confidence
     - `identify_distribution_problems()`: Skewed/outlier-heavy data
   - 1 integration method:
     - `identify_all_problems()`: Run all detections + rank
   - Severity enum: critical, high, medium, low, none
   - Severity thresholds based on percentages:
     - Critical: >15% affected
     - High: 10-15% affected
     - Medium: 5-10% affected
     - Low: <5% affected
   - Helper methods for impact descriptions

2. **`agents/narrative_generator/workers/__init__.py`** (Updated)
   - Added ProblemIdentifier import
   - Exports both InsightExtractor and ProblemIdentifier

3. **`tests/test_problem_identifier.py`**
   - 18 comprehensive tests
   - Test categories:
     - Anomaly problem detection (3 tests)
     - Missing data problem detection (3 tests)
     - Prediction problem detection (3 tests)
     - Distribution problem detection (3 tests)
     - Severity scoring (2 tests)
     - Integration (4 tests)
     - Error handling (2 tests)

## Problem Structure

```python
{
  'type': 'anomalies' | 'missing_data' | 'low_prediction_confidence' | 'skewed_distribution',
  'severity': 'critical' | 'high' | 'medium' | 'low',
  'percentage': float,  # % of data affected
  'description': str,   # Human-readable description
  'impact': str,        # Impact explanation
  'location': str,      # Where problem is located
  'fix_priority': int   # 0-4 (for sorting)
}
```

## Severity Rules

**Anomaly Severity:**
- >15% anomalies → Critical
- 10-15% → High
- 5-10% → Medium
- <5% → Low
- 0% → None (no problem)

**Missing Data Severity:**
- >15% missing → Critical
- 10-15% missing → High
- 5-10% missing → Medium
- <5% missing → Low

**Prediction Confidence Severity:**
- <50% confidence → Critical
- 50-65% confidence → High
- 65-75% confidence → Medium
- >75% confidence → No problem

**Distribution Skew Severity:**
- CV >2.0 → Critical (coefficient of variation)
- CV 1.5-2.0 → High
- CV 1.0-1.5 → Medium
- CV <1.0 → No problem

## Impact Descriptions

Each problem type has impact descriptions:
- **Anomalies:** "Severely skews statistical measures", "Significantly affects model accuracy", etc.
- **Missing Data:** "Cannot train reliable models", "Significantly impacts training", etc.
- **Low Confidence:** "Predictions are unreliable", "Needs improvement before deployment", etc.
- **Skewed Distribution:** "Extreme variability", "High variability", etc.

## Key Features

✅ **Multiple Problem Types:**
- Anomalies detected and classified
- Missing data identified by completeness
- Prediction confidence assessed
- Distribution quality evaluated

✅ **Severity Ranking:**
- Problems ranked by severity (critical > high > medium > low)
- Priority scores for sorting (fix_priority: 4-0)
- Threshold-based classification

✅ **Problem Prioritization:**
- All problems identified and ranked by severity
- Highest priority problems listed first
- User knows which to fix first

✅ **Clear Impact Descriptions:**
- Each problem explains why it matters
- Impact varies by severity
- Actionable feedback

## Tests Status: ✅ 18 Passing

- Anomaly problem detection ✓
- Missing data problem detection ✓
- Prediction problem detection ✓
- Skewed distribution detection ✓
- Severity thresholds at boundaries ✓
- Severity scoring for ranking ✓
- Multiple problems identified ✓
- Problems ranked by severity ✓
- Clean dataset produces no problems ✓
- Problem structure validation ✓
- Empty/None input handling ✓
- Impact descriptions vary by severity ✓

## Ready for Day 3

Next: **ActionRecommender** (Sunday, Dec 22)
- Generate actionable recommendations
- For each problem, suggest fix
- Rank by priority and impact
- Explain why action matters

## Summary

- ✅ 3 files created/updated
- ✅ 18 tests passing
- ✅ 4 problem types detectable
- ✅ Severity ranking working
- ✅ Impact descriptions clear
- ✅ Code follows architecture pattern

**Status:** Ready for Day 3 ➡️
