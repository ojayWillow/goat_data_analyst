# Pipeline Quick Reference

## ✅ CORRECT PIPELINE (FOLLOW THIS ORDER)

```
1. load_data         → DataLoaderAgent
2. explore           → ExplorerAgent
3. aggregate         → AggregatorAgent
4. detect_anomalies  → AnomalyDetectorAgent
5. predict           → PredictorAgent
6. recommend         → RecommenderAgent
7. narrative         → NarrativeGeneratorAgent
8. visualize         → VisualizerAgent
9. report            → ReporterAgent
```

---

## Code Example: CORRECT

```python
orchestrator = Orchestrator()

# Register all agents
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
    {'type': 'load_data', 'parameters': {'file_path': 'data.csv'}},
    {'type': 'explore', 'parameters': {}},
    {'type': 'aggregate', 'parameters': {'group_by': 'region'}},
    {'type': 'detect_anomalies', 'parameters': {'method': 'iso_forest'}},
    {'type': 'predict', 'parameters': {'prediction_type': 'trend'}},
    {'type': 'recommend', 'parameters': {}},
    {'type': 'narrative', 'parameters': {}},
    {'type': 'visualize', 'parameters': {'chart_type': 'bar'}},
    {'type': 'report', 'parameters': {'report_type': 'comprehensive'}}
]

# Execute - TaskRouter validates order and routes correctly
result = orchestrator.execute_workflow(workflow)
```

---

## ❌ WRONG Examples

### WRONG 1: Out of Order
```python
workflow = [
    {'type': 'predict', ...},     # ERROR! Before load_data
    {'type': 'load_data', ...},   # This must be FIRST
]
# TaskRouter throws: ERROR: Tasks out of order!
```

### WRONG 2: Missing Steps
```python
workflow = [
    {'type': 'load_data', ...},
    {'type': 'report', ...}  # Missing explore, aggregate, etc!
]
# TaskRouter throws: ERROR: Tasks out of order!
```

### WRONG 3: Unknown Task Type
```python
workflow = [
    {'type': 'load_data', ...},
    {'type': 'analyze_sentiment', ...}  # Not a valid task type
]
# TaskRouter throws: ERROR: Unknown task type
```

---

## What TaskRouter Does

### 1. Validates Each Task
```python
# Check if task type is valid
if task_type not in TASK_TO_AGENT:
    raise error("Invalid task type")
```

### 2. Validates Pipeline Order
```python
# Check all tasks are in correct order
if task_indices != sorted(task_indices):
    raise error("Tasks out of order")
```

### 3. Routes to Correct Agent
```python
# Look up agent for task
agent = TASK_TO_AGENT[task_type]  # e.g. 'explore' -> 'explorer'
agent.execute(task)  # Run on correct agent
```

### 4. Caches Result
```python
# Store result for next agents
data_manager.set(task_type, result)
```

---

## Data Flow

```
load_data
   │
   └── Cached: loaded_data
       │
explore (reads cached_data)
   │
   └── Cached: exploration_results
       │
aggregate (reads cached_data)
   │
   └── Cached: aggregation_results
       │
detect_anomalies (reads cached_data)
   │
   └── Cached: anomalies
       │
predict (reads cached_data)
   │
   └── Cached: predictions
       │
recommend (reads cached_data)
   │
   └── Cached: recommendations
       │
narrative (reads ALL cached data)
   │
   └── Creates: story + insights
       │
visualize (reads cached_data)
   │
   └── Creates: charts
       │
report (assembles everything)
   │
   └── FINAL OUTPUT
```

---

## Testing Pipeline

```python
# Test correct routing
from agents.orchestrator.workers.task_router import TaskRouter

router = TaskRouter(agent_registry, data_manager)

# Get pipeline info
info = router.get_pipeline_info()
print(info['order'])  # ['load_data', 'explore', ...]

# Validate workflow
workflow = [...]
router.validate_pipeline_order(workflow)  # True or raises error
```

---

## Key Points

✓ **Always follow the pipeline order**
✓ **All 9 steps in same workflow**
✓ **TaskRouter validates automatically**
✓ **Each agent caches its output**
✓ **Narrative reads all cached data**
✓ **Report assembles final output**

---

## Files

- `CORRECT_PIPELINE_ROUTING.md` - Detailed explanation
- `agents/orchestrator/workers/task_router.py` - Implementation
- This file - Quick reference

---

**Your pipeline is now guaranteed to route correctly!**
