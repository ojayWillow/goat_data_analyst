# Reporter Agent Flow - How Reports Are Generated

**Great question. Let me clarify the exact data flow.**

---

## The Question You Asked:

> "Report is something we get from load, explore, aggregate, anomalies, predict.
> Then we get the report. Does the report go to the orchestrator?"

**Answer: YES, but with nuance.**

---

## Data Flow Architecture

```
┌──────────────────────────────────────────┐
│            ORCHESTRATOR (Master Conductor)           │
│   Coordinates everything + manages DATA CACHE       │
└──────────────────────────────────────────┘
              │
    ┌──────────────────────────────────────────┐
    │         DATA CACHE (Shared Memory)          │
    │  Orchestrator stores results here:       │
    │  - loaded_data                           │
    │  - exploration_results                   │
    │  - aggregation_results                   │
    │  - anomalies                             │
    │  - predictions                           │
    │  - recommendations                       │
    │  - narrative_story                       │
    │  - visualizations                        │
    └──────────────────────────────────────────┘
              │
        ├──────────────────────────────────────────┐
        │              Each Agent:                 │
        │   1. Takes data from cache              │
        │   2. Processes it                       │
        │   3. Stores result back in cache        │
        └──────────────────────────────────────────┘
        │
        ├─DataLoaderAgent
        │   Input: none
        │   Process: load CSV
        │   Output cached: 'loaded_data'
        │
        ├─ExplorerAgent
        │   Input: 'loaded_data' (from cache)
        │   Process: analyze, statistics
        │   Output cached: 'exploration_results'
        │
        ├─AggregatorAgent
        │   Input: 'loaded_data' (from cache)
        │   Process: group and summarize
        │   Output cached: 'aggregation_results'
        │
        ├─AnomalyDetectorAgent
        │   Input: 'loaded_data' (from cache)
        │   Process: find outliers
        │   Output cached: 'anomalies'
        │
        ├─PredictorAgent
        │   Input: 'loaded_data' (from cache)
        │   Process: train models, predict
        │   Output cached: 'predictions'
        │
        ├─RecommenderAgent
        │   Input: ALL previous results (from cache)
        │   Process: suggest actions
        │   Output cached: 'recommendations'
        │
        ├─NarrativeGeneratorAgent
        │   Input: ALL previous results (from cache)
        │   Process: create story
        │   Output cached: 'narrative_story'
        │
        ├─VisualizerAgent
        │   Input: ALL previous results (from cache)
        │   Process: create charts
        │   Output cached: 'visualizations'
        │
        ├─ReporterAgent
        │   Input: ALL previous results (from cache)
        │   Process: assemble into report
        │   Output: FINAL REPORT (PDF/HTML/DOCX)
        │
        └─ORCHESTRATOR receives the report back
           Logs it, stores it, returns to user
```

---

## Step-by-Step: How Reporter Works

### Phase 1: Before Reporter Runs

**Orchestrator has already executed:**
```
1. load_data       → Cached: 'loaded_data' (DataFrame)
2. explore         → Cached: 'exploration_results' (stats, insights)
3. aggregate       → Cached: 'aggregation_results' (grouped data)
4. anomalies       → Cached: 'anomalies' (outliers list)
5. predict         → Cached: 'predictions' (forecasts, models)
6. recommend       → Cached: 'recommendations' (actions list)
7. narrative       → Cached: 'narrative_story' (human story)
8. visualize       → Cached: 'visualizations' (charts)
```

**All this data is in the DATA CACHE (managed by Orchestrator).**

---

### Phase 2: Reporter Reads Everything

**When Reporter task is triggered:**

```python
def execute_report_task(task):
    """Reporter agent executes."""
    
    # Get ALL cached data from Orchestrator's cache
    report_inputs = {
        'raw_data': orchestrator.get_cached_data('loaded_data'),
        'exploration': orchestrator.get_cached_data('exploration_results'),
        'aggregation': orchestrator.get_cached_data('aggregation_results'),
        'anomalies': orchestrator.get_cached_data('anomalies'),
        'predictions': orchestrator.get_cached_data('predictions'),
        'recommendations': orchestrator.get_cached_data('recommendations'),
        'narrative': orchestrator.get_cached_data('narrative_story'),
        'visualizations': orchestrator.get_cached_data('visualizations')
    }
    
    # Assemble into professional report
    report = ReporterAgent.generate_report(report_inputs)
    
    # Return report
    return report
```

---

### Phase 3: Reporter Creates Professional Document

**Reporter takes all cached inputs and creates:**

```
┌─────────────────────────────────────┐
│        FINAL REPORT (PDF/HTML/DOCX)             │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ COVER PAGE                                  │
│ │                                          │
│ Customer Analytics Report 2025             │
│ Generated: 2025-12-13                      │
│ │                                          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ EXECUTIVE SUMMARY (1 page)                 │
│ │                                          │
│ Key findings at a glance                   │
│ From EXPLORATION results                   │
│ │                                          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ DATA OVERVIEW (2 pages)                    │
│ │                                          │
│ What the data looks like                   │
│ From LOADED_DATA results                   │
│ │                                          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ DETAILED ANALYSIS (4 pages)                │
│ │                                          │
│ Regional breakdown, patterns, insights     │
│ From AGGREGATION results                   │
│ │                                          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ RISK ASSESSMENT (2 pages)                  │
│ │                                          │
│ Fraud alerts, anomalies, issues            │
│ From ANOMALIES results                     │
│ │                                          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ PREDICTIONS & FORECASTS (2 pages)         │
│ │                                          │
│ What will happen, future trends            │
│ From PREDICTIONS results                   │
│ │                                          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ NARRATIVE ANALYSIS (3 pages)              │
│ │                                          │
│ The story - what it means, why it matters │
│ From NARRATIVE GENERATOR results           │
│ │                                          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ RECOMMENDATIONS (3 pages)                  │
│ │                                          │
│ Actions to take, prioritized               │
│ From RECOMMENDATIONS results               │
│ │                                          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ VISUALIZATIONS (4 pages)                   │
│ │                                          │
│ Charts, graphs, heatmaps                   │
│ From VISUALIZER results                    │
│ │                                          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ APPENDIX (8 pages)                         │
│ │                                          │
│ - Raw data samples                         │
│ - Model details                            │
│ - Methodology                              │
│ - Technical details                        │
│ │                                          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ TOTAL: 30 pages, professional PDF          │
└─────────────────────────────────────┘
```

---

## Phase 4: Report Returns to Orchestrator

**Reporter finishes and returns result:**

```python
report_result = {
    'task_type': 'report',
    'status': 'completed',
    'report_file': 'report_2025-12-13.pdf',
    'report_size': '15MB',
    'pages': 30,
    'timestamp': '2025-12-13T19:14:00Z',
    'quality_score': 0.95
}
```

**Orchestrator receives this and:**
1. Caches it
2. Logs it
3. Returns final result to USER

---

## The Complete Flow (End-to-End)

```python
# USER initiates
user_input = "Analyze our customer data"

# ORCHESTRATOR coordinates
orchestrator.execute_workflow([
    {'type': 'load_data', 'parameters': {'file': 'data.csv'}},
    {'type': 'explore', 'parameters': {}},
    {'type': 'aggregate', 'parameters': {}},
    {'type': 'detect_anomalies', 'parameters': {}},
    {'type': 'predict', 'parameters': {}},
    {'type': 'recommend', 'parameters': {}},
    {'type': 'narrative', 'parameters': {}},
    {'type': 'visualize', 'parameters': {}},
    {'type': 'report', 'parameters': {'format': 'pdf'}}
])

# Each agent executes in order:
# 1. DataLoaderAgent: Loads CSV → cached as 'loaded_data'
# 2. ExplorerAgent: Analyzes → cached as 'exploration_results'
# 3. AggregatorAgent: Groups → cached as 'aggregation_results'
# 4. AnomalyDetectorAgent: Finds issues → cached as 'anomalies'
# 5. PredictorAgent: Predicts → cached as 'predictions'
# 6. RecommenderAgent: Suggests → cached as 'recommendations'
# 7. NarrativeGeneratorAgent: Tells story → cached as 'narrative_story'
# 8. VisualizerAgent: Creates charts → cached as 'visualizations'

# 9. ReporterAgent: READS ALL CACHED DATA
#    ✓ Gets 'loaded_data'
#    ✓ Gets 'exploration_results'
#    ✓ Gets 'aggregation_results'
#    ✓ Gets 'anomalies'
#    ✓ Gets 'predictions'
#    ✓ Gets 'recommendations'
#    ✓ Gets 'narrative_story'
#    ✓ Gets 'visualizations'
#    Assembles into 30-page PDF report
#    Returns to Orchestrator

# ORCHESTRATOR receives report
# Caches it
# Returns final_result to USER

final_result = {
    'status': 'success',
    'workflow_completed': True,
    'total_tasks': 9,
    'report_file': 'report_2025-12-13.pdf',
    'quality_score': 0.95
}

# USER gets the PDF report
print("Your report is ready: report_2025-12-13.pdf")
```

---

## Key Points About Reporter

### ✅ **Does Reporter Read from Orchestrator?**
YES. The Orchestrator manages the DATA CACHE.
Reporter reads from that cache.

### ✅ **Does Report Go Back to Orchestrator?**
YES. Reporter returns the generated report to Orchestrator.
Orchestrator stores it and returns to user.

### ✅ **What Does Reporter Read?**
EVERYTHING from previous agents:
- Raw data
- Analysis results
- Anomalies
- Predictions
- Recommendations
- Narrative story
- Visualizations

### ✅ **What Does Reporter Create?**
ONE PROFESSIONAL DOCUMENT:
- PDF/HTML/DOCX format
- 20-30 pages
- All findings assembled
- Professional layout
- Ready to send to executives

---

## Diagram: Data Flow

```
USER
  │
  ▼
ORCHESTRATOR (Master)
  │
  ├─DATA CACHE
  │   ├─ loaded_data
  │   ├─ exploration_results
  │   ├─ aggregation_results
  │   ├─ anomalies
  │   ├─ predictions
  │   ├─ recommendations
  │   ├─ narrative_story
  │   ├─ visualizations
  │   └─ [final_report - written by Reporter]
  │
  ├─ Load Agent (writes to cache)
  ├─ Explore Agent (reads cache, writes to cache)
  ├─ Aggregate Agent (reads cache, writes to cache)
  ├─ Anomaly Agent (reads cache, writes to cache)
  ├─ Predict Agent (reads cache, writes to cache)
  ├─ Recommend Agent (reads cache, writes to cache)
  ├─ Narrative Agent (reads cache, writes to cache)
  ├─ Visualizer Agent (reads cache, writes to cache)
  ├─ Reporter Agent (reads ALL cache, creates REPORT)
  │
  ▼
  RETURNS FINAL REPORT TO USER
```

---

## Summary: Reporter Flow

**Your Question:**
> "Report is something from load, explore, aggregate, anomalies, predict.
> Does report go to orchestrator?"

**Answer:**
1. ✓ Reporter reads results from load, explore, aggregate, anomalies, predict
2. ✓ Reporter also reads from recommend, narrative, visualize
3. ✓ Reporter assembles everything into ONE professional document
4. ✓ Reporter returns that document to ORCHESTRATOR
5. ✓ Orchestrator returns it to USER

**Flow:**
```
All Agents → Cache Results → Reporter Reads All → Report Generated
→ Reporter Returns to Orchestrator → Orchestrator Returns to User
```

**It's not a linear pipeline where Reporter gets data from just predict.**
**Reporter is the FINAL STEP that ASSEMBLES everything into one document.**
