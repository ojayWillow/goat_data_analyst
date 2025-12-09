"""Worker Summary - Clean results from each worker.

Shows ONLY what each worker did and what they found.
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
import pandas as pd

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.explorer import Explorer

def main():
    print("\n" + "="*80)
    print("EXPLORER WORKERS - RESULTS SUMMARY")
    print("="*80)
    
    # Load data
    print("\nLoading FIFA 21 data...")
    df = pd.read_csv("data/fifa21_raw_data.csv", low_memory=False)
    print(f"Loaded: {df.shape[0]} rows x {df.shape[1]} columns\n")
    
    # Initialize explorer
    explorer = Explorer()
    explorer.set_data(df)
    
    # Worker 1: NumericAnalyzer
    print("-" * 80)
    print("WORKER 1: NumericAnalyzer")
    print("-" * 80)
    numeric_result = explorer.numeric_worker.safe_execute(df=df)
    numeric_data = numeric_result.data
    print(f"Status: {'SUCCESS' if numeric_result.success else 'FAILED'}")
    print(f"Quality Score: {numeric_result.quality_score:.3f}")
    print(f"Found: {len(numeric_data.get('numeric_columns', []))} numeric columns")
    print(f"Analyzed: {numeric_data.get('columns_analyzed', 0)} columns")
    if numeric_result.errors:
        print(f"Errors: {len(numeric_result.errors)}")
    if numeric_result.warnings:
        print(f"Warnings: {len(numeric_result.warnings)}")
    print()
    
    # Worker 2: CategoricalAnalyzer
    print("-" * 80)
    print("WORKER 2: CategoricalAnalyzer")
    print("-" * 80)
    cat_result = explorer.categorical_worker.safe_execute(df=df)
    cat_data = cat_result.data
    print(f"Status: {'SUCCESS' if cat_result.success else 'FAILED'}")
    print(f"Quality Score: {cat_result.quality_score:.3f}")
    print(f"Found: {len(cat_data.get('categorical_columns', []))} categorical columns")
    print(f"Analyzed: {cat_data.get('columns_analyzed', 0)} columns")
    if cat_result.errors:
        print(f"Errors: {len(cat_result.errors)}")
    if cat_result.warnings:
        print(f"Warnings: {len(cat_result.warnings)}")
    print()
    
    # Worker 3: CorrelationAnalyzer
    print("-" * 80)
    print("WORKER 3: CorrelationAnalyzer")
    print("-" * 80)
    corr_result = explorer.correlation_worker.safe_execute(df=df)
    corr_data = corr_result.data
    print(f"Status: {'SUCCESS' if corr_result.success else 'FAILED'}")
    print(f"Quality Score: {corr_result.quality_score:.3f}")
    print(f"Found: {corr_data.get('correlation_count', 0)} strong correlations (threshold: {corr_data.get('threshold', 0.7)})")
    if corr_data.get('strong_correlations'):
        print(f"\nTop 5 Correlations:")
        for i, corr in enumerate(corr_data.get('strong_correlations', [])[:5], 1):
            print(f"  {i}. {corr['column_1']} <-> {corr['column_2']}: {corr['correlation']:.3f} ({corr['strength']})")
    if corr_result.errors:
        print(f"Errors: {len(corr_result.errors)}")
    print()
    
    # Worker 4: QualityAssessor
    print("-" * 80)
    print("WORKER 4: QualityAssessor")
    print("-" * 80)
    quality_result = explorer.quality_worker.safe_execute(df=df)
    quality_data = quality_result.data
    print(f"Status: {'SUCCESS' if quality_result.success else 'FAILED'}")
    print(f"Quality Score: {quality_result.quality_score:.3f}")
    print(f"\nData Quality Metrics:")
    print(f"  Overall Quality Score: {quality_data.get('overall_quality_score', 0):.2f}/100")
    print(f"  Quality Rating: {quality_data.get('quality_rating', 'N/A')}")
    print(f"  Total Cells: {quality_data.get('total_cells', 0):,}")
    print(f"  Null Cells: {quality_data.get('null_cells', 0):,} ({quality_data.get('null_percentage', 0):.2f}%)")
    print(f"  Duplicate Rows: {quality_data.get('duplicate_rows', 0):,} ({quality_data.get('duplicate_percentage', 0):.2f}%)")
    print(f"  Complete Rows: {quality_data.get('complete_rows', 0):,}")
    
    if quality_data.get('problematic_columns'):
        print(f"\n  Problematic Columns ({len(quality_data.get('problematic_columns', []))})")
        for col_issue in quality_data.get('problematic_columns', [])[:5]:
            print(f"    - {col_issue['column']}: {col_issue['null_percentage']:.2f}% null")
    
    if quality_result.warnings:
        print(f"\n  Warnings: {len(quality_result.warnings)}")
        for warning in quality_result.warnings:
            print(f"    - {warning}")
    print()
    
    # Overall Summary
    print("="*80)
    print("OVERALL WORKER PERFORMANCE")
    print("="*80)
    print(f"\nAll Workers: {'ALL PASSED' if all([numeric_result.success, cat_result.success, corr_result.success, quality_result.success]) else 'SOME FAILED'}")
    print(f"\nAverage Quality Score: {(numeric_result.quality_score + cat_result.quality_score + corr_result.quality_score + quality_result.quality_score) / 4:.3f}")
    print(f"\nExecution Times:")
    print(f"  NumericAnalyzer: {numeric_result.execution_time_ms}ms")
    print(f"  CategoricalAnalyzer: {cat_result.execution_time_ms}ms")
    print(f"  CorrelationAnalyzer: {corr_result.execution_time_ms}ms")
    print(f"  QualityAssessor: {quality_result.execution_time_ms}ms")
    print(f"  Total: {numeric_result.execution_time_ms + cat_result.execution_time_ms + corr_result.execution_time_ms + quality_result.execution_time_ms}ms")
    
    print("\n" + "="*80)
    print("ALL WORKERS COMPLETED SUCCESSFULLY")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
