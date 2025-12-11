# Error Intelligence Integration + 4-Week Hardening Plan

**Date:** December 11, 2025  
**Repo:** https://github.com/ojayWillow/goat_data_analyst  
**Goal:** Integrate error_intelligence into all workers + Execute 4-week hardening to reach Health ≥ 90

---

## WHAT YOU NEED TO DO

### 1. Error Intelligence Integration (ALL 11 Aggregator Workers)

**Current Problem:**
- Aggregator has 11 workers (138.8KB total)
- Workers execute operations but don't track errors systematically
- No error intelligence layer connected

**What To Do:**
Every worker's `execute()` method needs this pattern:

#### BEFORE (Example):
```python
# agents/aggregator/workers/statistical_worker.py

class StatisticalWorker:
    def execute(self, data):
        # Does the work
        return {"mean": data.mean(), "std": data.std()}
```

#### AFTER (Correct Pattern):
```python
# agents/aggregator/workers/statistical_worker.py
from core.error_intelligence import ErrorIntelligence

class StatisticalWorker:
    def __init__(self):
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, data):
        try:
            # Original work remains IDENTICAL
            result = {"mean": data.mean(), "std": data.std()}
            
            # Track success
            self.error_intelligence.track_success(
                agent="aggregator.statistical_worker",
                operation="calculate_statistics"
            )
            
            return result
            
        except Exception as e:
            # Track error
            self.error_intelligence.track_error(
                agent="aggregator.statistical_worker",
                operation="calculate_statistics",
                error=e,
                context={"data_shape": data.shape if hasattr(data, 'shape') else None}
            )
            
            # Re-raise to maintain existing behavior
            raise
```

**Apply This Pattern To:**
1. `agents/aggregator/workers/statistical_worker.py`
2. `agents/aggregator/workers/correlation_worker.py`
3. `agents/aggregator/workers/groupby_worker.py`
4. `agents/aggregator/workers/pivot_worker.py`
5. `agents/aggregator/workers/time_series_worker.py`
6. `agents/aggregator/workers/distribution_worker.py`
7. `agents/aggregator/workers/outlier_worker.py`
8. `agents/aggregator/workers/normalization_worker.py`
9. `agents/aggregator/workers/feature_engineering_worker.py`
10. `agents/aggregator/workers/data_quality_worker.py`
11. `agents/aggregator/workers/summary_worker.py`

**Rules:**
- Don't change the worker logic
- Add `ErrorIntelligence()` in `__init__`
- Wrap `execute()` in try/except
- Track success on normal path
- Track error + re-raise on failure

---

### 2. Four-Week Hardening Plan (Health: 59 → 90+)

## Week 1: Agent Readiness (Dec 10-14)

**Mission:** Test all 7 untested agents

**Untested Agents:**
1. aggregator - 11 workers
2. explorer - 14 workers
3. narrative_generator - 4 workers
4. orchestrator - 5 workers
5. recommender - 6 workers
6. reporter - 6 workers
7. visualizer - 9 workers

**For Each Agent, Create:**

File: `tests/test_{agent_name}.py`

```python
import pytest
from agents.{agent_name} import {AgentName}

def test_agent_initialization():
    """Agent initializes without error"""
    agent = {AgentName}()
    assert agent is not None

def test_agent_execute_valid_input():
    """Agent executes with valid input"""
    agent = {AgentName}()
    result = agent.execute(valid_input)
    assert result is not None
    assert "expected_key" in result

def test_agent_execute_invalid_input():
    """Agent handles invalid input gracefully"""
    agent = {AgentName}()
    with pytest.raises(ValueError):
        agent.execute(None)

def test_agent_output_format():
    """Agent output matches expected format"""
    agent = {AgentName}()
    result = agent.execute(valid_input)
    assert isinstance(result, dict)
    assert "status" in result

def test_agent_error_handling():
    """Agent error messages are helpful"""
    agent = {AgentName}()
    try:
        agent.execute(bad_input)
    except Exception as e:
        assert "helpful message" in str(e)
```

**Daily Tasks:**

**Day 1 (Tue, Dec 10):**
- [ ] Create `tests/test_aggregator.py` (5 tests)
- [ ] Create `tests/test_explorer.py` (5 tests)
- [ ] Run: `pytest tests/test_aggregator.py tests/test_explorer.py -v`

**Day 2 (Wed, Dec 11):**
- [ ] Create `tests/test_narrative_generator.py` (5 tests)
- [ ] Create `tests/test_orchestrator.py` (5 tests)
- [ ] Run: `pytest tests/ -v`

**Day 3 (Thu, Dec 12):**
- [ ] Create `tests/test_recommender.py` (5 tests)
- [ ] Create `tests/test_reporter.py` (5 tests)
- [ ] Create `tests/test_visualizer.py` (5 tests)
- [ ] Run: `pytest tests/ -v`

**Day 4 (Fri, Dec 13):**
- [ ] Fix any failing tests
- [ ] Verify Health Score: `python scripts/test_project_manager.py`
- [ ] Target: Health ≥ 70

**Week 1 Exit Criteria:**
- ✅ All 7 agents have tests
- ✅ All tests passing
- ✅ Health Score ≥ 70
- ✅ No unhandled exceptions

---

## Week 2: Pipeline Testing (Dec 15-21)

**Mission:** Validate agents work together

**Pipeline Flow:**
```
File Input → DataLoader → Explorer → Aggregator → Recommender → Reporter
```

**Integration Tests:**

File: `tests/test_pipeline_integration.py`

```python
def test_loader_to_explorer():
    """Data flows from loader to explorer"""
    loader = DataLoader()
    data = loader.load('sample.csv')
    
    explorer = Explorer()
    result = explorer.execute(data)
    
    assert result is not None
    assert "columns" in result

def test_explorer_to_aggregator():
    """Explored data passes to aggregator"""
    explorer = Explorer()
    explored = explorer.execute(data)
    
    aggregator = Aggregator()
    result = aggregator.execute(explored)
    
    assert result is not None

def test_full_pipeline():
    """Complete pipeline works end-to-end"""
    # Load
    loader = DataLoader()
    data = loader.load('sample.csv')
    
    # Explore
    explorer = Explorer()
    exploration = explorer.execute(data)
    
    # Aggregate
    aggregator = Aggregator()
    aggregation = aggregator.execute(exploration)
    
    # Recommend
    recommender = Recommender()
    recommendations = recommender.execute(aggregation)
    
    # Report
    reporter = Reporter()
    report = reporter.execute(recommendations)
    
    assert report is not None
    assert "narrative" in report
```

**Daily Tasks:**

**Day 5-6 (Sat-Sun, Dec 14-15):**
- [ ] Create `tests/test_pipeline_integration.py`
- [ ] Test 2-agent chains (5 tests)
- [ ] Test 3-agent chains (5 tests)

**Day 7-8 (Mon-Tue, Dec 16-17):**
- [ ] Test full 5-agent pipeline (5 tests)
- [ ] Test error isolation (one agent fails, others continue)
- [ ] Test data type consistency across agents

**Day 9 (Wed, Dec 18):**
- [ ] Performance baseline: 1K rows → full pipeline → 10s
- [ ] Memory test: 100K rows uses ≤ 1GB

**Day 10 (Thu, Dec 19):**
- [ ] Verify Health Score: `python scripts/test_project_manager.py`
- [ ] Target: Health ≥ 80

**Week 2 Exit Criteria:**
- ✅ 20 integration tests passing
- ✅ Full pipeline works
- ✅ Health Score ≥ 80
- ✅ Performance: 1K rows in 10s

---

## Week 3: Narrative & Reports (Dec 22-28)

**Mission:** Make output understandable

**Narrative Generator Flow:**
```
Analysis Results → Insight Extractor → Problem Identifier → Action Recommender → Story Builder → Narrative
```

**What To Build:**

**File:** `agents/narrative_generator/workers/insight_extractor.py`
```python
class InsightExtractor:
    def extract_anomalies(self, results):
        """Extract key anomalies"""
        return {
            "count": len(results["anomalies"]),
            "severity": "high" if count > 10 else "medium",
            "top_anomalies": results["anomalies"][:5]
        }
    
    def extract_predictions(self, results):
        """Extract prediction insights"""
        return {
            "accuracy": results["accuracy"],
            "confidence": results["confidence"],
            "trend": "increasing" if slope > 0 else "decreasing"
        }
```

**File:** `agents/narrative_generator/workers/story_builder.py`
```python
class StoryBuilder:
    def build_narrative(self, insights, problems, actions):
        """Build readable narrative"""
        return {
            "headline": f"Your data shows {insights['anomaly_count']} anomalies",
            "summary": f"Found {len(problems)} issues, {len(actions)} recommendations",
            "problems": problems,
            "actions": actions,
            "next_steps": [actions[0]["action"], actions[1]["action"]]
        }
```

**Daily Tasks:**

**Day 11-12 (Fri-Sat, Dec 20-21):**
- [ ] Build `insight_extractor.py`
- [ ] Build `problem_identifier.py`
- [ ] Test: insights extracted correctly (10 tests)

**Day 13-14 (Sun-Mon, Dec 22-23):**
- [ ] Build `action_recommender.py`
- [ ] Build `story_builder.py`
- [ ] Test: narratives are clear (10 tests)

**Day 15 (Tue, Dec 24):**
- [ ] Integrate narrative into pipeline
- [ ] Test: pipeline produces narrative
- [ ] Verify Health Score: `python scripts/test_project_manager.py`
- [ ] Target: Health ≥ 85

**Week 3 Exit Criteria:**
- ✅ Narrative generator working
- ✅ 30 narrative tests passing
- ✅ Health Score ≥ 85
- ✅ Output is human-readable

---

## Week 4: User Experience (Dec 29 - Jan 5)

**Mission:** Production-ready deployment

**User Journey:**

```
STEP 1: FILE UPLOAD
User sees: "Upload CSV/Excel/JSON"
System validates: Format, size, data quality
Output: "✅ File valid" or "❌ Error: reason"

STEP 2: CONFIGURE ANALYSIS
User sees: "Quick / Standard / Deep"
System shows: Expected time, output preview
Output: "Ready to analyze"

STEP 3: RUN ANALYSIS
User sees: Progress bar "Step 2/5: Detecting patterns..."
System runs: Pipeline with real-time updates
Output: % complete, estimated time remaining

STEP 4: VIEW RESULTS
User sees:
  - TAB 1: Narrative (clear summary)
  - TAB 2: Report (detailed analysis)
  - TAB 3: Charts (visualizations)
System provides: Export (PDF, CSV, JSON)
```

**Error Messages:**

**Bad:**
```
Error: ValueError in line 42
```

**Good:**
```
❌ ERROR: Invalid date format

What went wrong:
  Column "date" contains invalid dates in rows: 15, 42, 87

What to do:
  1. Check your data format (use YYYY-MM-DD)
  2. Fix the invalid rows
  3. Re-upload the file
```

**Daily Tasks:**

**Day 16-17 (Wed-Thu, Dec 25-26):**
- [ ] Create user flow documentation
- [ ] Design error messages (10 scenarios)
- [ ] Create UI mockups (text-based)

**Day 18 (Fri, Dec 27):**
- [ ] Implement progress tracking
- [ ] Test: User sees real-time updates
- [ ] Test: All error messages are helpful

**Day 19 (Sat, Dec 28):**
- [ ] User testing with sample files
- [ ] Document all user scenarios
- [ ] Create user guide

**Day 20 (Sun, Dec 29):**
- [ ] Final verification
- [ ] Verify Health Score: `python scripts/test_project_manager.py`
- [ ] Target: Health ≥ 90
- [ ] 🚀 **PRODUCTION READY**

**Week 4 Exit Criteria:**
- ✅ User flow documented
- ✅ All error messages clear
- ✅ Health Score ≥ 90
- ✅ Ready for production

---

## COMMANDS TO RUN

### Health Check (Run Daily)
```bash
python scripts/test_project_manager.py
```

### Run All Tests
```bash
pytest tests/ -v
```

### Test Specific Agent
```bash
pytest tests/test_aggregator.py -v
```

### Coverage Report
```bash
pytest tests/ --cov=agents --cov-report=html
```

### Baseline Metrics
```bash
bash scripts/baseline_metrics.sh
```

### Production Ready Check
```bash
python -c "
from agents.project_manager import ProjectManager
pm = ProjectManager()
r = pm.execute()
assert r['health']['health_score'] >= 90
print('🚀 PRODUCTION READY')
"
```

---

## SUCCESS METRICS

| Week | Focus | Health | Tests | Status |
|------|-------|--------|-------|--------|
| 1 | Test agents | 70 | 35 | In Progress |
| 2 | Pipeline | 80 | 55 | Not Started |
| 3 | Narrative | 85 | 85 | Not Started |
| 4 | UX | 90+ | 100+ | Not Started |

---

## FINAL CHECKLIST

### Week 1 Complete When:
- [ ] All 7 agents have tests
- [ ] All tests passing
- [ ] Health ≥ 70
- [ ] No crashes on valid input

### Week 2 Complete When:
- [ ] 20 integration tests passing
- [ ] Full pipeline works
- [ ] Health ≥ 80
- [ ] Performance: 1K rows in 10s

### Week 3 Complete When:
- [ ] Narrative generator working
- [ ] 30 narrative tests passing
- [ ] Health ≥ 85
- [ ] Output is readable

### Week 4 Complete When:
- [ ] User flow complete
- [ ] Error messages helpful
- [ ] Health ≥ 90
- [ ] 🚀 Production ready

---

## START NOW

**Step 1:** Integrate error intelligence in aggregator workers (11 files)

**Step 2:** Create tests for aggregator
```bash
# Create file
touch tests/test_aggregator.py

# Add 5 basic tests
pytest tests/test_aggregator.py -v
```

**Step 3:** Repeat for other 6 untested agents

**Step 4:** Track progress
```bash
python scripts/test_project_manager.py
```

---

**Status:** Ready to execute  
**Timeline:** Dec 11, 2025 → Jan 6, 2026  
**Target:** Health 90+, Production Ready

**LET'S BUILD THIS! 🚀**
