# MASTER PLAN: Testing + Hardening + Error Intelligence
**Status:** 🟢 ACTIVE  
**Timeline:** Dec 11-15, 2025 (5 Days)  
**Branch:** `main` only  

---

## WHERE WE ARE

### ✅ WHAT WE HAVE
- **13 Agents**: All exist (Loader, Explorer, Aggregator, Anomaly, Visualizer, etc.)
- **Error Intelligence**: Built + working in Aggregator (13/13 tests passing)
- **Aggregator**: Fully tested + monitored (10 workers)
- **Architecture**: Clean worker pattern

### ❌ WHAT'S MISSING
- **No tests** for Loader, Explorer, Anomaly, Visualizer, Predictor (8 agents)
- **No performance data** (Can we hit 1M rows in <5s?)
- **No Error Intelligence** in untested agents (only Aggregator has it)
- **System improvements**: Config, error recovery, validation (from Hardening Plan)

---

## THE PLAN: Test → Monitor → Harden

**Philosophy:** We test existing agents FIRST. Only add monitoring to proven code.

---

## PHASE 1: DATA LOADER - TEST + MONITOR (Day 1)
**Goal:** Prove the Loader works with real data.

### Step 1.1: Create Tests (TDD) - 3 hours
**File:** `scripts/test_data_loader.py`

```python
def test_load_csv_basic():
    \"\"\"Can it load a simple CSV?\"\"\"
    
def test_load_csv_1m_rows():
    \"\"\"Can it load 1M rows in <5s?\"\"\"
    
def test_load_corrupted_csv():
    \"\"\"Does error recovery work?\"\"\"
    
def test_load_json():
    \"\"\"Can it load JSON?\"\"\"
    
def test_load_parquet():
    \"\"\"Can it load Parquet?\"\"\"
```

**Run:** `pytest scripts/test_data_loader.py -v`  
**Expect:** FAILURES (we haven't fixed anything yet)

### Step 1.2: Fix Failures - 4 hours
- Update `agents/loaders/data_loader.py`
- Add error handling for corrupted files
- Optimize for speed

**Run again:** `pytest scripts/test_data_loader.py -v`  
**Target:** ALL PASS + 1M rows in <5s

### Step 1.3: Add Error Intelligence - 1 hour
**ONLY AFTER TESTS PASS**

Add to Loader workers:
```python
from agents.error_intelligence.main import ErrorIntelligence

class CSVWorker:
    def __init__(self):
        self.error_intelligence = ErrorIntelligence()
    
    def execute(self, **kwargs):
        try:
            result = self._load_csv(**kwargs)
            self.error_intelligence.track_success(
                agent_name="loader",
                worker_name="CSVWorker",
                operation="load_csv"
            )
            return result
        except Exception as e:
            self.error_intelligence.track_error(...)
            raise
```

### Step 1.4: Verify Monitoring - 30 min
**File:** `scripts/test_error_intelligence_loader.py`

```python
def test_loader_tracking():
    ei = ErrorIntelligence()
    ei.error_tracker.clear()
    
    loader = DataLoader()
    loader.execute(file_path="test.csv")
    
    patterns = ei.error_tracker.get_patterns()
    assert patterns["loader"]["successes"] > 0
```

**Commit:** `git commit -m "feat: Data Loader tested + monitored"`

---

## PHASE 2: DATA EXPLORER - TEST + MONITOR (Day 2)
**Goal:** Prove the Explorer works at scale.

### Step 2.1: Create Tests - 3 hours
**File:** `scripts/test_data_explorer.py`

```python
def test_explore_numeric_basic():
    \"\"\"Basic stats work?\"\"\"
    
def test_explore_numeric_1m_rows():
    \"\"\"Stats on 1M rows in <3s?\"\"\"
    
def test_explore_categorical():
    \"\"\"Categorical analysis works?\"\"\"
    
def test_explore_missing_data():
    \"\"\"Handles missing data?\"\"\"
```

### Step 2.2: Fix Failures - 4 hours
- Update `agents/explorers/data_explorer.py`
- Optimize statistical operations
- Add missing data handling

**Target:** ALL PASS + 1M rows in <3s

### Step 2.3: Add Error Intelligence - 1 hour
Add to Explorer workers (same pattern as Loader)

### Step 2.4: Verify Monitoring - 30 min
**File:** `scripts/test_error_intelligence_explorer.py`

**Commit:** `git commit -m "feat: Data Explorer tested + monitored"`

---

## PHASE 3: INTEGRATION TEST (Day 3)
**Goal:** Full pipeline works end-to-end.

### Step 3.1: Create Integration Tests - 4 hours
**File:** `scripts/test_full_pipeline.py`

```python
def test_load_explore_aggregate():
    \"\"\"Load → Explore → Aggregate\"\"\"
    loader = DataLoader()
    data = loader.execute(file_path="test.csv")
    
    explorer = Explorer()
    stats = explorer.execute(data=data)
    
    aggregator = Aggregator()
    result = aggregator.execute(data=data)
    
    assert result.success
```

### Step 3.2: Fix Integration Issues - 4 hours
- Fix data flow between agents
- Ensure error tracking works across pipeline

**Target:** Full pipeline runs without errors

**Commit:** `git commit -m "feat: Full pipeline integration tested"`

---

## PHASE 4: ANOMALY + VISUALIZER (Day 4)
**Goal:** Test detection and visualization.

### Step 4.1: Anomaly Detector Tests - 3 hours
**File:** `scripts/test_anomaly_detector.py`

### Step 4.2: Visualizer Tests - 3 hours
**File:** `scripts/test_visualizer.py`

### Step 4.3: Add Error Intelligence - 2 hours
Add monitoring to both agents

**Commit:** `git commit -m "feat: Anomaly + Visualizer tested + monitored"`

---

## PHASE 5: PREDICTOR + DOCS (Day 5)
**Goal:** Test prediction + document everything.

### Step 5.1: Predictor Tests - 3 hours
**File:** `scripts/test_predictor.py`

### Step 5.2: Add Error Intelligence - 1 hour

### Step 5.3: Documentation - 4 hours
- Update ERROR-INTELLIGENCE-GUIDE.md with real examples
- Create PERFORMANCE-BENCHMARKS.md
- Create TESTING-STRATEGY.md

**Commit:** `git commit -m "docs: Complete testing + monitoring documentation"`

---

## DAILY CHECKLIST

### Day 1 (Thu Dec 11): Data Loader
- [ ] Create `scripts/test_data_loader.py`
- [ ] Run tests (expect failures)
- [ ] Fix `agents/loaders/data_loader.py`
- [ ] Verify 1M rows < 5s
- [ ] Add ErrorIntelligence to Loader workers
- [ ] Create `scripts/test_error_intelligence_loader.py`
- [ ] All tests pass
- [ ] Commit

### Day 2 (Fri Dec 12): Data Explorer
- [ ] Create `scripts/test_data_explorer.py`
- [ ] Run tests (expect failures)
- [ ] Fix `agents/explorers/data_explorer.py`
- [ ] Verify 1M rows stats < 3s
- [ ] Add ErrorIntelligence to Explorer workers
- [ ] Create `scripts/test_error_intelligence_explorer.py`
- [ ] All tests pass
- [ ] Commit

### Day 3 (Sat Dec 13): Integration
- [ ] Create `scripts/test_full_pipeline.py`
- [ ] Test Load → Explore → Aggregate
- [ ] Fix data flow issues
- [ ] Verify error tracking across pipeline
- [ ] All tests pass
- [ ] Commit

### Day 4 (Sun Dec 14): Anomaly + Visualizer
- [ ] Create `scripts/test_anomaly_detector.py`
- [ ] Create `scripts/test_visualizer.py`
- [ ] Fix both agents
- [ ] Add ErrorIntelligence to both
- [ ] All tests pass
- [ ] Commit

### Day 5 (Mon Dec 15): Predictor + Docs
- [ ] Create `scripts/test_predictor.py`
- [ ] Fix Predictor
- [ ] Add ErrorIntelligence
- [ ] Update documentation
- [ ] All tests pass
- [ ] Final commit

---

## SUCCESS CRITERIA

### Exit Criteria (Must ALL Pass)
- ✅ Data Loader: 1M rows in <5s
- ✅ Data Explorer: Stats on 1M rows in <3s
- ✅ All 8 agents have tests
- ✅ Error Intelligence integrated in all tested agents
- ✅ Full pipeline works end-to-end
- ✅ Health Score > 80 (from ProjectManager)
- ✅ 100+ total tests passing
- ✅ Documentation complete

### Performance Targets (From Hardening Plan)
| Agent | Operation | Target |
|---|---|---|
| Loader | 1M rows | <5s |
| Explorer | 1M rows stats | <3s |
| Anomaly | 1M rows detect | <10s |
| Aggregator | 1M rows groupby | <2s |
| Visualizer | 100K points | <2s |
| Predictor | 100K rows, 100 features | <5s |

---

## WHAT ABOUT HARDENING PLAN?

**Hardening Plan (6-8 weeks) = PHASE 2**

This week is **PHASE 1: Prove agents work**

**Next week:** System improvements (config, error recovery, validation)

**Priority now:** Test what we have. Fix what breaks. Monitor proven code.

---

## COMMANDS TO RUN

### Create Test File
```powershell
# Day 1
code scripts/test_data_loader.py
```

### Run Tests
```powershell
pytest scripts/test_data_loader.py -v
```

### Check Health
```powershell
python scripts/test_project_manager.py
```

### Commit Progress
```powershell
git add .
git commit -m "feat: [describe what you did]"
git push origin main
```

---

## READY TO START?

**First Action:** Create `scripts/test_data_loader.py`

I will provide the test code once you confirm.

Let's prove the Data Loader actually works. 🚀
