@echo off
REM DataLoader Local Test Setup & Execution Script (Windows)
REM Automates environment setup and test execution
REM Usage: setup_and_test.bat [--coverage] [--verbose]

setlocal enabledelayedexpansion
setlocal

REM Colors (Windows 10+ only, graceful fallback)
set "RESET=[0m"
set "GREEN=[32m"
set "RED=[31m"
set "YELLOW=[33m"
set "BLUE=[34m"

REM Script variables
set "SCRIPT_DIR=%~dp0"
set "VIRTENV_DIR=%SCRIPT_DIR%venv"
set "COVERAGE=false"
set "VERBOSE=false"

REM Parse arguments
:parse_args
if "%1"=="--coverage" (
    set "COVERAGE=true"
    shift
    goto parse_args
)
if "%1"=="--verbose" (
    set "VERBOSE=true"
    shift
    goto parse_args
)
if "%1"=="--help" (
    echo Usage: setup_and_test.bat [OPTIONS]
    echo.
    echo Options:
    echo   --coverage    Generate coverage report
    echo   --verbose     Verbose test output
    echo   --help        Show this help message
    exit /b 0
)

cls

echo.
echo ===============================================================================
echo DataLoader Test Setup ^& Execution (Windows)
echo ===============================================================================
echo.

REM Check Python version
echo [*] Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8+ from https://www.python.org
    echo Make sure to check 'Add Python to PATH' during installation
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%i"
echo [+] Python %PYTHON_VERSION% found
echo.

REM Step 1: Create/activate virtual environment
echo ===============================================================================
echo Step 1/5: Virtual Environment
echo ===============================================================================
echo.

if not exist "%VIRTENV_DIR%" (
    echo [*] Creating virtual environment...
    python -m venv "%VIRTENV_DIR%"
    if errorlevel 1 (
        echo [!] ERROR: Failed to create virtual environment
        exit /b 1
    )
    echo [+] Virtual environment created
) else (
    echo [+] Virtual environment already exists
)

echo [*] Activating virtual environment...
call "%VIRTENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo [!] ERROR: Failed to activate virtual environment
    exit /b 1
)
echo [+] Virtual environment activated
echo.

REM Step 2: Upgrade pip
echo ===============================================================================
echo Step 2/5: Upgrading Pip
echo ===============================================================================
echo.

echo [*] Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel >nul 2>&1
if errorlevel 1 (
    echo [!] WARNING: Pip upgrade had issues
) else (
    echo [+] Pip upgraded
)
echo.

REM Step 3: Install dependencies
echo ===============================================================================
echo Step 3/5: Installing Dependencies
echo ===============================================================================
echo.

if exist "%SCRIPT_DIR%requirements.txt" (
    echo [*] Installing base requirements...
    pip install -q -r "%SCRIPT_DIR%requirements.txt"
    if errorlevel 1 (
        echo [!] WARNING: Some base requirements failed
    ) else (
        echo [+] Base requirements installed
    )
) else (
    echo [*] requirements.txt not found, skipping base requirements
)

echo [*] Installing test dependencies...
pip install -q pytest>=7.0 pytest-cov>=4.0
if errorlevel 1 (
    echo [!] ERROR: Failed to install pytest
    exit /b 1
)
echo [+] Pytest installed

echo [*] Installing data processing libraries...
pip install -q pandas>=1.5 openpyxl>=3.0 pyarrow>=10.0
if errorlevel 1 (
    echo [!] WARNING: Some data libraries failed
) else (
    echo [+] Data libraries installed
)
echo.

REM Step 4: Verify installation
echo ===============================================================================
echo Step 4/5: Verifying Installation
echo ===============================================================================
echo.

echo [*] Checking Python...
python --version
echo [+] Python OK
echo.

echo [*] Checking pytest...
pytest --version
if errorlevel 1 (
    echo [!] ERROR: Pytest not properly installed
    exit /b 1
)
echo [+] Pytest OK
echo.

echo [*] Checking pandas...
python -c "import pandas; print(f'Pandas {pandas.__version__}')" >nul 2>&1
if errorlevel 1 (
    echo [!] WARNING: Pandas import failed
) else (
    echo [+] Pandas OK
)
echo.

echo [*] Checking pytest-cov...
python -c "import pytest_cov; print('pytest-cov available')" >nul 2>&1
if errorlevel 1 (
    echo [!] WARNING: pytest-cov import failed
) else (
    echo [+] pytest-cov OK
)
echo.

REM Step 5: Run tests
echo ===============================================================================
echo Step 5/5: Running Tests
echo ===============================================================================
echo.

cd /d "%SCRIPT_DIR%"

set "TEST_CMD=python tests\run_dataloader_tests.py"

if "%COVERAGE%"=="true" (
    set "TEST_CMD=!TEST_CMD! -c"
)

if "%VERBOSE%"=="true" (
    set "TEST_CMD=!TEST_CMD! -v"
)

echo [*] Executing: !TEST_CMD!
echo.

!TEST_CMD!

if errorlevel 1 (
    echo.
    echo ===============================================================================
    echo Test Execution Failed
    echo ===============================================================================
    echo.
    echo [!] Some tests failed. See output above for details.
    echo.
    echo Troubleshooting tips:
    echo   - Check Python version (3.8+)
    echo   - Verify all dependencies: pip list
    echo   - Try fresh install: rmdir /s /q venv ^&^& setup_and_test.bat
    echo.
    exit /b 1
) else (
    echo.
    echo ===============================================================================
    echo Test Execution Complete
    echo ===============================================================================
    echo.
    echo [+] All tests passed!
    echo.
    
    if "%COVERAGE%"=="true" (
        echo [*] Coverage report generated in: htmlcov\index.html
        echo.
        set /p "OPEN_BROWSER=Open coverage report in browser? (y/n): "
        if /i "%OPEN_BROWSER%"=="y" (
            start htmlcov\index.html
        )
    )
    
    echo.
    echo [+] Setup and testing completed successfully!
    echo.
    echo To run tests again:
    echo   venv\Scripts\activate.bat  ^REM Activate virtual environment
    echo   python tests\run_dataloader_tests.py  ^REM Run tests
    echo.
    
    endlocal
    exit /b 0
)
