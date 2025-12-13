# Windows PowerShell Commands for Orchestrator Testing

## Navigation & Verification

```powershell
# Navigate to project
cd C:\Projects\GOAT_DATA_ANALYST

# Verify you're in right directory
PWD

# Show file (Windows equivalent of 'head')
Get-Content agents/orchestrator/orchestrator.py -Head 20

# Check file size
Get-ChildItem agents/orchestrator/orchestrator.py

# List orchestrator folder
Get-ChildItem agents/orchestrator/

# Verify git pull worked
git status
git log --oneline -5
```

---

## Python & Testing Setup

```powershell
# Check Python version
python --version

# Check pip
pip --version

# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Verify installations
pytest --version
```

---

## Create Test File

```powershell
# Create test file
New-Item -Path "tests/test_orchestrator_v3.py" -ItemType File

# Copy content from LOCAL_TEST_SETUP_ORCHESTRATOR_V3.md into this file
```

---

## Run Tests

```powershell
# Quick test (5 seconds)
pytest tests/test_orchestrator_v3.py -v --tb=short

# Full test with coverage (10-15 seconds)
pytest tests/test_orchestrator_v3.py `
  --cov=agents.orchestrator.orchestrator `
  --cov-report=html `
  --cov-report=term-missing `
  -v

# Run specific test class
pytest tests/test_orchestrator_v3.py::TestOrchestratorV3Initialization -v

# Run specific test
pytest tests/test_orchestrator_v3.py::TestQualityScore::test_init -v
```

---

## View Coverage Report

```powershell
# Open HTML coverage report in browser
Start-Process htmlcov/index.html

# Or open with specific browser
Start-Process -FilePath "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "htmlcov/index.html"
```

---

## Verify Orchestrator Upgrade

```powershell
# Show first 30 lines
Get-Content agents/orchestrator/orchestrator.py -Head 30

# Search for ErrorIntelligence import (should be present)
Select-String "ErrorIntelligence" agents/orchestrator/orchestrator.py

# Search for QualityScore class (should be present)
Select-String "class QualityScore" agents/orchestrator/orchestrator.py

# Count lines in file
(Get-Content agents/orchestrator/orchestrator.py).Count

# Get file info
Get-ChildItem agents/orchestrator/orchestrator.py | Format-List Name, Length, LastWriteTime
```

---

## Git Commands (Windows)

```powershell
# Pull latest changes
git pull origin main

# Check status
git status

# View last 5 commits
git log --oneline -5

# View changes
git diff agents/orchestrator/orchestrator.py

# Stage all changes
git add .

# Commit
git commit -m "My test message"

# Push
git push origin main
```

---

## Troubleshooting

### Python not found
```powershell
# Check if Python is in PATH
python --version

# If not found, you may need to reinstall Python
# Or add to PATH manually
```

### Module import errors
```powershell
# Make sure PYTHONPATH includes project root
$env:PYTHONPATH = "C:\Projects\GOAT_DATA_ANALYST"

# Then run tests
pytest tests/test_orchestrator_v3.py -v
```

### pytest not found
```powershell
# Install in current Python environment
python -m pip install pytest pytest-cov pytest-mock

# Verify
pytest --version
```

### Permission denied on file operations
```powershell
# Run PowerShell as Administrator
Start-Process powershell -Verb RunAs
```

---

## Quick Command Summary

```powershell
# All-in-one setup and test
cd C:\Projects\GOAT_DATA_ANALYST
git pull origin main
pip install pytest pytest-cov pytest-mock
Get-Content agents/orchestrator/orchestrator.py -Head 30
pytest tests/test_orchestrator_v3.py -v
```

---

## Expected Output

After running tests, you should see:

```
========================= test session starts =========================
platform win32 -- Python 3.9.0, pytest-6.2.4
cachedir: .pytest_cache
rootdir: C:\Projects\GOAT_DATA_ANALYST
collected 25 items

tests/test_orchestrator_v3.py::TestOrchestratorV3Initialization::test_init_success PASSED
tests/test_orchestrator_v3.py::TestQualityScore::test_init PASSED
tests/test_orchestrator_v3.py::TestQualityScore::test_quality_all_successful PASSED
...

========================= 25 passed in 0.45s =========================
```

---

## Notes

- Use backtick (`) for line continuation in PowerShell (instead of backslash)
- Use `Start-Process` to open files instead of `open`
- Use `Get-ChildItem` instead of `ls`
- Use `Get-Content` instead of `cat`
- Use `Select-String` instead of `grep`

---

**Status:** Ready to test on Windows  
**Tested On:** Windows PowerShell 7.x  
**Python:** 3.8+  
**Date:** 2025-12-13
