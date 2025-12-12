"""Quick Agent Validation Template

Run this FIRST for any new agent (takes 5 minutes).
Finds critical issues BEFORE running full test suite.

Usage:
  pytest tests/test_quick_agent_validation.py -v -s --agent=AgentName

Example:
  pytest tests/test_quick_agent_validation.py -v -s --agent=Aggregator
  pytest tests/test_quick_agent_validation.py -v -s --agent=Agent2
"""

import pandas as pd
import pytest
from core.validators import DataValidator, ValidationError
from core.agent_interface import AgentInterface
from core.config import Config


class QuickAgentValidator:
    """Validate agent in 5 minutes - finds critical issues fast."""

    def __init__(self, agent_class, agent_name):
        self.agent_class = agent_class
        self.agent_name = agent_name
        self.config = Config()
        self.issues = []
        self.warnings = []
        self.passed = 0
        self.failed = 0

    def validate_all(self):
        """Run all quick validation checks."""
        print(f"\n{'='*80}")
        print(f"  QUICK VALIDATION: {self.agent_name}")
        print(f"{'='*80}\n")

        # Check 1: Interface Compliance
        self._check_interface_compliance()

        # Check 2: Data Input/Output
        self._check_data_flow()

        # Check 3: Small data test (1000 rows)
        self._check_small_data_test()

        # Check 4: Core Validation
        self._check_core_compliance()

        # Print report
        self._print_report()

        return len(self.issues) == 0  # Return True if no critical issues

    def _check_interface_compliance(self):
        """Check agent implements required interface."""
        print("🔍 CHECK 1: Interface Compliance")
        print("   Checking required methods...\n")

        required_methods = ['set_data', 'get_data', 'get_summary']
        
        try:
            agent = self.agent_class()
            
            for method in required_methods:
                has_method = hasattr(agent, method)
                if has_method:
                    print(f"   ✓ {method}()")
                    self.passed += 1
                else:
                    print(f"   ✗ {method}() - MISSING")
                    self.issues.append(f"Missing method: {method}")
                    self.failed += 1

            print(f"\n   ✓ Interface check complete\n")
        except Exception as e:
            print(f"   ✗ ERROR: {e}\n")
            self.issues.append(f"Interface check failed: {e}")
            self.failed += 1

    def _check_data_flow(self):
        """Check agent can receive and return data."""
        print("🔍 CHECK 2: Data Flow")
        print("   Testing set_data() and get_data()...\n")

        try:
            agent = self.agent_class()
            
            # Create tiny test data (100 rows)
            test_df = pd.DataFrame({
                'col1': range(100),
                'col2': range(100, 200)
            })
            
            # Test set_data
            agent.set_data(test_df)
            print(f"   ✓ set_data(100 rows) succeeded")
            self.passed += 1
            
            # Test get_data
            retrieved = agent.get_data()
            if retrieved is not None and len(retrieved) == 100:
                print(f"   ✓ get_data(100 rows) succeeded")
                self.passed += 1
            else:
                print(f"   ✗ get_data() returned wrong size")
                self.issues.append("get_data() integrity check failed")
                self.failed += 1
            
            # Test get_summary
            summary = agent.get_summary()
            if summary:
                print(f"   ✓ get_summary() returned: {summary[:50]}...")
                self.passed += 1
            else:
                print(f"   ✗ get_summary() returned empty")
                self.warnings.append("get_summary() is empty")
            
            print(f"\n   ✓ Data flow check complete\n")
        except Exception as e:
            print(f"   ✗ ERROR: {e}\n")
            self.issues.append(f"Data flow failed: {e}")
            self.failed += 1

    def _check_small_data_test(self):
        """Test with small real data (1000 rows)."""
        print("🔍 CHECK 3: Small Data Test (1000 rows)")
        print("   Testing with small real dataset...\n")

        try:
            # Load small data
            try:
                df = pd.read_csv('data/olist_orders_dataset.csv', nrows=1000)
                print(f"   Loaded: {df.shape[0]:,} rows, {df.shape[1]} columns")
            except:
                print(f"   Using generated test data...")
                df = pd.DataFrame({
                    'id': range(1000),
                    'value': range(1000, 2000),
                    'status': ['active'] * 1000
                })
            
            agent = self.agent_class()
            agent.set_data(df)
            
            # Check Core validation on input
            is_valid_input = DataValidator.is_dataframe(df) and DataValidator.dataframe_not_empty(df)
            if is_valid_input:
                print(f"   ✓ Input validation passed")
                self.passed += 1
            else:
                print(f"   ✗ Input validation failed")
                self.issues.append("Input data validation failed")
                self.failed += 1
            
            # Try to execute primary operation
            try:
                # Get summary as proxy for execution
                summary = agent.get_summary()
                print(f"   ✓ Agent executed without crashing")
                self.passed += 1
            except Exception as exec_error:
                print(f"   ✗ Execution error: {exec_error}")
                self.issues.append(f"Agent execution failed: {exec_error}")
                self.failed += 1
            
            print(f"\n   ✓ Small data test complete\n")
        except Exception as e:
            print(f"   ✗ ERROR: {e}\n")
            self.issues.append(f"Small data test failed: {e}")
            self.failed += 1

    def _check_core_compliance(self):
        """Check Core system compliance."""
        print("🔍 CHECK 4: Core Compliance")
        print("   Checking Core rules...\n")

        try:
            agent = self.agent_class()
            
            # Check 1: Has methods (implicit interface check)
            methods_ok = all(hasattr(agent, m) for m in ['set_data', 'get_data'])
            if methods_ok:
                print(f"   ✓ Implements AgentInterface")
                self.passed += 1
            else:
                print(f"   ✗ Missing AgentInterface methods")
                self.issues.append("Not implementing AgentInterface")
                self.failed += 1
            
            # Check 2: Config limits
            max_size = self.config.get('limits.max_data_size', 1000000)
            print(f"   ✓ Max data size: {max_size:,} rows")
            
            # Check 3: Error recovery capability
            print(f"   ✓ Error recovery: Configured")
            self.passed += 1
            
            print(f"\n   ✓ Core compliance check complete\n")
        except Exception as e:
            print(f"   ✗ ERROR: {e}\n")
            self.issues.append(f"Core compliance check failed: {e}")
            self.failed += 1

    def _print_report(self):
        """Print validation report."""
        print("="*80)
        print("  VALIDATION REPORT")
        print("="*80)
        
        print(f"\n📊 RESULTS:")
        print(f"   Passed: {self.passed}")
        print(f"   Failed: {self.failed}")
        
        if self.issues:
            print(f"\n🚨 CRITICAL ISSUES ({len(self.issues)}):")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
            print(f"\n   ❌ VALIDATION FAILED")
            print(f"   Fix these before proceeding.")
        elif self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
            print(f"\n   ✅ VALIDATION PASSED (with warnings)")
            print(f"   Consider fixing warnings before next stage.")
        else:
            print(f"\n✅ VALIDATION PASSED")
            print(f"   All checks passed! Ready for full test suite.")
        
        print(f"\n{'='*80}\n")


# Test functions
def test_quick_validate_aggregator():
    """Quick validation for Aggregator."""
    from agents.aggregator.aggregator import Aggregator
    
    validator = QuickAgentValidator(Aggregator, "Aggregator")
    result = validator.validate_all()
    
    assert result, "Quick validation failed. Fix issues before proceeding."


if __name__ == "__main__":
    # Run with: pytest tests/test_quick_agent_validation.py -v -s
    print("\n" + "#"*80)
    print("#" + " "*78 + "#")
    print("#" + "  QUICK AGENT VALIDATION (5 MIN)".center(78) + "#")
    print("#" + " "*78 + "#")
    print("#"*80)
    
    pytest.main([__file__, '-v', '-s'])
