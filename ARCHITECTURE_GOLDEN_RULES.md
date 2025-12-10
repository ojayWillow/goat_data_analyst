# 🏛️ **ARCHITECTURE GOLDEN RULES**

**Last Updated:** Wednesday, December 10, 2025, 10:19 AM EET  
**Status:** 🔒 **LOCKED - DO NOT DEVIATE**

---

## ⚠️ **CRITICAL PRINCIPLE**

> **"Without structure, we lose functionality. Every new feature must follow the established architecture pattern. No exceptions."**

This document defines the **non-negotiable architectural principles** for the `goat_data_analyst` project. Every pull request, every new method, every worker must align with these rules.

---

## 🏗️ **THE GOLDEN RULE: Agent + Workers Pattern**

### **Every Department Has This Structure:**

```
agents/
├── department_name/
│   ├── department_agent.py         ← Orchestrator (thin, no computation)
│   └── workers/
│       ├── worker_1.py             ← Task A (does the work)
│       ├── worker_2.py             ← Task B (does the work)
│       └── worker_3.py             ← Task C (does the work)
```

### **This Pattern is Exemplified By:**
- ✅ **Aggregator** (already implemented correctly)
- ✅ **Loader** (follows the pattern)
- ✅ **Cleaner** (follows the pattern)
- ⚠️ **Explorer** (being refactored to follow the pattern)

---

## 📋 **RESPONSIBILITIES - CRYSTAL CLEAR**

### **Agent (Department Level)**

**Is Responsible For:**
- ✅ Input validation
- ✅ Flow control/orchestration
- ✅ Delegating to workers
- ✅ Aggregating results
- ✅ Error handling at department level
- ✅ Logging operations

**Is NOT Responsible For:**
- ❌ Computation logic
- ❌ Business logic
- ❌ Statistical calculations
- ❌ Data transformations
- ❌ Direct data processing

### **Worker (Task Level)**

**Is Responsible For:**
- ✅ Specific computation tasks
- ✅ Business logic implementation
- ✅ Error handling for their task
- ✅ Returning structured results
- ✅ Logging their work

**Is NOT Responsible For:**
- ❌ Orchestration
- ❌ Calling other workers
- ❌ Input validation (agent does this)
- ❌ Result aggregation (agent does this)

---

## 📁 **DIRECTORY STRUCTURE RULE**

### **Current Departments (MUST Follow This)**

```
agents/
├── aggregator/
│   ├── aggregator.py
│   └── workers/
│       ├── file_worker.py
│       ├── db_worker.py
│       └── api_worker.py
│
├── loader/
│   ├── loader.py
│   └── workers/
│       ├── data_worker.py
│       └── source_worker.py
│
├── cleaner/
│   ├── cleaner.py
│   └── workers/
│       ├── null_worker.py
│       ├── outlier_worker.py
│       └── type_worker.py
│
├── explorer/
│   ├── explorer.py
│   └── workers/
│       ├── stats_worker.py
│       ├── categorical_worker.py
│       └── multivariate_worker.py
│
├── analyzer/          ← Future
│   ├── analyzer.py
│   └── workers/
│       └── ...
│
├── modeler/           ← Future
│   ├── modeler.py
│   └── workers/
│       └── ...
│
└── reporter/          ← Future
    ├── reporter.py
    └── workers/
        └── ...
```

### **Rule:**
- **Every department gets its own folder** under `agents/`
- **Agent is named** `department_name.py`
- **Workers live in** `workers/` subfolder
- **No exceptions** to this structure

---

## ✅ **CHECKLIST: Before Adding Any New Feature**

Every PR must pass this checklist:

### **If Adding a New Function/Method:**

- [ ] Is this computation logic? → Goes in a **worker**
- [ ] Is this orchestration? → Goes in the **agent**
- [ ] Is the function already in an agent? → **MOVE IT TO A WORKER**
- [ ] Does it follow the department pattern? → **YES** before merge
- [ ] Is the worker in the correct folder? → `agents/department/workers/`
- [ ] Does the agent delegate to it? → **YES**
- [ ] Does the worker return structured results? → **YES**

### **If Modifying an Agent:**

- [ ] Am I adding computation logic? → **NO, that's a worker's job**
- [ ] Am I validating input? → **YES, that's the agent's job**
- [ ] Am I orchestrating workers? → **YES, that's the agent's job**
- [ ] Is my agent thin and focused? → **YES, it should be <200 lines**

### **If Creating a New Department:**

- [ ] Did I create the folder? → `agents/new_department/`
- [ ] Did I create the agent? → `new_department_agent.py`
- [ ] Did I create the workers folder? → `agents/new_department/workers/`
- [ ] Does my agent delegate to workers? → **YES**
- [ ] Does my structure match Aggregator? → **YES**

---

## 🚫 **ANTI-PATTERNS - NEVER DO THIS**

### ❌ **Fat Agent (WRONG)**
```python
# WRONG - Agent doing all the work
class Explorer(Agent):
    def test_normality(self):
        # Computation logic here - WRONG!
        pass
    
    def compute_vif(self):
        # Computation logic here - WRONG!
        pass
```

### ✅ **Thin Agent (CORRECT)**
```python
# CORRECT - Agent orchestrates workers
class Explorer(Agent):
    def __init__(self):
        self.stats_worker = StatsWorker()
    
    def test_normality(self, features):
        return self.stats_worker.test_normality(features)
```

### ❌ **Workers Without Structure (WRONG)**
```python
# WRONG - Functions scattered in agent file
class Explorer(Agent):
    @staticmethod
    def helper_function_1():
        pass
    
    @staticmethod
    def helper_function_2():
        pass
```

### ✅ **Workers in Proper Folder (CORRECT)**
```
agents/explorer/workers/stats_worker.py  ← Each function is a method in a worker class
agents/explorer/workers/categorical_worker.py
agents/explorer/workers/multivariate_worker.py
```

---

## 📊 **ARCHITECTURE DIAGRAM**

```
┌─────────────────────────────────────────────────────┐
│                  PROJECT ROOT                       │
│              (Orchestrator/Launcher)                │
└─────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────┴───────────────┐
        ↓                               ↓
    ┌───────────┐              ┌──────────────┐
    │ AGENT 1   │              │ AGENT 2      │
    │(Loader)   │              │(Cleaner)     │
    │           │              │              │
    │ Workers:  │              │ Workers:     │
    │ ├─ W1     │              │ ├─ W1        │
    │ ├─ W2     │              │ ├─ W2        │
    │ └─ W3     │              │ └─ W3        │
    └───────────┘              └──────────────┘
        ↓                           ↓
    ┌───────────┐              ┌──────────────┐
    │ AGENT 3   │              │ AGENT 4      │
    │(Explorer) │              │(Analyzer)    │
    │           │              │              │
    │ Workers:  │              │ Workers:     │
    │ ├─ W1     │              │ ├─ W1        │
    │ ├─ W2     │              │ ├─ W2        │
    │ └─ W3     │              │ └─ W3        │
    └───────────┘              └──────────────┘
```

---

## 🔍 **WHEN REVIEWING CODE**

Every time you:
- **Open a PR**: Check architecture first
- **Add a feature**: Ask "Is this a worker or agent responsibility?"
- **Read the repo**: Understand the agent/worker pattern
- **Write tests**: Test workers independently, agents as coordinators

### **Questions to Ask:**
1. Is this code in the right place?
2. Is this an agent doing computation? (RED FLAG)
3. Are workers properly separated?
4. Does the agent only orchestrate?
5. Is the structure consistent with other departments?

---

## 📚 **REFERENCE IMPLEMENTATION**

**Look at `agents/aggregator/` to understand the pattern.**

It's the **gold standard** for this project.

```
agents/aggregator/
├── aggregator.py         ← Thin orchestrator
└── workers/
    ├── file_worker.py    ← Handles file operations
    ├── db_worker.py      ← Handles database operations
    └── api_worker.py     ← Handles API operations
```

**Every new department should mirror this structure.**

---

## 🚨 **VIOLATIONS - Immediate Action Required**

If you find:
- ✗ Computation logic in an agent → **MOVE TO WORKER**
- ✗ Worker logic scattered in agent → **CREATE WORKER CLASS**
- ✗ Department without workers folder → **CREATE IT**
- ✗ Agent doing multiple responsibilities → **REFACTOR**
- ✗ Non-standard folder structure → **STANDARDIZE**

**These are not optional. They are mandatory.**

---

## 💾 **VERSION HISTORY**

| Date | Version | Change | Author |
|------|---------|--------|--------|
| Dec 10, 2025 | 1.0 | Initial golden rules established | Project Team |

---

## 🔐 **SIGN-OFF**

**This is a NON-NEGOTIABLE architectural principle.**

Every commit, every PR, every feature must align with these rules.

**Without structure, we lose functionality.**  
**With structure, we build something sustainable.**

---

**Last Reviewed:** Wednesday, December 10, 2025, 10:19 AM EET  
**Status:** 🟢 **ACTIVE - ALL MUST FOLLOW**
