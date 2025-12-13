#!/usr/bin/env python3
"""Test runner for Report Generator workers and integration.

Runs comprehensive tests for:
1. Individual workers (TopicAnalyzer, ChartMapper, ChartSelector, etc.)
2. Agent integration
3. Error handling
4. Complete workflows
"""

import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime


class TestRunner:
    """Run tests and collect results."""

    def __init__(self):
        """Initialize test runner."""
        self.test_dir = Path(__file__).parent
        self.results = []
        self.start_time = None
        self.end_time = None

    def run_tests(self, test_file: str, description: str) -> bool:
        """Run a test file and collect results.
        
        Args:
            test_file: Test file name
            description: Test description
        
        Returns:
            True if tests passed, False otherwise
        """
        print(f"\n{'='*80}")
        print(f"Running: {description}")
        print(f"{'='*80}")
        print(f"File: {test_file}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        start = time.time()
        
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(self.test_dir / test_file),
                    "-v",
                    "--tb=short",
                    "--color=yes",
                    "-x"  # Stop on first failure
                ],
                capture_output=False,
                text=True
            )
            
            elapsed = time.time() - start
            passed = result.returncode == 0
            
            self.results.append({
                'file': test_file,
                'description': description,
                'passed': passed,
                'elapsed': elapsed,
                'timestamp': datetime.now().isoformat()
            })
            
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"\n{status} - Elapsed: {elapsed:.2f}s")
            
            return passed
        
        except Exception as e:
            print(f"❌ ERROR: {e}")
            self.results.append({
                'file': test_file,
                'description': description,
                'passed': False,
                'elapsed': time.time() - start,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            return False

    def run_all(self) -> int:
        """Run all test suites.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        self.start_time = time.time()
        
        print("\n" + "="*80)
        print("REPORT GENERATOR TEST SUITE")
        print("="*80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Test suite 1: Worker Unit Tests
        print("\n🧪 TEST SUITE 1: Worker Unit Tests")
        print("-" * 80)
        
        workers_passed = self.run_tests(
            "test_report_generator_workers.py",
            "Individual Worker Tests (5 workers, 45 test cases)"
        )

        # Test suite 2: Integration Tests
        print("\n🧪 TEST SUITE 2: Agent Integration Tests")
        print("-" * 80)
        
        integration_passed = self.run_tests(
            "test_report_generator_integration.py",
            "Report Generator Integration Tests (End-to-End Workflows)"
        )

        self.end_time = time.time()
        
        # Print summary
        self._print_summary(workers_passed, integration_passed)
        
        # Return exit code
        return 0 if (workers_passed and integration_passed) else 1

    def _print_summary(self, workers_passed: bool, integration_passed: bool) -> None:
        """Print test summary.
        
        Args:
            workers_passed: Whether worker tests passed
            integration_passed: Whether integration tests passed
        """
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        total_time = self.end_time - self.start_time
        
        print(f"\nTotal Time: {total_time:.2f}s")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        print("Test Results:")
        for result in self.results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"  {status} - {result['description']}")
            print(f"      Time: {result['elapsed']:.2f}s")
            if 'error' in result:
                print(f"      Error: {result['error']}")
        
        print()
        
        # Overall status
        all_passed = all(r['passed'] for r in self.results)
        
        if all_passed:
            print("🎉 ALL TESTS PASSED! 🎉")
            print()
            print("Status: ✅ READY FOR DEPLOYMENT")
        else:
            failed_count = sum(1 for r in self.results if not r['passed'])
            print(f"❌ {failed_count} test suite(s) failed")
            print()
            print("Status: ⚠️  NEEDS FIXING")
        
        print()
        
        # Detailed breakdown
        print("Breakdown:")
        print(f"  Worker Tests: {'✅ PASSED' if workers_passed else '❌ FAILED'}")
        print(f"  Integration Tests: {'✅ PASSED' if integration_passed else '❌ FAILED'}")
        
        print()
        print("="*80)

    def generate_report(self) -> str:
        """Generate test report.
        
        Returns:
            Report string
        """
        report_lines = [
            "Test Execution Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "Test Results:",
        ]
        
        for result in self.results:
            status = "PASS" if result['passed'] else "FAIL"
            report_lines.append(
                f"  [{status}] {result['description']} ({result['elapsed']:.2f}s)"
            )
        
        all_passed = all(r['passed'] for r in self.results)
        report_lines.append("")
        report_lines.append(
            f"Overall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}"
        )
        
        return "\n".join(report_lines)


def main():
    """Main entry point."""
    runner = TestRunner()
    exit_code = runner.run_all()
    
    # Save report
    report_path = Path(__file__).parent / "report_generator_test_results.txt"
    with open(report_path, "w") as f:
        f.write(runner.generate_report())
    
    print(f"\nReport saved to: {report_path}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
