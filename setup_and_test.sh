#!/bin/bash

################################################################################
# DataLoader Local Test Setup & Execution Script
# Automates environment setup and test execution
# Usage: bash setup_and_test.sh [--coverage] [--verbose]
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Script variables
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VIRTENV_DIR="$SCRIPT_DIR/venv"
COVERAGE=false
VERBOSE=false

################################################################################
# Functions
################################################################################

print_header() {
    echo -e "${BLUE}=================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=================================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

################################################################################
# Parse Arguments
################################################################################

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: bash setup_and_test.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --coverage    Generate coverage report"
            echo "  --verbose     Verbose test output"
            echo "  --help        Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

################################################################################
# Main Setup
################################################################################

print_header "DataLoader Test Setup & Execution"
echo ""

# Check Python version
print_info "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
print_success "Python $PYTHON_VERSION found"

# Check minimum Python version
MIN_VERSION="3.8"
if [ "$(printf '%s\n' "$MIN_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$MIN_VERSION" ]; then
    print_error "Python $MIN_VERSION or higher required (found $PYTHON_VERSION)"
    exit 1
fi

echo ""

# Step 1: Create/activate virtual environment
print_header "Step 1/5: Virtual Environment"

if [ ! -d "$VIRTENV_DIR" ]; then
    print_info "Creating virtual environment at $VIRTENV_DIR..."
    python3 -m venv "$VIRTENV_DIR"
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

print_info "Activating virtual environment..."
source "$VIRTENV_DIR/bin/activate"
print_success "Virtual environment activated"

echo ""

# Step 2: Upgrade pip
print_header "Step 2/5: Upgrading Pip"
print_info "Upgrading pip, setuptools, and wheel..."
python -m pip install --upgrade pip setuptools wheel > /dev/null 2>&1
print_success "Pip upgraded"

echo ""

# Step 3: Install dependencies
print_header "Step 3/5: Installing Dependencies"

if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    print_info "Installing requirements from requirements.txt..."
    pip install -q -r "$SCRIPT_DIR/requirements.txt"
    print_success "Base requirements installed"
else
    print_warning "requirements.txt not found, skipping"
fi

# Install test dependencies
print_info "Installing test dependencies..."
pip install -q pytest>=7.0 pytest-cov>=4.0
print_success "Pytest installed"

print_info "Installing data processing libraries..."
pip install -q pandas>=1.5 openpyxl>=3.0 pyarrow>=10.0
print_success "Data libraries installed"

echo ""

# Step 4: Verify installation
print_header "Step 4/5: Verifying Installation"

print_info "Checking Python..."
python --version
print_success "Python OK"

print_info "Checking pytest..."
pytest --version
print_success "Pytest OK"

print_info "Checking pandas..."
python -c "import pandas; print(f'Pandas {pandas.__version__}')" 2>/dev/null || print_error "Pandas failed"
print_success "Pandas OK"

print_info "Checking pytest-cov..."
python -c "import pytest_cov; print('pytest-cov available')" 2>/dev/null || print_error "pytest-cov failed"
print_success "pytest-cov OK"

echo ""

# Step 5: Run tests
print_header "Step 5/5: Running Tests"
echo ""

# Change to script directory
cd "$SCRIPT_DIR"

# Build test command
TEST_CMD="python tests/run_dataloader_tests.py"

if [ "$COVERAGE" = true ]; then
    TEST_CMD="$TEST_CMD -c"
fi

if [ "$VERBOSE" = true ]; then
    TEST_CMD="$TEST_CMD -v"
fi

print_info "Executing: $TEST_CMD"
echo ""

# Run tests
if eval "$TEST_CMD"; then
    echo ""
    print_header "Test Execution Complete"
    print_success "All tests passed!"
    echo ""
    print_info "Test output above ^"
    echo ""
    
    if [ "$COVERAGE" = true ]; then
        print_info "Coverage report generated in: htmlcov/index.html"
        echo ""
        if command -v open &> /dev/null; then
            read -p "Open coverage report in browser? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                open htmlcov/index.html
            fi
        fi
    fi
    
    print_success "Setup and testing completed successfully!"
    echo ""
    echo "To run tests again:"
    echo "  source venv/bin/activate  # Activate virtual environment"
    echo "  python tests/run_dataloader_tests.py  # Run tests"
    echo ""
    exit 0
else
    echo ""
    print_header "Test Execution Failed"
    print_error "Some tests failed. See output above for details."
    echo ""
    print_info "Troubleshooting tips:"
    echo "  - Check Python version (3.8+)"
    echo "  - Verify all dependencies installed: pip list"
    echo "  - Check file permissions: ls -la tests/"
    echo "  - Try fresh install: rm -rf venv && bash setup_and_test.sh"
    echo ""
    exit 1
fi
