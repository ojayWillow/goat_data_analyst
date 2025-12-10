# Week 3 Plan - Orchestration Layer

**Status:** Planned (Not Started)
**Scope:** Dec 17–21, 2025
**Goal:** Build a simple, robust orchestration layer on top of the 5 Week 2 agents.

---

## 1. Objectives

- Coordinate all 5 agents (AnomalyDetector, Predictor, Recommender, Reporter, Visualizer) via a single Orchestrator.
- Provide **one flexible pipeline** that can enable/disable agents via config.
- Expose a **single API endpoint** (`/analyze`) that runs the pipeline.
- Keep execution **sequential, fail-fast, and simple**.
- Add ~50 tests without increasing complexity.

---

## 2. Core Decisions (Locked In)

1. **Parallelization:**
   - No parallel execution in Week 3.
   - All agents run sequentially in a deterministic order.

2. **Pipelines:**
   - One pipeline implementation, **config-driven**.
   - Predefined configs like `full`, `quick`, `anomaly_focus`, `prediction_focus` are just presets over the same mechanism.

3. **Caching:**
   - No caching in Week 3.
   - We measure first; if performance becomes a real issue, caching moves to Week 4+.

4. **Error Handling:**
   - **Fail-fast**: if any agent raises, orchestration stops and returns an error.
   - Simple per-agent `try/except`, no complex retry logic here (retry stays inside agents where it already exists).

5. **API Design:**
   - Single POST endpoint: `/analyze`.
   - Optional `pipeline` preset and `agents` config block to toggle agent usage.

6. **Logging:**
   - Use existing `core.structured_logger`.
   - For each agent call, log `agent_completed` with `elapsed_seconds` and `status`.

7. **Communication Format:**
   - In-process Python **dicts and DataFrames**.
   - No queues, no network messaging.

8. **Performance Target:**
   - Maintain current performance: **1K rows < 30 seconds** end-to-end.
   - Do not regress.

---

## 3. Orchestrator Design

### 3.1 Orchestrator Class

File: `agents/orchestrator/orchestrator.py`

Responsibilities:
- Hold instances of all 5 agents.
- Accept a DataFrame + config dict.
- Run agents sequentially according to config.
- Aggregate results into a single response dict.
- Fail-fast on errors, with clear error payloads.

Pseudocode:

```python
class Orchestrator:
    def __init__(self):
        self.anomaly_detector = AnomalyDetector()
        self.predictor = Predictor()
        self.recommender = Recommender()
        self.reporter = Reporter()
        self.visualizer = Visualizer()
        self.logger = get_structured_logger("Orchestrator")

    def execute(self, df: pd.DataFrame, config: dict) -> dict:
        if df is None or df.empty:
            return {"status": "error", "error": "No data provided"}

        results: dict[str, Any] = {}

        # 1) Anomaly detector
        if config.get("run_anomaly_detector", True):
            try:
                start = time.time()
                self.anomaly_detector.set_data(df)
                results["anomalies"] = self.anomaly_detector.detect_ensemble()
                self.logger.info("agent_completed", {
                    "agent": "AnomalyDetector",
                    "elapsed_seconds": time.time() - start,
                    "status": "success",
                })
            except Exception as e:
                return {"status": "error", "agent": "AnomalyDetector", "error": str(e)}

        # 2) Predictor, 3) Recommender, 4) Reporter, 5) Visualizer
        # Same pattern as above, guarded by config flags.

        return {"status": "success", "results": results}
```

### 3.2 Config-Driven Pipelines

File: `agents/orchestrator/pipeline_config.py`

```python
PIPELINE_CONFIGS = {
    "full": {
        "run_anomaly_detector": True,
        "run_predictor": True,
        "run_recommender": True,
        "run_reporter": True,
        "run_visualizer": True,
    },
    "quick": {
        "run_anomaly_detector": True,
        "run_predictor": False,
        "run_recommender": True,
        "run_reporter": True,
        "run_visualizer": False,
    },
    "anomaly_focus": {
        "run_anomaly_detector": True,
        "run_predictor": False,
        "run_recommender": True,
        "run_reporter": False,
        "run_visualizer": False,
    },
    "prediction_focus": {
        "run_anomaly_detector": False,
        "run_predictor": True,
        "run_recommender": False,
        "run_reporter": True,
        "run_visualizer": False,
    },
}
```

A simple helper will merge preset + overrides:

```python
def resolve_config(pipeline: str | None, override: dict | None) -> dict:
    base = PIPELINE_CONFIGS.get(pipeline or "full", PIPELINE_CONFIGS["full"]).copy()
    if override:
        base.update(override)
    return base
```

---

## 4. API Design (FastAPI)

File: `api/main.py`

### Endpoint: `POST /analyze`

Request body (example):

```json
{
  "data": {"columns": [...], "rows": [...]},
  "pipeline": "full",
  "agents": {
    "run_anomaly_detector": true,
    "run_predictor": false,
    "run_recommender": true,
    "run_reporter": true,
    "run_visualizer": false
  }
}
```

Response (success):

```json
{
  "status": "success",
  "results": {
    "anomalies": { ... },
    "predictions": { ... },
    "recommendations": { ... },
    "report": { ... },
    "charts": { ... }
  }
}
```

Response (error):

```json
{
  "status": "error",
  "agent": "Predictor",
  "error": "<message>"
}
```

### Endpoint: `GET /health`

Simple health check.

```json
{
  "status": "healthy"
}
```

---

## 5. Week 3 Daily Breakdown

### Day 1 – Orchestrator Core (10 tests)

**Build:**
- `Orchestrator` class
- `execute(df, config)` method (sequential)
- Fail-fast error strategy
- Basic timing logs per agent

**Tests (examples):**
- Orchestrator initializes correctly
- Executes with all agents enabled
- Executes with some agents disabled
- Fails when no data provided
- Fails fast when one agent raises
- Returns structured `{"status": "success", "results": {...}}`
- Performance: 1K rows < 30s (smoke test)

---

### Day 2 – Pipeline Config Layer (10 tests)

**Build:**
- `PIPELINE_CONFIGS` registry
- `resolve_config(pipeline, override)`
- Integration between orchestrator and pipeline configs

**Tests (examples):**
- `full` preset yields all agents
- `quick` preset disables predictor & visualizer
- `anomaly_focus` only runs anomaly + recommender
- Overrides apply on top of preset
- Unknown pipeline falls back to `full`
- Invalid override keys ignored or validated

---

### Day 3 – API Layer (10 tests)

**Build:**
- FastAPI app
- `POST /analyze`
- `GET /health`
- Request/response models (pydantic) for validation

**Tests (examples):**
- Valid request with `full` pipeline returns 200 + `status=success`
- Invalid data shape returns 400/422
- Custom `agents` override works
- Health endpoint returns 200 + `status=healthy`
- Error from agent surfaces as `status=error` + `agent` name

---

### Day 4 – End-to-End Flows (10 tests)

**Build:**
- Full pipeline tests using real agents on synthetic data
- Edge case handling (missing columns, NaNs, small datasets)

**Tests (examples):**
- End-to-end: data → /analyze → all 5 agents → combined result
- End-to-end: quick pipeline
- Dataset with missing values
- Dataset with anomalies
- Non-numeric target for predictor (validation error surfaced)

---

### Day 5 – Documentation & Polish (10 tests)

**Build:**
- README.md: Orchestrator + API usage
- Examples: Python scripts calling `/analyze`
- Final verification of performance and stability

**Tests (examples):**
- Final full test run: all Week 1–3 tests
- API example script runs successfully (smoke)
- No deprecation warnings

---

## 6. Definition of Done (Week 3)

- ✅ Orchestrator class implemented and tested
- ✅ Single config-driven pipeline in place
- ✅ FastAPI `/analyze` + `/health` endpoints working
- ✅ 50+ new tests for orchestration and API
- ✅ All Week 1–2 tests still passing
- ✅ Performance target maintained (< 30s for 1K rows)
- ✅ Documentation updated (README + examples)

---

**Ready to execute starting Week 3.**
