# HARDENING V2 - Complete Plan

## Phase 0: Agent Readiness (Week 1)

### Current State
- ✅ 5 agents tested
- ⚠️ 7 agents untested
- Health: 59/100 (too low)

### Untested Agents (Priority)
1. **aggregator** - 11 workers, 138.8KB
2. **explorer** - 14 workers, 159.0KB
3. **narrative_generator** - 4 workers, 160.3KB
4. **orchestrator** - 5 workers, 115.7KB
5. **recommender** - 6 workers, 87.4KB
6. **reporter** - 6 workers, 85.6KB
7. **visualizer** - 9 workers, 119.6KB

### Week 1 Tests Needed
```python
# For each untested agent:
# tests/test_{agent_name}.py

# 1. Initialize agent
# 2. Test basic execute()
# 3. Test input validation
# 4. Test output format
# 5. Test error handling
```

**Goal:** All 12 agents tested → Health ≥ 70

---

## Phase 1: Pipeline Testing (Week 2)

### Old Pipeline Flow
```
File Input 
  ↓
Data Loader (TESTED ✅)
  ↓
Explorer (UNTESTED ⚠️)
  ↓
Analysis Agents
  ↓
Reports
```

### What We Need to Validate
1. **Data Flow** - Does data pass correctly between agents?
2. **Report Generation** - Does each agent produce valid output?
3. **Error Handling** - What happens when input is invalid?

### Test Steps
```python
# Test pipeline end-to-end
from agents.data_loader import DataLoader
from agents.explorer import Explorer
from agents.orchestrator import Orchestrator

# Step 1: Load file
loader = DataLoader()
data = loader.load('sample.csv')

# Step 2: Explore
explorer = Explorer()
exploration = explorer.execute(data)

# Step 3: Get insights
orchestrator = Orchestrator()
insights = orchestrator.execute(exploration)

# Validate each step produces correct output
assert data is not None
assert exploration is not None
assert insights is not None
```

**Goal:** Full pipeline works → Health ≥ 80

---

## Phase 2: Narrative & Reports (Week 3)

### Current Generators (Untested)
1. **narrative_generator** - Creates story from data
2. **report_generator** - Creates reports

### What We Need
```
Analysis Results
  ↓
Narrative Generator → "Here's what we found..."
  ↓
Report Generator → PDF/JSON output
  ↓
Visualizer → Charts/graphs
```

### Information Flow
**Narrative Generator receives:**
- Data insights
- Patterns detected
- Anomalies found

**Narrative Generator outputs:**
```json
{
  "narrative": "Text summary",
  "key_points": [...],
  "recommendations": [...]
}
```

**Report Generator receives:**
- Narrative
- Raw data
- Analysis results

**Report Generator outputs:**
```json
{
  "report": "Full report",
  "format": "PDF/HTML/JSON",
  "metadata": {...}
}
```

### Testing
```python
from agents.narrative_generator import NarrativeGenerator
from agents.report_generator import ReportGenerator

# Test narrative
ng = NarrativeGenerator()
narrative = ng.execute(analysis_results)
assert narrative['narrative'] is not None
assert len(narrative['key_points']) > 0

# Test report
rg = ReportGenerator()
report = rg.execute(narrative)
assert report['format'] in ['PDF', 'HTML', 'JSON']
```

**Goal:** Reports are clear and accurate → Health ≥ 85

---

## Phase 3: User Experience (Week 4)

### User Journey & Information Architecture

```
STEP 1: FILE SELECTION
  ↓ [USER SEES]
  "Select file(s) to analyze"
  - Upload options: Single file, Multiple files, URL
  - Supported formats: CSV, Excel, JSON, SQL
  - File size limit: 500MB
  
  ↓ [WHAT HAPPENS]
  Data Loader validates file
  Shows: "✅ File valid" or "❌ Error: Invalid format"

STEP 2: ANALYSIS CONFIGURATION
  ↓ [USER SEES]
  "Configure Analysis"
  - Analysis type: Quick / Standard / Deep
  - What each does:
    * Quick: Basic patterns (30s)
    * Standard: Detailed analysis (2m)
    * Deep: Full AI analysis (5m)
  - Expected output preview
  
  ↓ [WHAT HAPPENS]
  Validation engine checks:
  - Data quality
  - Required fields present
  - Shows: "Ready to analyze" or "Missing: X, Y, Z"

STEP 3: RUNNING ANALYSIS
  ↓ [USER SEES]
  Progress bar with status:
  "Step 1/5: Exploring data..."
  "Step 2/5: Detecting patterns..."
  "Step 3/5: Finding anomalies..."
  "Step 4/5: Generating narrative..."
  "Step 5/5: Creating report..."
  
  ↓ [WHAT HAPPENS]
  Each agent runs sequentially
  Shows: Real-time progress + estimated time remaining

STEP 4: RESULTS
  ↓ [USER SEES]
  
  TAB 1: NARRATIVE
  - Clear text summary
  - Key findings highlighted
  - Recommendations listed
  
  TAB 2: DETAILED REPORT
  - Full analysis
  - Charts/visualizations
  - Data tables
  - Export options: PDF, CSV, JSON
  
  TAB 3: QUALITY METRICS
  - Confidence scores
  - Data quality assessment
  - Anomaly confidence
  
  ↓ [WHAT HAPPENS]
  Report generator creates all formats
  Visualizer generates charts
  All data cached for export
```

### Information at Each Step

**Step 1 - File Upload:**
```
✓ File name: data.csv
✓ Rows: 10,000
✓ Columns: 25
✓ Size: 5.2 MB
✓ Status: VALID
→ Ready to configure analysis
```

**Step 2 - Configuration:**
```
Selected: Standard Analysis
Expected output:
- Data exploration report
- Pattern detection
- Anomaly detection
- Narrative summary
Expected time: ~2 minutes
→ Ready to run
```

**Step 3 - Progress:**
```
[████████░░] 80% Complete
Current: Generating narrative...
Completed:
  ✓ Data exploration (0.3s)
  ✓ Pattern detection (12.4s)
  ✓ Anomaly detection (8.7s)
Remaining: ~5 seconds
```

**Step 4 - Results:**
```
NARRATIVE TAB
═══════════════════
Analysis of Q4 Sales Data

Key Findings:
• 15% revenue increase
• 3 anomalies detected
• 87% data quality score

Recommendations:
1. Investigate spike in November
2. Review product C performance
3. Follow up with customer segment B

REPORT TAB
═══════════════════
[Full detailed report with charts]

Export:
📄 Download PDF
📊 Download CSV
📋 Download JSON
```

### Error Messages (Clear Guidance)

When something fails:

```
❌ ERROR: Invalid date format

What went wrong:
  Column "date" contains invalid dates in rows: 15, 42, 87

What to do:
  1. Check your data format (use YYYY-MM-DD)
  2. Fix the invalid rows
  3. Re-upload the file

Or:
  Click "Skip validation" to continue (not recommended)
```

**Goal:** Users never confused, always know what's happening → Ready for production

---

## Implementation Checklist

### Week 1: Agent Readiness
- [ ] Create test files for 7 untested agents
- [ ] Test each agent's execute() method
- [ ] Test input validation
- [ ] Test error handling
- [ ] Run ProjectManager → Health ≥ 70

### Week 2: Pipeline Testing
- [ ] Test end-to-end data flow
- [ ] Validate data passes between agents
- [ ] Test error scenarios
- [ ] Document pipeline behavior
- [ ] Run ProjectManager → Health ≥ 80

### Week 3: Reports & Narratives
- [ ] Test narrative_generator output
- [ ] Test report_generator output
- [ ] Validate report formats (PDF, JSON, etc)
- [ ] Test visualizer charts
- [ ] Document output examples
- [ ] Run ProjectManager → Health ≥ 85

### Week 4: User Experience
- [ ] Design UI flow (file → analysis → results)
- [ ] Create information displays for each step
- [ ] Implement error messaging
- [ ] User testing with sample files
- [ ] Documentation for users
- [ ] Run ProjectManager → Health ≥ 90

---

## Success Metrics

| Metric | Week 1 | Week 2 | Week 3 | Week 4 |
|--------|--------|--------|--------|--------|
| Health Score | 70 | 80 | 85 | 90+ |
| Test Coverage | 50% | 75% | 90% | 95%+ |
| Agents Tested | 7/12 | 12/12 | 12/12 | 12/12 |
| Documentation | Basic | Complete | Complete | Complete |
| User Ready | No | No | No | YES |

---

## Commands to Run

### Weekly Health Check
```bash
python scripts/test_project_manager.py
```

### Baseline (Week 1)
```bash
bash scripts/baseline_metrics.sh
# Captures: Health=59.17, Coverage=41.7%, Arch=100
```

### Track Progress (Week 2-4)
```bash
python -c "
from agents.project_manager import ProjectManager
pm = ProjectManager()
r = pm.execute()
print(f'Health: {r[\"health\"][\"health_score\"]}/100')
print(f'Coverage: {r[\"health\"][\"summary\"][\"test_coverage\"]}%')
"
```

### Production Ready Check (Week 4)
```bash
python -c "
from agents.project_manager import ProjectManager
pm = ProjectManager()
r = pm.execute()
assert r['health']['health_score'] >= 90
assert r['health']['summary']['test_coverage'] >= 95
print('🚀 PRODUCTION READY')
"
```

---

## Summary

**Week 1:** Test agents (59 → 70)  
**Week 2:** Fix pipeline (70 → 80)  
**Week 3:** Build reports (80 → 85)  
**Week 4:** Perfect UX (85 → 90+) → LIVE

Each step has clear information flow for users.
