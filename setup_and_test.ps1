#Requires -Version 5.0

<#
.SYNOPSIS
    DataLoader Test Setup & Execution Script for PowerShell (Windows)
.DESCRIPTION
    Automates environment setup and test execution for DataLoader workers
.PARAMETER Coverage
    Generate coverage report
.PARAMETER Verbose
    Enable verbose test output
.EXAMPLE
    .\setup_and_test.ps1
    .\setup_and_test.ps1 -Coverage
    .\setup_and_test.ps1 -Verbose -Coverage
#>

param(
    [switch]$Coverage,
    [switch]$Verbose
)

# Configure error handling
$ErrorActionPreference = 'Continue'
$WarningPreference = 'SilentlyContinue'

# Colors
$colors = @{
    'Green'  = 'Green'
    'Red'    = 'Red'
    'Yellow' = 'Yellow'
    'Blue'   = 'Cyan'
}

# Functions
function Write-Header {
    param([string]$Message)
    Write-Host "" 
    Write-Host "===============================================================================" -ForegroundColor $colors['Blue']
    Write-Host $Message -ForegroundColor $colors['Blue']
    Write-Host "===============================================================================" -ForegroundColor $colors['Blue']
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-Host "[✓] $Message" -ForegroundColor $colors['Green']
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[✗] $Message" -ForegroundColor $colors['Red']
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "[⚠] $Message" -ForegroundColor $colors['Yellow']
}

function Write-Info {
    param([string]$Message)
    Write-Host "[ℹ] $Message" -ForegroundColor $colors['Blue']
}

function Get-ScriptRoot {
    return Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
}

# Main execution
try {
    $ScriptRoot = Get-ScriptRoot
    $VenvPath = Join-Path $ScriptRoot "venv"
    
    Write-Header "DataLoader Test Setup & Execution (PowerShell)"
    
    # Step 1: Check Python
    Write-Header "Step 1/6: Checking Python Installation"
    
    Write-Info "Checking Python version..."
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Python is not installed or not in PATH"
        Write-Host ""
        Write-Host "Please install Python 3.8+ from https://www.python.org"
        Write-Host "Make sure to check 'Add Python to PATH' during installation"
        Write-Host ""
        exit 1
    }
    
    Write-Success "$pythonVersion found"
    Write-Host ""
    
    # Step 2: Create/Activate Virtual Environment
    Write-Header "Step 2/6: Virtual Environment Setup"
    
    if (-not (Test-Path $VenvPath)) {
        Write-Info "Creating virtual environment at $VenvPath..."
        python -m venv $VenvPath
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Failed to create virtual environment"
            exit 1
        }
        Write-Success "Virtual environment created"
    } else {
        Write-Success "Virtual environment already exists"
    }
    
    Write-Info "Activating virtual environment..."
    $activateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
    & $activateScript
    Write-Success "Virtual environment activated"
    Write-Host ""
    
    # Step 3: Upgrade pip
    Write-Header "Step 3/6: Upgrading Pip"
    
    Write-Info "Upgrading pip, setuptools, and wheel..."
    python -m pip install --upgrade pip setuptools wheel --quiet 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Pip upgraded successfully"
    } else {
        Write-Warning-Custom "Pip upgrade completed with warnings"
    }
    Write-Host ""
    
    # Step 4: Install Dependencies
    Write-Header "Step 4/6: Installing Dependencies"
    
    $requirementsFile = Join-Path $ScriptRoot "requirements.txt"
    if (Test-Path $requirementsFile) {
        Write-Info "Installing requirements from requirements.txt..."
        pip install -q -r $requirementsFile 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Base requirements installed"
        } else {
            Write-Warning-Custom "Some base requirements had issues"
        }
    } else {
        Write-Warning-Custom "requirements.txt not found, skipping base requirements"
    }
    
    Write-Info "Installing test dependencies..."
    pip install -q pytest>=7.0 pytest-cov>=4.0 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Pytest installed"
    } else {
        Write-Error-Custom "Failed to install pytest"
        exit 1
    }
    
    Write-Info "Installing data processing libraries..."
    pip install -q pandas>=1.5 openpyxl>=3.0 pyarrow>=10.0 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Data libraries installed"
    } else {
        Write-Warning-Custom "Some data libraries had issues"
    }
    Write-Host ""
    
    # Step 5: Verify Installation
    Write-Header "Step 5/6: Verifying Installation"
    
    Write-Info "Checking Python..."
    python --version
    Write-Success "Python OK"
    Write-Host ""
    
    Write-Info "Checking pytest..."
    pytest --version
    Write-Success "Pytest OK"
    Write-Host ""
    
    Write-Info "Checking pandas..."
    $pandasCheck = python -c "import pandas; print(f'Pandas {pandas.__version__}')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host $pandasCheck
        Write-Success "Pandas OK"
    } else {
        Write-Warning-Custom "Pandas check had issues"
    }
    Write-Host ""
    
    Write-Info "Checking pytest-cov..."
    $covCheck = python -c "import pytest_cov; print('pytest-cov available')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host $covCheck
        Write-Success "pytest-cov OK"
    } else {
        Write-Warning-Custom "pytest-cov check had issues"
    }
    Write-Host ""
    
    # Step 6: Run Tests
    Write-Header "Step 6/6: Running Tests"
    Write-Host ""
    
    Push-Location $ScriptRoot
    
    $testCmd = "python tests\run_dataloader_tests.py"
    
    if ($Coverage) {
        $testCmd += " -c"
    }
    
    if ($Verbose) {
        $testCmd += " -v"
    }
    
    Write-Info "Executing: $testCmd"
    Write-Host ""
    
    Invoke-Expression $testCmd
    $testResult = $LASTEXITCODE
    
    Pop-Location
    
    # Results
    Write-Host ""
    if ($testResult -eq 0) {
        Write-Header "Test Execution Complete"
        Write-Success "All tests passed!"
        Write-Host ""
        
        if ($Coverage) {
            Write-Info "Coverage report generated in: htmlcov\index.html"
            Write-Host ""
            
            $openBrowser = Read-Host "Open coverage report in browser? (y/n)"
            if ($openBrowser -eq 'y' -or $openBrowser -eq 'Y') {
                $reportPath = Join-Path $ScriptRoot "htmlcov\index.html"
                if (Test-Path $reportPath) {
                    Start-Process $reportPath
                }
            }
        }
        
        Write-Host ""
        Write-Success "Setup and testing completed successfully!"
        Write-Host ""
        Write-Host "To run tests again:"
        Write-Host "  # Activate virtual environment:"
        Write-Host "  .\venv\Scripts\Activate.ps1"
        Write-Host ""
        Write-Host "  # Run tests:"
        Write-Host "  python tests\run_dataloader_tests.py"
        Write-Host ""
        Write-Host "  # With options:"
        Write-Host "  python tests\run_dataloader_tests.py -v  # Verbose"
        Write-Host "  python tests\run_dataloader_tests.py -c  # Coverage"
        Write-Host ""
        
        exit 0
    } else {
        Write-Header "Test Execution Failed"
        Write-Error-Custom "Some tests failed. See output above for details."
        Write-Host ""
        Write-Host "Troubleshooting tips:"
        Write-Host "  - Check Python version: python --version"
        Write-Host "  - Verify dependencies: pip list"
        Write-Host "  - Try fresh install: Remove-Item -Recurse -Force venv"
        Write-Host "                       .\setup_and_test.ps1"
        Write-Host ""
        exit 1
    }
}
catch {
    Write-Error-Custom "An error occurred: $_"
    exit 1
}
