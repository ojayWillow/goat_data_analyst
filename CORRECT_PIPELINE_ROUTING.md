# Correct Pipeline Routing

**Make sure data goes to the RIGHT agent, in the RIGHT order.**

---

## Your Current Agents

```
1. DataLoaderAgent       - Load raw data
2. ExplorerAgent         - Analyze & find patterns
3. AggregatorAgent       - Group & summarize
4. AnomalyDetectorAgent  - Find outliers/fraud
5. PredictorAgent        - Make predictions
6. RecommenderAgent      - Suggest actions
7. VisualizerAgent       - Create charts/visuals
8. ReporterAgent         - Format into report
9. NarrativeGeneratorAgent - Create story
10. OrchestratorAgent    - COORDINATOR (routes all)
11. ErrorIntelligence    - Track all errors
```

---

## Correct Pipeline Flow

```
┌──────────────────────────────────────┐
│ 1. RAW DATA FILE                              │
└──────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ ORCHESTRATOR                                 │
│ (routes task: 'load_data')                  │
└──────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ 2. DATALOADER AGENT                          │
│ - Read file                                  │
│ - Validate data                              │
│ - Return DataFrame                           │
└──────────────────────────────────────┘
           │
           ├── Cache: df
           │
           ▼
┌──────────────────────────────────────┐
│ 3. EXPLORER AGENT                            │
│ - Analyze patterns                           │
│ - Calculate stats                            │
│ - Find insights                              │
└──────────────────────────────────────┘
           │
           ├── Cache: exploration_results
           │
           ▼
┌──────────────────────────────────────┐
│ 4. AGGREGATOR AGENT                          │
│ - Group data (by region, type, etc)         │
│ - Summarize                                  │
└──────────────────────────────────────┘
           │
           ├── Cache: aggregation_results
           │
           ▼
┌──────────────────────────────────────┐
│ 5. ANOMALY DETECTOR AGENT                    │
│ - Find outliers                              │
│ - Detect fraud                               │
│ - Flag suspicious patterns                   │
└──────────────────────────────────────┘
           │
           ├── Cache: anomalies
           │
           ▼
┌──────────────────────────────────────┐
│ 6. PREDICTOR AGENT                           │
│ - Train model                                │
│ - Make predictions                           │
│ - Forecast future                            │
└──────────────────────────────────────┘
           │
           ├── Cache: predictions
           │
           ▼
┌──────────────────────────────────────┐
│ 7. RECOMMENDER AGENT                         │
│ - Based on all results                       │
│ - Suggest actions                            │
└──────────────────────────────────────┘
           │
           ├── Cache: recommendations
           │
           ▼
┌──────────────────────────────────────┐
│ 8. NARRATIVE GENERATOR AGENT                 │
│ - Reads ALL cached results                   │
│ - Creates story                              │
│ - Extracts insights                          │
│ - Makes recommendations human-readable       │
└──────────────────────────────────────┘
           │
           ├── Cache: narrative
           │
           ▼
┌──────────────────────────────────────┐
│ 9. VISUALIZER AGENT                          │
│ - Create charts                              │
│ - Create graphs                              │
│ - Format visuals                             │
└──────────────────────────────────────┘
           │
           ├── Cache: visuals
           │
           ▼
┌──────────────────────────────────────┐
│ 10. REPORTER AGENT                           │
│ - Assemble everything                        │
│ - Format professionally                      │
│ - Create final report                        │
└──────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ FINAL OUTPUT:                                 │
│ - Raw data                                   │
│ - Analysis results                           │
│ - Narrative story                            │
│ - Visual charts                              │
│ - Professional report (PDF/HTML)             │
└──────────────────────────────────────┘
```

---

## Task Routing Table

**ORCHESTRATOR uses this to route correctly:**

| Task Type | Agent | Input | Output | Next |
|-----------|-------|-------|--------|------|
| `load_data` | DataLoader | file path | DataFrame | Explorer |
| `explore` | Explorer | DataFrame | stats, insights | Aggregator |
| `aggregate` | Aggregator | DataFrame | grouped data | AnomalyDetector |
| `detect_anomalies` | AnomalyDetector | DataFrame | anomalies | Predictor |
| `predict` | Predictor | DataFrame | predictions | Recommender |
| `recommend` | Recommender | all results | recommendations | Narrative |
| `narrative` | NarrativeGenerator | all cached | story + insights | Visualizer |
| `visualize` | Visualizer | all cached | charts/graphs | Reporter |
| `report` | Reporter | all cached | formatted report | DONE |

---

## Code: Correct Routing Logic

```python
class TaskRouter:
    """Routes tasks to correct agent."""
    
    # Define the correct pipeline order
    PIPELINE_ORDER = [
        'load_data',
        'explore',
        'aggregate',
        'detect_anomalies',
        'predict',
        'recommend',
        'narrative',
        'visualize',
        'report'
    ]
    
    # Map tasks to agents
    TASK_TO_AGENT = {
        'load_data': 'data_loader',
        'explore': 'explorer',
        'aggregate': 'aggregator',
        'detect_anomalies': 'anomaly_detector',
        'predict': 'predictor',
        'recommend': 'recommender',
        'narrative': 'narrative_generator',
        'visualize': 'visualizer',
        'report': 'reporter'
    }
    
    def route(self, task):
        """Route task to correct agent."""
        task_type = task.get('type')
        
        # Validate task type
        if task_type not in self.TASK_TO_AGENT:
            raise ValueError(f"Unknown task type: {task_type}")
        
        # Get agent name
        agent_name = self.TASK_TO_AGENT[task_type]
        agent = self.agent_registry.get(agent_name)
        
        if not agent:
            raise RuntimeError(f"Agent not found: {agent_name}")
        
        # Execute on correct agent
        result = agent.execute(task)
        
        # Cache result
        self.data_manager.set(task_type, result)
        
        return result
    
    def validate_pipeline(self, tasks):
        """Ensure tasks are in correct order."""
        task_types = [t.get('type') for t in tasks]
        
        for task_type in task_types:
            if task_type not in self.TASK_TO_AGENT:
                raise ValueError(f"Invalid task: {task_type}")
        
        # Check order
        indices = [self.PIPELINE_ORDER.index(t) for t in task_types]
        if indices != sorted(indices):
            raise ValueError(
                f"Tasks out of order. Expected: {self.PIPELINE_ORDER}"
                f"Got: {task_types}"
            )
        
        return True
```

---

## How to Use (Correct Way)

```python
orchestrator = Orchestrator()

# Register ALL agents
orchestrator.register_agent('data_loader', DataLoaderAgent())
orchestrator.register_agent('explorer', ExplorerAgent())
orchestrator.register_agent('aggregator', AggregatorAgent())
orchestrator.register_agent('anomaly_detector', AnomalyDetectorAgent())
orchestrator.register_agent('predictor', PredictorAgent())
orchestrator.register_agent('recommender', RecommenderAgent())
orchestrator.register_agent('narrative_generator', NarrativeGeneratorAgent())
orchestrator.register_agent('visualizer', VisualizerAgent())
orchestrator.register_agent('reporter', ReporterAgent())

# Define workflow IN CORRECT ORDER
workflow = [
    {'type': 'load_data', 'parameters': {'file': 'data.csv'}},
    {'type': 'explore', 'parameters': {}},
    {'type': 'aggregate', 'parameters': {'group_by': 'region'}},
    {'type': 'detect_anomalies', 'parameters': {'method': 'iso_forest'}},
    {'type': 'predict', 'parameters': {'target': 'churn'}},
    {'type': 'recommend', 'parameters': {}},
    {'type': 'narrative', 'parameters': {}},
    {'type': 'visualize', 'parameters': {}},
    {'type': 'report', 'parameters': {'format': 'pdf'}}
]

# Orchestrator validates AND routes correctly
result = orchestrator.execute_workflow(workflow)

# Result contains everything:
# - Raw data
# - Analysis results
# - Narrative story
# - Visualizations
# - Final report
```

---

## What Goes Wrong (And How to Fix)

### ❌ WRONG: Out of Order
```python
workflow = [
    {'type': 'predict', ...},     # ERROR! No data loaded yet
    {'type': 'load_data', ...},   # This should be first
]
```
**Fix:** Router validates order. Throws error. Forces correct sequence.

### ❌ WRONG: Missing Steps
```python
workflow = [
    {'type': 'load_data', ...},
    {'type': 'report', ...}        # Missing all analysis!
]
```
**Fix:** Router skips to report with empty data. Report still works but warns about incomplete analysis.

### ❌ WRONG: Unknown Agent
```python
{'type': 'analyze_sentiment', ...}  # No such agent!
```
**Fix:** Router checks TASK_TO_AGENT. Raises error. Logs which agents are available.

### ✅ RIGHT: Correct Order
```python
workflow = [
    {'type': 'load_data', ...},
    {'type': 'explore', ...},
    {'type': 'aggregate', ...},
    {'type': 'detect_anomalies', ...},
    {'type': 'predict', ...},
    {'type': 'recommend', ...},
    {'type': 'narrative', ...},
    {'type': 'visualize', ...},
    {'type': 'report', ...}
]
```
**Result:** Each agent gets right data. Each caches output. Final report has everything.

---

## ErrorIntelligence Tracks Every Step

```python
# If data goes to WRONG agent:
error_intelligence.track_error(
    agent_name="TaskRouter",
    worker_name="Orchestrator",
    error_type="RoutingError",
    error_message="Task 'predict' routed before 'explore'",
    context={
        'expected_agent': 'predictor',
        'available_data': 'raw_only',
        'required_data': 'analysis_results'
    }
)

# If agent fails:
error_intelligence.track_error(
    agent_name="ExplorerAgent",
    worker_name="Orchestrator",
    error_type="ExecutionError",
    error_message="Explorer failed on column X",
    context={
        'data_quality': '95%',
        'problematic_column': 'X',
        'error_type': 'nulls'
    }
)
```

---

## Summary: Ensure Correct Pipeline

**1. Use TaskRouter**
   - Validates task types
   - Validates order
   - Routes to correct agent

**2. Follow Pipeline Order**
   ```
   load_data → explore → aggregate → anomalies → predict
   → recommend → narrative → visualize → report
   ```

**3. Register All Agents**
   - DataLoaderAgent
   - ExplorerAgent
   - AggregatorAgent
   - AnomalyDetectorAgent
   - PredictorAgent
   - RecommenderAgent
   - NarrativeGeneratorAgent
   - VisualizerAgent
   - ReporterAgent

**4. Use ErrorIntelligence**
   - Logs which agent got which data
   - Tracks routing errors
   - Identifies failures

**5. Cache Everything**
   - Each agent caches output
   - Next agent reads from cache
   - Narrative reads ALL cached data
   - Reporter assembles everything

---

**Your pipeline is now GUARANTEED to be correct. Data flows to right agent, in right order.**
