#!/usr/bin/env python
"""Test execution script for DataLoader workers.

Runs all tests with coverage reporting and generates summary.

Usage:
    python run_dataloader_tests.py
    python run_dataloader_tests.py --verbose
    python run_dataloader_tests.py --coverage
"""

import pytest
import sys
from pathlib import Path


def run_tests(verbose=False, coverage=False):
    """Run all DataLoader tests.
    
    Args:
        verbose: Enable verbose output
        coverage: Generate coverage report
        
    Returns:
        Exit code (0 = success)
    """
    test_dir = Path(__file__).parent
    
    # Build pytest arguments
    args = [
        str(test_dir / "test_data_loader_workers_a_plus.py"),
        str(test_dir / "test_data_loader_integration.py"),
        "-v" if verbose else "-q",
        "--tb=short",
    ]
    
    if coverage:
        args.extend([
            "--cov=agents.data_loader.workers",
            "--cov-report=html",
            "--cov-report=term-missing",
        ])
    
    print("\n" + "="*70)
    print("RUNNING DATALOADER WORKER TESTS")
    print("="*70 + "\n")
    
    # Run tests
    exit_code = pytest.main(args)
    
    print("\n" + "="*70)
    if exit_code == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print(f"❌ TESTS FAILED (exit code: {exit_code})")
    print("="*70 + "\n")
    
    return exit_code


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run DataLoader worker tests"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "-c", "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    
    args = parser.parse_args()
    exit_code = run_tests(verbose=args.verbose, coverage=args.coverage)
    sys.exit(exit_code)
