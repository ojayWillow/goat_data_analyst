# Error Resilience & Intelligence Rollout Plan

## 1. Current System – Honest Assessment

### 1.1 Architecture (Good)

The current design is **strong** conceptually:

- **Agent-level resilience** via `core.error_recovery`:
  - `@retry_on_error` decorator wraps agent methods.
  - Handles **transient errors** (network, IO, temporary glitches).
  - Uses **exponential backoff** and optional **fallbacks**.
- **Worker-level observability** via `ErrorIntelligence`:
  - Workers call `track_success()` and `track_error()`.
  - `ErrorTracker` (singleton) aggregates metrics across all agents and workers.
  - `PatternAnalyzer`, `WorkerHealth`, `FixRecommender`, and `LearningEngine` build insights.
- **ProjectManager** uses these metrics to compute an **honest health score** and recommendations.

Conceptually, this is an **enterprise-grade** two-layer system:

- Agents = *resilience* (keep system running).
- Workers = *intelligence* (learn from what happens).

### 1.2 Implementation Gaps (Bad)

- Only **Aggregator** is a full reference implementation:
  - Agent uses `@retry_on_error` on all public methods.
  - Workers (e.g., `StatisticsWorker`) correctly integrate `ErrorIntelligence`.
- Other agents (DataLoader, Explorer, AnomalyDetector, etc.):
  - **Do not** consistently use `@retry_on_error` on their public methods.
  - Workers **do not** integrate `ErrorIntelligence` (no imports, no tracking calls).
- Result:
  - Health report shows **100% test coverage** but **very low operational resilience**.
  - Error Intelligence coverage is **extremely low** (only Aggregator workers integrated).

### 1.3 Core Systems – Do They Need Changes?

#### 1.3.1 `core/error_recovery`

- The `ErrorRecoveryStrategy` and `@retry_on_error` implementation is **solid** for Phase 1:
  - Clear API: `retry`, `_execute_with_timeout`, `with_fallback`, `retry_on_error`, `with_fallback`.
  - Good logging, exponential backoff, optional timeout and fallback.
- **Conclusion**: 
  - **No mandatory changes required now** to start rollout.
  - Future **Phase 2+** improvements (optional):
    - Pass richer context (e.g., retry count) to Error Intelligence.
    - Different strategies per error type (transient vs data vs logic).

#### 1.3.2 `agents/error_intelligence`

- `ErrorIntelligence` + workers (`ErrorTracker`, `PatternAnalyzer`, `WorkerHealth`, `FixRecommender`, `LearningEngine`) are **ready for rollout**:
  - `ErrorTracker` is a proper singleton.
  - API is clean: `track_success`, `track_error`, `analyze_patterns`, `get_worker_health`, `get_recommendations`, `record_fix`.
- **Conclusion**:
  - **No core changes are required** for Phase 1 rollout.
  - Future **Phase 2+** improvements (optional):
    - Include retry metadata from `core.error_recovery`.
    - Add error budgets / SLO metrics.


## 2. Target State – What “Good” Looks Like

### 2.1 For Every Agent

- **All public methods** that perform IO, computation, orchestration or user-facing work MUST:
  - Use `@retry_on_error(max_attempts=3, backoff=2)` (or tuned values).
  - Log meaningful context (using `structured_logger` where available).

Examples:

```python
from core.error_recovery import retry_on_error

class DataLoader:
    ...

    @retry_on_error(max_attempts=3, backoff=2)
    def load_csv(self, path: str, **kwargs) -> pd.DataFrame:
        ...

    @retry_on_error(max_attempts=3, backoff=2)
    def load_parquet(self, path: str, **kwargs) -> pd.DataFrame:
        ...
```

### 2.2 For Every Worker

- All workers that perform real work (load, transform, analyze, generate, predict) MUST:
  - Import `ErrorIntelligence`.
  - Hold a single instance per worker (`self.error_intelligence`).
  - Track **both** successful executions and failures.

Standard pattern:

```python
from agents.error_intelligence.main import ErrorIntelligence
from .base_worker import BaseWorker, WorkerResult, ErrorType

class SomeWorker(BaseWorker):
    def __init__(self):
        super().__init__("SomeWorker")
        self.error_intelligence = ErrorIntelligence()

    def execute(self, **kwargs) -> WorkerResult:
        result = self._create_result(task_type="some_task")
        try:
            # Do work
            result = self._run_task(result, **kwargs)

            # Track success
            self.error_intelligence.track_success(
                agent_name="agent_name",
                worker_name="SomeWorker",
                operation="some_task",
                context={k: v for k, v in kwargs.items() if k != "df"}
            )

            return result

        except Exception as e:
            # Track error
            self.error_intelligence.track_error(
                agent_name="agent_name",
                worker_name="SomeWorker",
                error_type=type(e).__name__,
                error_message=str(e),
                context={k: v for k, v in kwargs.items() if k != "df"}
            )
            raise
```


## 3. Do We Need to Change Aggregator?

**Aggregator today is the reference model** and is already very close to ideal:

- Agent-level:
  - Uses `@retry_on_error` on all public methods like `apply_window_function`, `apply_rolling_aggregation`, `aggregate_all`, etc.
- Worker-level:
  - At least `StatisticsWorker` correctly integrates `ErrorIntelligence` and tracks success/error.

For Phase 1, **Aggregator does NOT require changes** to the error system.

Future optional refinements:

- Standardize **all** Aggregator workers to follow the same Error Intelligence pattern as `StatisticsWorker`.
- Ensure context keys are consistent (e.g., always include `task_type`, `rows`, `columns` where relevant).


## 4. Rollout Roadmap

### 4.1 Phase 0 – Baseline & Agreement (You Are Here)

**Goals:**
- Agree that:
  - Every agent should use `@retry_on_error` on public methods.
  - Every worker should integrate `ErrorIntelligence`.
- Confirm core systems (`core.error_recovery` and `agents.error_intelligence`) do **not** need changes to start.

**Status:**
- ✅ Architecture reviewed
- ✅ Gaps identified
- ✅ No core changes required for Phase 1


### 4.2 Phase 1 – Agent-Level Resilience (Retry Everywhere)

**Objective:** Ensure all agents have consistent retry behavior.

**Steps:**
1. **Create Agent Retry Guide** (short file or section):
   - Where to import `retry_on_error`.
   - Which methods to decorate.
   - Recommended defaults: `max_attempts=3`, `backoff=2`.

2. **Inventory all agents:**
   - `data_loader`, `explorer`, `anomaly_detector`, `orchestrator`, `predictor`, `reporter`, `report_generator`, `visualizer`, `project_manager`, etc.

3. **For each agent:**
   - Identify public methods (API surface).
   - Add `@retry_on_error` decorator.
   - Ensure errors are logged with useful context.

4. **Update ProjectManager health report** to include:
   - `retry_coverage`: number of agents using `retry_on_error` / total agents.
   - Simple breakdown: list of agents missing retries.

**Exit Criteria:**
- All top-level agents use `@retry_on_error` on their main public methods.
- ProjectManager shows **100% retry coverage**.


### 4.3 Phase 2 – Worker-Level Intelligence (ErrorIntelligence Everywhere)

**Objective:** Ensure all workers report into Error Intelligence.

**Steps:**
1. **Create Worker Integration Guide** (this is mostly done in `ERROR-INTELLIGENCE-GUIDE.md`):
   - Import pattern.
   - Where to instantiate `ErrorIntelligence`.
   - How to wrap `execute` with tracking.

2. **Standardize a base pattern** in each agent’s `base_worker.py`:
   - Option A (Phase 2): Manual tracking in each worker (current style).
   - Option B (Phase 3): Add a `safe_execute()` in `BaseWorker` that auto-wraps `execute()` with tracking.

3. **For each agent with workers** (e.g., `data_loader`, `explorer`, `aggregator`, etc.):
   - Add `self.error_intelligence = ErrorIntelligence()` in `__init__` of each worker.
   - Add tracking calls in `execute()` around the work.

4. **Extend ProjectManager’s ErrorIntelligenceChecker**:
   - Already updated to scan **workers**, not just main agent files.
   - Confirm it now correctly counts Aggregator as having Error Intelligence.

**Exit Criteria:**
- ProjectManager shows:
  - `Error Intelligence coverage`: close to or at **100% of agents with workers**.
  - Clear list of any remaining agents or workers not integrated.


### 4.4 Phase 3 – Automation & Intelligence

**Objective:** Reduce manual work and enrich intelligence.

**Ideas (for later sessions):**

1. **BaseWorker Auto-Tracking**
   - Implement `BaseWorker.safe_execute()` that:
     - Calls `execute()`.
     - Automatically calls `track_success` / `track_error`.
   - Workers then only implement `_run_task()`, not tracking boilerplate.

2. **Retry Context Bridging**
   - Have `@retry_on_error` pass retry metadata into Error Intelligence:
     - `retry_attempts`, `final_failure`, `is_transient`.
   - Error Intelligence can distinguish:
     - One catastrophic failure vs many small transient ones.

3. **Error Budgets / SLOs**
   - Define thresholds per agent:
     - e.g., “This agent can have 5% failure rate before alerting.”
   - Use `WorkerHealth` + retry metrics to flag SLO breaches.


## 5. Concrete File to Add Now

Create a new guide file at the repository root (suggested name):

`ERROR-RESILIENCE-ROLLING-PLAN.md`

Content:
- Summary of current state.
- Confirmation that core systems are ready.
- Clear step-by-step plan:
  - Phase 1: Agent-level retries.
  - Phase 2: Worker-level Error Intelligence.
  - Phase 3: Automation & advanced intelligence.
- Templates for:
  - Agent methods with `@retry_on_error`.
  - Workers with `ErrorIntelligence` tracking.
- Checklists to use per agent in upcoming sessions.

This file will be the **single source of truth** for “How we harden all agents and workers for resilience + intelligence”.


## 6. Summary – Direct Answers

- **Do we need to update anything in `core/error_recovery` right now?**
  - **No.** It’s good enough for rollout. Enhancements can come later.

- **Do we need to update anything in the Error Intelligence system right now?**
  - **No.** It’s already feature-complete for tracking and analysis.
  - The main work is integrating it into more workers.

- **Do we need every agent to use `@retry_on_error`?**
  - **Yes.** For any method that touches IO, heavy compute, or external systems.

- **Do we need every worker to use Error Intelligence?**
  - **Yes.** For any worker that can succeed or fail in a meaningful way.

- **Is the overall system design good?**
  - **Yes – very good architecture.** The problem is not the design, it’s the **partial rollout**.

Next session, this file will guide updating agents & workers one by one until ProjectManager’s health report shows **full coverage and honest resilience.**
