# GOAT Data Analyst 🐐

**The Complete AI-Powered Data Analysis System**

> From raw CSV data to beautiful, intelligently-formatted reports with empathetic narratives and smart visualizations.

**Status:** ✅ PRODUCTION READY | Complete System Built  
**Last Updated:** December 11, 2025  
**Total Code:** 6,800+ lines | **Tests:** 130+ all passing | **Quality:** Production-Grade

---

## 📋 Quick Overview

GOAT Data Analyst transforms raw data into **professional reports** through three stages:

1. **Analysis** (Orchestrator, Week 2) - Run all data analysis agents
2. **Storytelling** (Narrative Generator, Week 3) - Create empathetic narrative
3. **Reporting** (Report Generator, Week 2 – Report Segment) - Format with intelligent charts

---

## 🏗️ Complete Architecture

### End-to-End Flow

```text
CSV Data
    ↓
┌─────────────────────────────────────┐
│ WEEK 2: ORCHESTRATOR (6 Workers)    │
│ ✅ Analysis Coordination             │
│ • Loads and explores data           │
│ • Routes tasks to agents            │
│ • Manages data caching              │
│ • Executes workflows                │
│ Status: 53+ tests passing           │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ WEEK 3: NARRATIVE GENERATOR (4 Workers) │
│ ✅ Story Creation                    │
│ • Extracts key insights              │
│ • Identifies problems                │
│ • Generates recommendations          │
│ • Builds empathetic story            │
│ Status: 24+ tests passing            │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ REPORT GENERATOR (5 Workers)        │
│ ✅ Report Creation                   │
│ • Analyzes narrative topics          │
│ • Maps topics to chart types         │
│ • Selects best visualizations       │
│ • Formats professionally             │
│ • Applies customization              │
│ Status: 35+ tests passing            │
└────────────┬────────────────────────┘
             ↓
    📖 BEAUTIFUL REPORT
    ├── Narrative (empathetic story)
    ├── Charts (intelligently selected)
    ├── Professional formatting
    ├── Multiple export formats
    └── User customization
```

---

## 📊 Code & Test Statistics

| Component                     | Lines  | Workers | Tests | Status |
|-------------------------------|--------|---------|-------|--------|
| Core Systems                  | 800+   | -       | 10+   | ✅     |
| Week 2: Orchestrator          | 1,050+ | 6       | 53+   | ✅     |
| Week 3: Narrative Generator   | 1,200+ | 4       | 24+   | ✅     |
| Report Generator (Week 2 seg) | 2,050+ | 5       | 35+   | ✅     |
| Integration & Misc            | 1,700+ | -       | 10+   | ✅     |
| **TOTAL**                     | **6,800+** | **15** | **130+** | ✅     |

All tests passing; the system is production-grade.

---

## 🔹 Week 2 – Orchestrator

**Purpose:** Coordinate all data analysis agents and prepare inputs for narrative and report generation.

**Key Responsibilities:**
- Manage agent lifecycle and registration
- Load and cache CSV data
- Route tasks to analysis agents
- Execute complex workflows
- Optionally call the Narrative Generator

**Main Pieces:**
- `Orchestrator` (main entry point)
- Workers in `agents/orchestrator/workers/`:
  - `AgentRegistry`
  - `DataManager`
  - `TaskRouter`
  - `WorkflowExecutor`
  - `NarrativeIntegrator`

**Key Methods (Orchestrator):**
```python
orchestrator.register_agent(name, instance)
orchestrator.execute_task(task_type, parameters)
orchestrator.execute_workflow(workflow_tasks)
orchestrator.execute_workflow_with_narrative(tasks)
orchestrator.generate_narrative(results)
orchestrator.get_status()
```

**Location:** `agents/orchestrator/`  
**Tests:** `tests/test_orchestrator_refactored.py`, `tests/test_orchestrator_narrative_integration.py`

---

## 🔹 Week 3 – Narrative Generator

**Purpose:** Transform analysis results into a clear, empathetic story.

**Workers (`agents/narrative_generator/workers/`):**
- `InsightExtractor` – Extract key findings and patterns
- `ProblemIdentifier` – Highlight issues, anomalies, and risks
- `ActionRecommender` – Suggest concrete next steps
- `StoryBuilder` – Turn everything into a cohesive narrative

**Main API (`NarrativeGenerator`):**
```python
narrative_gen.generate_narrative_from_results(orchestrator_results)
narrative_gen.generate_narrative_from_workflow(workflow_results)
narrative_gen.validate_narrative(narrative)
narrative_gen.get_narrative_summary(narrative)
```

**Output Example:**
```json
{
  "full_narrative": "You have 23 anomalies in your data ...",
  "sections": [
    {"title": "Overview", "text": "..."},
    {"title": "Key Problems", "text": "..."},
    {"title": "Recommended Actions", "text": "..."}
  ],
  "confidence": 0.92
}
```

**Location:** `agents/narrative_generator/`  
**Tests:** `tests/test_integration_day5.py` and companions

---

## 🔹 Report Generator (Week 2 – Report Segment)

**Purpose:** Take the narrative + available charts and produce professional reports with intelligent chart selection.

### Workers (`agents/report_generator/workers/`)

1. **`TopicAnalyzer` (≈290 lines)**
   - Parses narrative text
   - Extracts topics with confidence scores
   - Splits narrative into sections
   - Assigns importance levels per section

   **Example Topics:**
   - anomalies, trends, distribution, correlation
   - patterns, comparison, recommendations, risk, performance

2. **`ChartMapper` (≈330 lines)**
   - Defines mapping from topics → chart types
   - Provides primary/secondary chart recommendations per topic
   - Ranks available charts for a given topic

   **Example Mapping:**
   ```text
   anomalies   → scatter_plot (primary), heatmap, box_plot
   trends      → line_chart (primary), area_chart, bar_chart
   correlation → heatmap (primary), scatter_plot, bubble_chart
   ```

3. **`ChartSelector` (≈300 lines)**
   - Given narrative sections + available charts, selects the best charts
   - Avoids redundancy (no duplicate charts across sections)
   - Honors section importance (critical/high/medium/low)
   - Integrates user preferences (include/exclude types, max charts, etc.)

   **Key methods:**
   ```python
   select_charts_for_narrative(sections, available_charts, user_preferences=None)
   select_charts_for_topics(topics, available_charts, max_charts=5)
   get_selection_summary(selected_by_section)
   ```

4. **`ReportFormatter` (≈360 lines)**
   - Formats report as:
     - HTML (responsive, professional CSS)
     - Markdown (clean for sharing/versioning)
     - PDF-ready HTML (for later PDF export)

   **Key methods:**
   ```python
   format_to_html(narrative, selected_charts, title, metadata=None) -> str
   format_to_markdown(narrative, selected_charts, title, metadata=None) -> str
   get_format_options() -> Dict[str, Any]
   ```

5. **`CustomizationEngine` (≈370 lines)**
   - Manages presets and custom user preferences
   - Validates preferences
   - Applies them to chart selections or other lists
   - Estimates impact of preferences

   **Built-in presets:**
   - `minimal` – text-first, almost no charts
   - `essential` – essential charts only
   - `complete` – all relevant charts
   - `visual_heavy` – maximum charts
   - `presentation` – slide-friendly selection

   **Key methods:**
   ```python
   get_customization_options(available_charts=None)
   get_preset(preset_name)
   list_presets()
   validate_preferences(preferences)
   apply_preferences(items, preferences)
   merge_preferences(preset, custom_overrides)
   get_preference_impact(original_count, preferences)
   ```

---

### `ReportGenerator` – Main Coordinator

**File:** `agents/report_generator/report_generator.py`

**Responsibilities:**
- Tie together TopicAnalyzer, ChartMapper, ChartSelector, ReportFormatter, and CustomizationEngine
- Provide a simple high-level API for generating reports

**Core Methods:**

```python
# 1) Analyze narrative only
analyze_narrative(narrative) -> Dict[str, Any]

# 2) Select charts for a narrative
select_charts_for_narrative(
    narrative: str,
    available_charts: List[Dict[str, Any]],
    user_preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, List[Dict[str, Any]]]

# 3) Generate a complete report (HTML/Markdown/PDF-ready)
generate_report(
    narrative: str,
    available_charts: List[Dict[str, Any]],
    title: str = "Data Analysis Report",
    output_format: str = "html",   # 'html' | 'markdown' | 'pdf'
    user_preferences: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]

# 4) Convenience wrappers
generate_html_report(...)
generate_markdown_report(...)

# 5) Customization helpers
get_customization_options(available_charts=None)
get_preset(preset_name)
list_presets()
validate_preferences(preferences)

# 6) Status
get_status() -> Dict[str, Any]
get_detailed_status() -> Dict[str, Any]
```

**Report Output Structure (simplified):**

```json
{
  "status": "success",
  "report_type": "intelligent_analysis",
  "title": "Data Analysis Report",
  "format": "html",
  "generated_at": "2025-12-11T07:05:00Z",
  "narrative": "...",                
  "selected_charts": {                 
    "Executive Summary": [{...}],
    "Findings": [{...}]
  },
  "formatted_content": "<html>...</html>",
  "metadata": {"author": "...", "dataset": "..."},
  "summary": {
    "sections": 3,
    "total_charts": 4,
    "word_count": 950
  }
}
```

**Tests:** `tests/test_report_generator.py` (35+ tests)

---

## 🚀 Quick Start

### Install

```bash
git clone https://github.com/ojayWillow/goat_data_analyst.git
cd goat_data_analyst
pip install -r requirements.txt
```

### End-to-End Example: Data → Narrative → Report

```python
from agents.orchestrator import Orchestrator
from agents.narrative_generator import NarrativeGenerator
from agents.report_generator import ReportGenerator

# 1) Run analysis workflow
orchestrator = Orchestrator()
workflow = [
    {"type": "load_data", "parameters": {"file_path": "data.csv"}},
    {"type": "explore_data", "parameters": {}},
    {"type": "detect_anomalies", "parameters": {}},
]
results = orchestrator.execute_workflow(workflow)

# 2) Generate narrative
narrative_gen = NarrativeGenerator()
narrative_obj = narrative_gen.generate_narrative_from_workflow(results)
narrative_text = narrative_obj["full_narrative"]

# 3) Available charts (coming from your charting layer)
available_charts = [
    {"id": "1", "type": "scatter_plot", "name": "Anomalies"},
    {"id": "2", "type": "line_chart", "name": "Trend Over Time"},
    {"id": "3", "type": "heatmap", "name": "Correlation Matrix"},
]

# 4) Generate HTML report
report_gen = ReportGenerator()
report = report_gen.generate_html_report(
    narrative=narrative_text,
    available_charts=available_charts,
    title="Sales Analysis Q4"
)

html_output = report["formatted_content"]
```

### Generate Markdown Report With Customization

```python
prefs = report_gen.merge_preferences("essential", {"max_charts": 2})

markdown_report = report_gen.generate_markdown_report(
    narrative=narrative_text,
    available_charts=available_charts,
    title="Sales Analysis Q4",
    user_preferences=prefs
)

print(markdown_report["formatted_content"])  # Markdown text
```

---

## 📂 Project Structure

```text
goat_data_analyst/
├── README.md
├── requirements.txt
│
├── core/
│   ├── logger.py
│   ├── structured_logger.py
│   ├── error_recovery.py
│   ├── validators.py
│   └── exceptions.py
│
├── agents/
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   └── workers/
│   │       ├── agent_registry.py
│   │       ├── data_manager.py
│   │       ├── task_router.py
│   │       ├── workflow_executor.py
│   │       └── narrative_integrator.py
│   │
│   ├── narrative_generator/
│   │   ├── __init__.py
│   │   ├── narrative_generator.py
│   │   └── workers/
│   │       ├── insight_extractor.py
│   │       ├── problem_identifier.py
│   │       ├── action_recommender.py
│   │       └── story_builder.py
│   │
│   └── report_generator/
│       ├── __init__.py
│       ├── report_generator.py
│       └── workers/
│           ├── topic_analyzer.py
│           ├── chart_mapper.py
│           ├── chart_selector.py
│           ├── report_formatter.py
│           └── customization_engine.py
│
└── tests/
    ├── test_orchestrator_refactored.py
    ├── test_orchestrator_narrative_integration.py
    ├── test_integration_day5.py
    └── test_report_generator.py
```

---

## 🧪 Testing

Run all tests:

```bash
pytest tests/ -v
```

Run by component:

```bash
pytest tests/test_orchestrator_refactored.py -v
pytest tests/test_orchestrator_narrative_integration.py -v
pytest tests/test_integration_day5.py -v
pytest tests/test_report_generator.py -v
```

All core paths are covered by tests; failures are logged with structured context.

---

## ✅ Quality & Reliability

| Metric          | Value           | Status |
|-----------------|-----------------|--------|
| Type Hints      | 100%            | ✅     |
| Tests           | 130+            | ✅     |
| Workers         | 15              | ✅     |
| Error Handling  | Comprehensive   | ✅     |
| Logging         | Structured      | ✅     |
| Integration     | End-to-end      | ✅     |
| Production Use  | Ready           | ✅     |

---

## 📌 What Changed (Documentation Cleanup)

To simplify documentation, multiple per-day/week markdown files were removed and consolidated here:

Removed (now redundant):
- `COMPLETE_INVENTORY.md`
- `CONSOLIDATION_COMPLETE.md`
- `WEEK3_DAY1_COMPLETE.md`
- `WEEK3_DAY2_COMPLETE.md`
- `WEEK3_DAY3_COMPLETE.md`
- `WEEK3_DAY4_COMPLETE.md`
- `WEEK3_DAY5_COMPLETE.md`
- `REPORT_GENERATOR_COMPLETE.md`
- `REPORTFILE.md` (if present)
- `REFACTORING_WEEK_COMPLETE.md` (if present)

All relevant content from those documents is now summarized and kept **only** in this `README.md`.

---

## 🤝 Contributing

1. Follow the worker-based architecture
2. Add type hints for all public functions
3. Use structured logging for important operations
4. Add tests for every new feature
5. Update this README if you change public behavior

---

## 📄 Meta

**Version:** 2.0 (Complete, consolidated system)  
**Status:** ✅ Production Ready  
**Last Updated:** December 11, 2025  
**Code:** 6,800+ lines  
**Tests:** 130+ all passing

The GOAT Data Analyst – from raw CSV to a beautiful, intelligent, customizable report.
