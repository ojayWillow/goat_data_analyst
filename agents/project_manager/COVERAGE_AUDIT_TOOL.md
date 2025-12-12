# Coverage Audit Tool

A comprehensive audit tool for identifying gaps in **Retry Error Recovery** (`@retry_on_error`) and **Error Intelligence** integration across all agents and workers.

## Overview

The Coverage Audit Tool scans your project and provides:

- ✅ **Retry Error Recovery Audit** - Which agents have `@retry_on_error` decorators
- ✅ **Error Intelligence Audit** - Which agents integrate ErrorIntelligence
- ✅ **Combined Analysis** - Critical gaps (agents missing BOTH)
- ✅ **Remediation Plans** - Actionable steps to close gaps
- ✅ **Export Options** - JSON/text output

## Quick Start

### As a Script

```bash
# Full audit report (text format)
python scripts/coverage_audit.py

# Export to JSON
python scripts/coverage_audit.py --format json --output audit_results.json

# Audit retry coverage only
python scripts/coverage_audit.py --retry-only --verbose

# Audit error intelligence only
python scripts/coverage_audit.py --ei-only --verbose
```

### As a Library

```python
from core.logger import get_logger
from agents.project_manager.workers import CoverageAuditTool, StructureScanner

logger = get_logger("MyCoverageAudit")
scanner = StructureScanner(logger)
structure = scanner.discover_structure()

# Initialize tool
audit_tool = CoverageAuditTool(logger)

# Run combined audit
result = audit_tool.audit_combined(structure)

# Print report
audit_tool.print_audit_report(result)

# Or export to JSON
audit_tool.export_audit_json(result, Path("audit_results.json"))
```

## Audit Methods

### 1. Retry Error Recovery Audit

**Purpose:** Find agents missing `@retry_on_error` decorators

```python
retry_audit = audit_tool.audit_retry_coverage(structure)
```

**Returns:**

```python
{
    "coverage_percentage": 76.92,  # % of agents with @retry_on_error
    "total_agents": 13,
    "covered_agents": 10,
    "uncovered_agents": ["recommender", "report_generator", "aggregator"],
    "agents_detail": {
        "data_loader": {
            "covered": True,
            "percentage": 100.0,
            "main_file_retry_count": 10,
            "main_file_total_methods": 10,
            "workers_retry": {
                "csv_worker": {"retry_count": 3, "total_methods": 3, "percentage": 100.0},
                "json_worker": {"retry_count": 2, "total_methods": 2, "percentage": 100.0}
            }
        },
        "recommender": {
            "covered": False,
            "percentage": 0,
            "main_file_total_methods": 8
        }
    },
    "missing_methods": {
        "recommender": ["get_recommendations", "rank_recommendations", ...],
        "aggregator": ["aggregate_results", "group_by_category", ...]
    },
    "summary": "RETRY ERROR RECOVERY COVERAGE\n...",
    "status": "🟢 Good"  # Based on coverage %
}
```

### 2. Error Intelligence Audit

**Purpose:** Find agents missing ErrorIntelligence integration

```python
ei_audit = audit_tool.audit_error_intelligence_coverage(structure)
```

**Returns:**

```python
{
    "coverage_percentage": 84.62,  # % of agents with ErrorIntelligence
    "total_agents": 13,
    "covered_agents": 11,
    "uncovered_agents": ["recommender", "report_generator"],
    "agents_detail": {
        "data_loader": {
            "covered": True,
            "main_file_has_ei": True,
            "workers_with_ei": ["csv_worker", "json_worker"],
            "workers_without_ei": []
        },
        "recommender": {
            "covered": False,
            "main_file_has_ei": False,
            "workers_without_ei": ["ranker", "filter_worker"]
        }
    },
    "missing_integrations": {
        "recommender": ["ranker", "filter_worker"],
        "report_generator": ["formatter", "validator"]
    },
    "summary": "ERROR INTELLIGENCE COVERAGE\n...",
    "status": "🟡 Good"
}
```

### 3. Combined Audit

**Purpose:** Identify critical gaps (agents missing BOTH)

```python
result = audit_tool.audit_combined(structure)
audit_tool.print_audit_report(result)
```

**Output:**

```
======================================================================
COVERAGE AUDIT REPORT
======================================================================

RETRY ERROR RECOVERY COVERAGE
─────────────────────────────────────────────────────
Coverage: 76.92% (10/13 agents)
Status: 🟢 Good

Covered Agents: 10
Uncovered Agents: 3

Uncovered List:
  • recommender
  • report_generator
  • aggregator

ERROR INTELLIGENCE COVERAGE
─────────────────────────────────────────────────────
Coverage: 84.62% (11/13 agents)
Status: 🟡 Good

Covered Agents: 11
Uncovered Agents: 2

Uncovered List:
  • recommender
  • report_generator

Missing Worker Integrations:
  recommender:
    • ranker
    • filter_worker
  report_generator:
    • formatter
    • validator

COMBINED COVERAGE SCORE: 80.77%

🔴 CRITICAL GAPS (Missing BOTH Retry & EI):
   • recommender

======================================================================
REMEDIATION PLAN
======================================================================

🔴 PHASE 1: Critical (Both Missing)
────────────────────────────────────
  recommender:
    1. Add @retry_on_error to public methods
    2. Integrate ErrorIntelligence
    3. Test both integrations

🟡 PHASE 2: Retry Only (Missing)
────────────────────────────────────
  report_generator: Add @retry_on_error decorator
  aggregator: Add @retry_on_error decorator

🟡 PHASE 3: Error Intelligence Only (Missing)
────────────────────────────────────
  report_generator: Integrate ErrorIntelligence

======================================================================
```

## Understanding Coverage Status

Coverage is categorized by percentage:

| Percentage | Status | Meaning |
|------------|--------|----------|
| 90-100% | 🟢 Excellent | Almost all agents covered |
| 75-89% | 🟢 Good | Most agents covered |
| 50-74% | 🟡 Fair | More than half covered |
| 25-49% | 🟡 Poor | Less than half covered |
| 0-24% | 🔴 Critical | Very few agents covered |

## Command Line Options

```bash
usage: coverage_audit.py [-h] [--format {text,json}] [--retry-only] [--ei-only]
                          [--output OUTPUT] [--verbose]

optional arguments:
  -h, --help            show this help message and exit
  --format {text,json}  Output format (default: text)
  --retry-only          Only audit retry error recovery coverage
  --ei-only             Only audit error intelligence coverage
  --output OUTPUT       Output file path (for JSON format)
  --verbose             Show detailed method-level information
```

### Examples

**Full audit with verbose details:**
```bash
python scripts/coverage_audit.py --verbose
```

**Only retry coverage, save to JSON:**
```bash
python scripts/coverage_audit.py --retry-only --format json --output retry_audit.json
```

**Only error intelligence, with details:**
```bash
python scripts/coverage_audit.py --ei-only --verbose
```

## Integration with Project Manager

The CoverageAuditTool integrates seamlessly with the Project Manager agent:

```python
from agents.project_manager import ProjectManager
from agents.project_manager.workers import CoverageAuditTool

# In ProjectManager's execute method
audit_tool = CoverageAuditTool(self.logger)
retry_audit = audit_tool.audit_retry_coverage(self.structure)
ei_audit = audit_tool.audit_error_intelligence_coverage(self.structure)

# Use results in health reporting
self.retry_error_recovery = retry_audit
self.error_intelligence = ei_audit
```

## Understanding Results

### Retry Error Recovery

**What it checks:** Does the agent have `@retry_on_error` decorators on public methods?

**Why it matters:** Error recovery ensures resilience against transient failures

**Example coverage detail:**
```python
"data_loader": {
    "covered": True,
    "percentage": 100.0,
    "main_file_retry_count": 10,  # Methods with @retry
    "main_file_total_methods": 10,  # Total public methods
    "workers_retry": {
        "csv_worker": {"retry_count": 3, "total_methods": 3, "percentage": 100.0}
    }
}
```

### Error Intelligence

**What it checks:** Does the agent use ErrorIntelligence for monitoring?

**Why it matters:** Error tracking enables learning and pattern detection

**Example coverage detail:**
```python
"data_loader": {
    "covered": True,
    "main_file_has_ei": True,
    "workers_with_ei": ["csv_worker", "json_worker"],  # Workers with EI
    "workers_without_ei": []  # Workers needing EI
}
```

## JSON Export Format

When exporting to JSON, the output includes:

```json
{
  "retry_audit": {
    "coverage_percentage": 76.92,
    "total_agents": 13,
    "covered_agents": 10,
    "uncovered_agents": [...],
    "agents_detail": {...}
  },
  "ei_audit": {
    "coverage_percentage": 84.62,
    "total_agents": 13,
    "covered_agents": 11,
    "uncovered_agents": [...],
    "agents_detail": {...}
  },
  "combined_coverage": 80.77,
  "critical_gaps": ["recommender"]
}
```

## Remediation Workflow

The tool suggests a 3-phase remediation plan:

### Phase 1: Critical Gaps
Agents missing **BOTH** retry and error intelligence.
- Highest priority
- Affects system resilience and monitoring
- Typically 1-3 agents

### Phase 2: Retry Only
Agents missing only `@retry_on_error`.
- Medium priority
- Affects resilience
- Typically 1-3 agents

### Phase 3: Error Intelligence Only
Agents missing only ErrorIntelligence.
- Medium priority
- Affects monitoring
- Typically 1-3 agents

## Usage Scenarios

### Scenario 1: Before Release

```bash
# Ensure all agents have minimum coverage
python scripts/coverage_audit.py --verbose

# Export results
python scripts/coverage_audit.py --format json --output pre_release_audit.json
```

### Scenario 2: After Adding New Agent

```bash
# Check if new agent meets requirements
python scripts/coverage_audit.py --retry-only --verbose
python scripts/coverage_audit.py --ei-only --verbose
```

### Scenario 3: Continuous Monitoring

Integrate into CI/CD:

```bash
# In your CI pipeline
python scripts/coverage_audit.py --format json --output audit_results.json

# Check coverage is >= 80%
if (audit_results['combined_coverage'] < 80.0); then
  echo "Coverage below 80%"
  exit 1
fi
```

## Limitations

- Only checks for decorator presence, not decorator configuration
- Only checks for ErrorIntelligence class usage, not full integration quality
- Worker detection based on directory structure (must be in `agents/agent_name/workers/`)
- Requires agents to follow naming conventions

## Future Enhancements

- ✨ Deep decorator analysis (check retry configuration)
- ✨ Error Intelligence usage depth analysis
- ✨ Test coverage correlation
- ✨ Performance metrics per agent
- ✨ Historical tracking (audit over time)
- ✨ HTML report generation

## See Also

- [Project Manager Documentation](README.md)
- [Error Intelligence Guide](../ERROR-INTELLIGENCE-GUIDE.md)
- [Retry Error Recovery Decorator](../../core/error_recovery.py)
