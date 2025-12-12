"""Test runner for Predictor Agent comprehensive test suite.

Usage:
    python tests/run_predictor_tests.py              # Run all tests
    python tests/run_predictor_tests.py --unit       # Unit tests only
    python tests/run_predictor_tests.py --integration # Integration only
    python tests/run_predictor_tests.py --verbose    # Verbose output
    python tests/run_predictor_tests.py --coverage   # With coverage report
"""

import subprocess
import sys
import argparse
from pathlib import Path


class PredictorTestRunner:
    """Runner for predictor tests."""
    
    def __init__(self):
        self.tests_dir = Path(__file__).parent
        self.repo_root = self.tests_dir.parent
    
    def run_all_tests(self, verbose=False, coverage=False):
        """Run all predictor tests.
        
        Args:
            verbose: Verbose output
            coverage: Generate coverage report
        """
        cmd = [
            'pytest',
            str(self.tests_dir),
            '-k', 'predictor',
            '-v' if verbose else '-q',
        ]
        
        if coverage:
            cmd.extend([
                '--cov=agents/predictor',
                '--cov-report=html',
                '--cov-report=term-missing'
            ])
        
        print(f"\n{'='*70}")
        print("PREDICTOR AGENT COMPREHENSIVE TEST SUITE")
        print(f"{'='*70}\n")
        
        return subprocess.run(cmd, cwd=self.repo_root)
    
    def run_unit_tests(self, verbose=False):
        """Run unit tests only.
        
        Args:
            verbose: Verbose output
        """
        cmd = [
            'pytest',
            str(self.tests_dir),
            '-k', 'unit and predictor',
            '-v' if verbose else '-q',
            '-m', 'unit',
        ]
        
        print(f"\n{'='*70}")
        print("PREDICTOR AGENT - UNIT TESTS ONLY")
        print(f"{'='*70}\n")
        
        return subprocess.run(cmd, cwd=self.repo_root)
    
    def run_integration_tests(self, verbose=False):
        """Run integration tests only.
        
        Args:
            verbose: Verbose output
        """
        cmd = [
            'pytest',
            str(self.tests_dir),
            '-k', 'integration and predictor',
            '-v' if verbose else '-q',
            '-m', 'integration',
        ]
        
        print(f"\n{'='*70}")
        print("PREDICTOR AGENT - INTEGRATION TESTS ONLY")
        print(f"{'='*70}\n")
        
        return subprocess.run(cmd, cwd=self.repo_root)
    
    def run_worker_tests(self, worker_name=None, verbose=False):
        """Run tests for specific worker.
        
        Args:
            worker_name: Worker to test (linear, tree, timeseries, validator)
            verbose: Verbose output
        """
        worker_map = {
            'linear': 'LinearRegression',
            'tree': 'DecisionTree',
            'timeseries': 'TimeSeries',
            'validator': 'Validator',
        }
        
        if worker_name not in worker_map:
            print(f"Unknown worker: {worker_name}")
            print(f"Valid workers: {', '.join(worker_map.keys())}")
            return subprocess.CompletedProcess(cmd=[], returncode=1)
        
        cmd = [
            'pytest',
            str(self.tests_dir / 'test_predictor_workers_unit.py'),
            '-k', f'Test{worker_map[worker_name]}',
            '-v' if verbose else '-q',
        ]
        
        print(f"\n{'='*70}")
        print(f"PREDICTOR - {worker_map[worker_name].upper()} WORKER TESTS")
        print(f"{'='*70}\n")
        
        return subprocess.run(cmd, cwd=self.repo_root)
    
    def generate_report(self):
        """Generate comprehensive test report."""
        cmd = [
            'pytest',
            str(self.tests_dir),
            '-k', 'predictor',
            '--tb=short',
            '--junit-xml=test-report.xml',
            '-v',
        ]
        
        print(f"\n{'='*70}")
        print("GENERATING COMPREHENSIVE TEST REPORT")
        print(f"{'='*70}\n")
        
        result = subprocess.run(cmd, cwd=self.repo_root)
        
        if result.returncode == 0:
            print(f"\n{'='*70}")
            print("✓ Test report generated: test-report.xml")
            print(f"{'='*70}\n")
        
        return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run Predictor Agent comprehensive tests',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python tests/run_predictor_tests.py
  
  # Run unit tests only
  python tests/run_predictor_tests.py --unit
  
  # Run integration tests only
  python tests/run_predictor_tests.py --integration
  
  # Run specific worker tests
  python tests/run_predictor_tests.py --worker linear
  python tests/run_predictor_tests.py --worker tree
  python tests/run_predictor_tests.py --worker timeseries
  python tests/run_predictor_tests.py --worker validator
  
  # Run with coverage
  python tests/run_predictor_tests.py --coverage
  
  # Verbose output
  python tests/run_predictor_tests.py -v
        """
    )
    
    parser.add_argument(
        '--unit',
        action='store_true',
        help='Run unit tests only'
    )
    parser.add_argument(
        '--integration',
        action='store_true',
        help='Run integration tests only'
    )
    parser.add_argument(
        '--worker',
        type=str,
        help='Run tests for specific worker (linear, tree, timeseries, validator)'
    )
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Generate coverage report'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate comprehensive test report (XML)'
    )
    
    args = parser.parse_args()
    
    runner = PredictorTestRunner()
    
    if args.report:
        result = runner.generate_report()
    elif args.worker:
        result = runner.run_worker_tests(args.worker, verbose=args.verbose)
    elif args.integration:
        result = runner.run_integration_tests(verbose=args.verbose)
    elif args.unit:
        result = runner.run_unit_tests(verbose=args.verbose)
    else:
        result = runner.run_all_tests(
            verbose=args.verbose,
            coverage=args.coverage
        )
    
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
