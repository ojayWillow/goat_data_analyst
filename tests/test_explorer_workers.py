"""Automated test for Explorer agent with worker architecture.

Tests the complete worker-based exploration pipeline.
No manual PowerShell commands needed - just run this script.
"""

import sys
from pathlib import Path
import json
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.explorer import Explorer
from core.logger import get_logger

logger = get_logger(__name__)


def test_explorer_workers():
    """Test Explorer agent with all workers."""
    print("\n" + "="*80)
    print("EXPLORER AGENT WORKER TEST")
    print("="*80)
    
    try:
        # Load FIFA data
        print("\n[1/4] Loading FIFA 21 data...")
        df = pd.read_csv("data/fifa21_raw_data.csv", low_memory=False)
        print(f"✅ Loaded: {df.shape[0]} rows × {df.shape[1]} columns")
        
        # Initialize Explorer
        print("\n[2/4] Initializing Explorer agent with workers...")
        explorer = Explorer()
        explorer.set_data(df)
        print("✅ Explorer ready with 4 workers:")
        print("   - NumericAnalyzer")
        print("   - CategoricalAnalyzer")
        print("   - CorrelationAnalyzer")
        print("   - QualityAssessor")
        
        # Execute workers
        print("\n[3/4] Executing all workers...")
        report = explorer.get_summary_report()
        print("✅ All workers executed successfully")
        
        # Display results
        print("\n[4/4] Displaying Results...")
        print("\n" + "-"*80)
        print("COMPREHENSIVE EXPLORATION REPORT")
        print("-"*80)
        
        # Basic info
        print(f"\nStatus: {report['status']}")
        print(f"Timestamp: {report['timestamp']}")
        print(f"Data Shape: {report['data_shape']['rows']} rows × {report['data_shape']['columns']} columns")
        print(f"\nWorkers Executed: {report['workers_executed']}")
        print(f"Overall Quality Score: {report['overall_quality_score']}")
        
        # Quality validation
        print("\n" + "-"*80)
        print("QUALITY VALIDATION REPORT")
        print("-"*80)
        
        validation = report['quality_validation']
        print(f"\nSuccessful Workers: {validation['successful_workers']}/{validation['total_workers']}")
        print(f"Failed Workers: {validation['failed_workers']}/{validation['total_workers']}")
        
        print("\nWorker Details:")
        for detail in validation['worker_details']:
            status = "✅" if detail['success'] else "❌"
            print(f"  {status} {detail['worker']:25} | Quality: {detail['quality_score']:.3f} | Errors: {detail['error_count']}")
        
        if validation['error_summary']:
            print(f"\nError Summary:")
            for error_type, count in validation['error_summary'].items():
                print(f"  - {error_type}: {count}")
        
        # Worker results
        print("\n" + "-"*80)
        print("DETAILED WORKER RESULTS")
        print("-"*80)
        
        for worker_name, result in report['worker_results'].items():
            print(f"\n{worker_name}:")
            print(f"  Success: {result['success']}")
            print(f"  Quality Score: {result['quality_score']}")
            print(f"  Task Type: {result['task_type']}")
            print(f"  Execution Time: {result['execution_time_ms']}ms")
            
            if result['errors']:
                print(f"  Errors: {len(result['errors'])}")
                for error in result['errors']:
                    print(f"    - [{error['severity']}] {error['message']}")
            
            if result['warnings']:
                print(f"  Warnings: {len(result['warnings'])}")
                for warning in result['warnings']:
                    print(f"    - {warning}")
        
        # Summary
        print("\n" + "-"*80)
        print("ANALYSIS SUMMARY")
        print("-"*80)
        
        summary = report['summary']
        print(f"\nNumeric Columns: {len(summary.get('numeric_columns', []))}")
        if summary.get('numeric_columns'):
            print(f"  Examples: {', '.join(summary['numeric_columns'][:5])}...")
        
        print(f"\nCategorical Columns: {len(summary.get('categorical_columns', []))}")
        if summary.get('categorical_columns'):
            print(f"  Examples: {', '.join(summary['categorical_columns'][:5])}...")
        
        print(f"\nStrongly Correlated Pairs: {len(summary.get('correlations', []))}")
        if summary.get('correlations'):
            print(f"  Top 3:")
            for corr in summary['correlations'][:3]:
                print(f"    - {corr['column_1']} ↔ {corr['column_2']}: {corr['correlation']:.3f}")
        
        print(f"\nData Quality Score: {summary.get('quality_score', 0):.2f}")
        print(f"Quality Rating: {summary.get('quality_rating', 'N/A')}")
        print(f"Null Percentage: {summary.get('null_percentage', 0):.2f}%")
        print(f"Duplicate Percentage: {summary.get('duplicate_percentage', 0):.2f}%")
        
        # Full JSON
        print("\n" + "="*80)
        print("FULL JSON RESPONSE (for debugging)")
        print("="*80)
        print(json.dumps(report, indent=2, default=str))
        
        print("\n" + "="*80)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_explorer_workers()
    sys.exit(0 if success else 1)
