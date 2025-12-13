# 🧪 Report Generator Testing Strategy

**Purpose:** Comprehensive testing of Report Generator workers and agent  
**Date:** December 13, 2025  
**Status:** Ready for Execution  
**Target Coverage:** 90%+

---

## Test Structure

### 1. Worker Unit Tests (`test_report_generator_workers.py`)

Tests for each of the 5 workers in isolation:

#### TopicAnalyzer (8 test cases)
```
✅ test_initialization
✅ test_analyze_narrative_success
✅ test_extract_narrative_sections
✅ test_analyze_narrative_empty
✅ test_get_topic_summary
```
**Coverage:** 100% of public methods  
**Scenarios:** Happy path, edge cases, error handling

#### ChartMapper (6 test cases)
```
✅ test_initialization
✅ test_get_charts_for_topic_valid
✅ test_get_charts_for_topic_invalid
✅ test_get_charts_for_topics
✅ test_rank_charts_for_topic
✅ test_get_topic_info
✅ test_suggest_chart_for_data
```
**Coverage:** 100% of public methods  
**Scenarios:** Valid topics, invalid topics, ranking logic

#### ChartSelector (6 test cases)
```
✅ test_initialization
✅ test_select_charts_for_narrative
✅ test_select_charts_empty_sections
✅ test_select_charts_empty_charts
✅ test_select_charts_with_preferences
✅ test_get_selection_summary
```
**Coverage:** 100% of public methods  
**Scenarios:** Section matching, ranking, duplicate prevention, preferences

#### ReportFormatter (6 test cases)
```
✅ test_initialization
✅ test_format_to_html
✅ test_format_to_markdown
✅ test_format_empty_narrative
✅ test_format_with_metadata
✅ test_get_format_options
```
**Coverage:** 100% of public methods  
**Scenarios:** HTML generation, Markdown generation, styling

#### CustomizationEngine (9 test cases)
```
✅ test_initialization
✅ test_get_customization_options
✅ test_get_preset
✅ test_get_preset_invalid
✅ test_list_presets
✅ test_validate_preferences_valid
✅ test_validate_preferences_invalid
✅ test_apply_preferences
✅ test_merge_preferences
✅ test_get_preference_impact
✅ test_get_recommendation
```
**Coverage:** 100% of public methods  
**Scenarios:** Presets, validation, merging, impact estimation

### 2. Integration Tests (`test_report_generator_integration.py`)

Tests for agent-level functionality and worker coordination:

#### Agent Initialization (1 test class)
```
✅ test_initialization
✅ test_workers_connected
✅ test_chart_mapper_passed_to_selector
```
**Focus:** Proper worker instantiation and connections

#### Narrative Analysis (3 test cases)
```
✅ test_analyze_narrative_success
✅ test_analyze_empty_narrative
```
**Focus:** TopicAnalyzer integration

#### Chart Selection (5 test cases)
```
✅ test_select_charts_success
✅ test_select_charts_empty_narrative
✅ test_select_charts_empty_charts
✅ test_select_charts_with_preferences
```
**Focus:** ChartSelector integration with preferences

#### Report Generation (9 test cases)
```
✅ test_generate_html_report
✅ test_generate_markdown_report
✅ test_generate_report_with_metadata
✅ test_generate_report_with_preferences
✅ test_generate_report_invalid_format
✅ test_generate_report_empty_narrative
✅ test_generate_report_empty_charts
✅ test_report_contains_summary
✅ test_report_is_tracked
```
**Focus:** End-to-end report generation in multiple formats

#### Customization Methods (4 test cases)
```
✅ test_get_customization_options
✅ test_get_preset
✅ test_list_presets
✅ test_validate_preferences
```
**Focus:** CustomizationEngine integration

#### Status Methods (2 test cases)
```
✅ test_get_status
✅ test_get_detailed_status
```
**Focus:** Status reporting

#### Error Recovery (3 test cases)
```
✅ test_handles_missing_narrative
✅ test_handles_invalid_format
✅ test_retry_on_error
```
**Focus:** Error handling and recovery

#### Complete Workflows (3 test cases)
```
✅ test_full_workflow_scenario_1
✅ test_full_workflow_scenario_2
✅ test_workflow_with_all_formats
```
**Focus:** Real-world end-to-end scenarios

---

## Test Execution

### Running Tests

**Run all tests:**
```bash
python tests/run_report_generator_tests.py
```

**Run worker tests only:**
```bash
pytest tests/test_report_generator_workers.py -v
```

**Run integration tests only:**
```bash
pytest tests/test_report_generator_integration.py -v
```

**Run specific test class:**
```bash
pytest tests/test_report_generator_workers.py::TestTopicAnalyzer -v
```

**Run with coverage:**
```bash
pytest tests/test_report_generator_*.py --cov=agents.report_generator --cov-report=html
```

### Test Environment

- Python 3.8+
- pytest
- All core dependencies installed
- No external API calls required (all tests use mocked data)

---

## Test Scenarios

### Scenario 1: Happy Path (Normal Operation)

**What:** Standard report generation with valid inputs

**Test Cases:**
- Analyze clean narrative
- Select appropriate charts
- Generate HTML report
- Generate Markdown report
- Apply preferences

**Expected Results:**
```
✅ All workers execute successfully
✅ Report contains all sections
✅ Charts properly embedded
✅ Formatting correct
✅ No errors or warnings
```

### Scenario 2: Edge Cases

**What:** Boundary conditions and unusual inputs

**Test Cases:**
- Empty narrative
- No available charts
- Invalid preferences
- Very long narrative
- Many charts (50+)
- Special characters in content

**Expected Results:**
```
✅ Graceful error handling
✅ Clear error messages
✅ No crashes
✅ Partial results if possible
```

### Scenario 3: User Preferences

**What:** Customization and filtering

**Test Cases:**
- Apply presets (minimal, essential, complete, etc.)
- Exclude chart types
- Limit chart count
- Prefer specific types
- Merge custom with preset

**Expected Results:**
```
✅ Preferences applied correctly
✅ Charts filtered as specified
✅ Count respected
✅ Types excluded/preferred
```

### Scenario 4: Error Conditions

**What:** Exception handling and recovery

**Test Cases:**
- Invalid format requested
- Missing required data
- Worker failures
- Invalid configuration
- Retry on transient failures

**Expected Results:**
```
✅ Exceptions caught
✅ Errors logged
✅ Graceful degradation
✅ Retry attempts made
```

### Scenario 5: Complete Workflows

**What:** Real-world end-to-end scenarios

**Test Case 1: Executive Summary**
```
Input:
  - Brief narrative (100-200 words)
  - 3-5 key charts
  - Metadata

Expected:
  - Professional HTML report
  - Charts prominently displayed
  - Executive summary format
```

**Test Case 2: Detailed Analysis**
```
Input:
  - Long narrative (1000+ words)
  - 10+ charts
  - User preferences (prefer analytical charts)

Expected:
  - Comprehensive report
  - Charts organized by section
  - Detailed findings
```

**Test Case 3: Multi-Format Output**
```
Input:
  - Same narrative/charts
  - Generate HTML, Markdown, PDF

Expected:
  - All formats generated
  - Content consistent
  - Formatting appropriate to format
```

---

## Test Metrics

### Coverage Targets

```
Target: 90%+ code coverage

Breakdown:
├─ TopicAnalyzer: 100% (all methods tested)
├─ ChartMapper: 100% (all methods tested)
├─ ChartSelector: 100% (all methods tested)
├─ ReportFormatter: 100% (all methods tested)
├─ CustomizationEngine: 100% (all methods tested)
└─ ReportGenerator: 95% (agent-level)
```

### Performance Targets

```
Worker Execution Times:
├─ TopicAnalyzer: < 2 seconds
├─ ChartMapper: < 1 second
├─ ChartSelector: < 2 seconds
├─ ReportFormatter: < 2 seconds
├─ CustomizationEngine: < 1 second
└─ Total Pipeline: < 10 seconds
```

### Quality Metrics

```
✅ 100% Type Hints
✅ 100% Docstrings
✅ Zero Unhandled Exceptions
✅ All Tests Pass
✅ No Memory Leaks
✅ Structured Logging Works
✅ Error Tracking Active
```

---

## Pass/Fail Criteria

### Must Pass
```
✅ All worker unit tests pass
✅ All integration tests pass
✅ No unhandled exceptions
✅ Error handling works
✅ Complete workflows succeed
```

### Should Pass
```
✅ Code coverage >= 90%
✅ Performance within targets
✅ Error messages clear
✅ Logging comprehensive
✅ Preferences work correctly
```

### Nice to Have
```
✅ Code coverage >= 95%
✅ Performance < 50% of targets
✅ Extended error scenarios handled
✅ Performance optimized
```

---

## Test Results Tracking

### Result File
```
tests/report_generator_test_results.txt
```

### Content
```
Test Execution Report
Generated: [timestamp]

Test Results:
  [PASS] Worker Unit Tests (X.XXs)
  [PASS] Integration Tests (X.XXs)
  [PASS] Error Handling (X.XXs)
  [PASS] Complete Workflows (X.XXs)

Overall: ALL TESTS PASSED ✅
```

---

## Test Execution Schedule

### Phase 1: Unit Tests (Worker-Level)
**Time:** 5-10 minutes
**Run:** `pytest tests/test_report_generator_workers.py -v`
**Goal:** Verify each worker works independently

### Phase 2: Integration Tests (Agent-Level)
**Time:** 5-10 minutes
**Run:** `pytest tests/test_report_generator_integration.py -v`
**Goal:** Verify workers integrate correctly

### Phase 3: Full Suite
**Time:** 10-20 minutes
**Run:** `python tests/run_report_generator_tests.py`
**Goal:** Complete verification with reporting

---

## Debugging Tips

### If Tests Fail

1. **Check imports:**
   ```bash
   python -c "from agents.report_generator.workers.topic_analyzer import TopicAnalyzer"
   ```

2. **Check logger configuration:**
   ```bash
   python -c "from core.logger import get_logger; logger = get_logger('test')"
   ```

3. **Check structured logger:**
   ```bash
   python -c "from core.structured_logger import get_structured_logger; logger = get_structured_logger('test')"
   ```

4. **Run single test with verbose output:**
   ```bash
   pytest tests/test_report_generator_workers.py::TestTopicAnalyzer::test_initialization -vv -s
   ```

5. **Check error intelligence:**
   ```bash
   python -c "from agents.error_intelligence.main import ErrorIntelligence; ei = ErrorIntelligence()"
   ```

### Common Issues

**ImportError:** Ensure core modules are in PYTHONPATH
**WorkerError not caught:** Check exception handling in agent
**Logging not showing:** Check logger configuration
**Tests timeout:** Check for infinite loops or blocking calls

---

## Next Steps After Testing

If all tests pass:

1. ✅ Run code quality checks
   ```bash
   pylint agents/report_generator/
   black --check agents/report_generator/
   mypy agents/report_generator/
   ```

2. ✅ Generate coverage report
   ```bash
   pytest --cov=agents.report_generator --cov-report=html
   ```

3. ✅ Create PR with results

4. ✅ Move to deployment phase

---

**Status:** Ready for Testing ✅  
**Test Suite:** Complete with 40+ test cases  
**Expected Duration:** 15-30 minutes  
**Target Coverage:** 90%+
