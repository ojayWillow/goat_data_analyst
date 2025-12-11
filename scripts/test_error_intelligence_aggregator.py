"""Test Aggregator Workers - Tests all 10 aggregator workers with proper success/error tracking."""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.aggregator.workers.statistics import StatisticsWorker
from agents.aggregator.workers.crosstab import CrossTabWorker
from agents.aggregator.workers.groupby import GroupByWorker
from agents.aggregator.workers.pivot import PivotWorker
from agents.aggregator.workers.rolling import RollingWorker
from agents.aggregator.workers.rolling_aggregation import RollingAggregation
from agents.aggregator.workers.value_count import ValueCountWorker
from agents.aggregator.workers.exponential_weighted import ExponentialWeighted
from agents.aggregator.workers.lag_lead_function import LagLeadFunction
from agents.aggregator.workers.window_function import WindowFunction
from agents.error_intelligence.main import ErrorIntelligence


def create_sample_data():
    """Create sample DataFrame for testing."""
    np.random.seed(42)
    data = {
        'category': np.random.choice(['A', 'B', 'C'], 100),
        'subcategory': np.random.choice(['X', 'Y', 'Z'], 100),
        'value': np.random.randint(1, 100, 100),
        'amount': np.random.uniform(10, 1000, 100),
        'date': [datetime.now() - timedelta(days=i) for i in range(100)],
    }
    return pd.DataFrame(data)


def test_statistics_worker():
    """Test StatisticsWorker - Calculate summary statistics."""
    print("\n=== Test 1: StatisticsWorker ===")
    worker = StatisticsWorker()
    df = create_sample_data()
    
    result = worker.execute(df=df, group_column='category')
    
    assert result.success == True
    assert 'statistics' in result.data
    assert len(result.data['statistics']) > 0
    
    print(f"✓ StatisticsWorker executed successfully")
    print(f"  - Groups: {result.data['groups']}")
    print(f"  - Numeric columns: {result.data['numeric_columns_count']}")
    print(f"  - Quality score: {result.quality_score}")
    assert True


def test_crosstab_worker():
    """Test CrossTabWorker - Create cross-tabulations."""
    print("\n=== Test 2: CrossTabWorker ===")
    worker = CrossTabWorker()
    df = create_sample_data()
    
    result = worker.execute(df=df, rows='category', columns='subcategory')
    
    assert result.success == True
    assert 'crosstab_data' in result.data
    assert result.data['rows'] > 0
    
    print(f"✓ CrossTabWorker executed successfully")
    print(f"  - Shape: {result.data['rows']} x {result.data['columns']}")
    print(f"  - Quality score: {result.quality_score}")
    assert True


def test_groupby_worker():
    """Test GroupByWorker - Perform groupby aggregation."""
    print("\n=== Test 3: GroupByWorker ===")
    worker = GroupByWorker()
    df = create_sample_data()
    
    result = worker.execute(df=df, group_cols=['category'], agg_specs={'value': 'mean'})
    
    assert result.success == True
    assert 'grouped_data' in result.data
    assert result.data['groups_count'] > 0
    
    print(f"✓ GroupByWorker executed successfully")
    print(f"  - Groups: {result.data['groups_count']}")
    print(f"  - Quality score: {result.quality_score}")
    assert True


def test_pivot_worker():
    """Test PivotWorker - Create pivot tables."""
    print("\n=== Test 4: PivotWorker ===")
    worker = PivotWorker()
    df = create_sample_data()
    
    result = worker.execute(
        df=df,
        index='category',
        columns='subcategory',
        values='value',
        aggfunc='sum'
    )
    
    assert result.success == True
    assert 'pivot_data' in result.data
    assert result.data['rows'] > 0
    
    print(f"✓ PivotWorker executed successfully")
    print(f"  - Shape: {result.data['rows']} x {result.data['columns']}")
    print(f"  - Quality score: {result.quality_score}")
    assert True


def test_rolling_worker():
    """Test RollingWorker - Perform rolling aggregation."""
    print("\n=== Test 5: RollingWorker ===")
    worker = RollingWorker()
    df = create_sample_data()
    
    result = worker.execute(df=df, column='value', window=5, aggfunc='mean')
    
    assert result.success == True
    assert 'rolling_data' in result.data
    assert result.data['window'] == 5
    
    print(f"✓ RollingWorker executed successfully")
    print(f"  - Window size: {result.data['window']}")
    print(f"  - Non-null values: {result.data['non_null_values']}")
    print(f"  - Quality score: {result.quality_score}")
    assert True


def test_rolling_aggregation_worker():
    """Test RollingAggregation - Multi-column rolling aggregations."""
    print("\n=== Test 6: RollingAggregation ===")
    worker = RollingAggregation()
    df = create_sample_data()
    
    result = worker.execute(
        df=df,
        window_size=5,
        columns=['value', 'amount'],
        agg_dict={'value': ['mean', 'sum'], 'amount': ['mean']}
    )
    
    assert result.success == True
    assert 'window_size' in result.data
    assert result.data['window_size'] == 5
    
    print(f"✓ RollingAggregation executed successfully")
    print(f"  - Columns aggregated: {len(result.data['columns_aggregated'])}")
    print(f"  - Rows processed: {result.data['rows_processed']}")
    assert True


def test_value_count_worker():
    """Test ValueCountWorker - Count unique values."""
    print("\n=== Test 7: ValueCountWorker ===")
    worker = ValueCountWorker()
    df = create_sample_data()
    
    result = worker.execute(df=df, column='category', top_n=10)
    
    assert result.success == True
    assert 'value_counts' in result.data
    assert len(result.data['value_counts']) > 0
    
    print(f"✓ ValueCountWorker executed successfully")
    print(f"  - Unique values: {result.data['total_unique']}")
    print(f"  - Results shown: {result.data['results_returned']}")
    print(f"  - Quality score: {result.quality_score}")
    assert True


def test_exponential_weighted_worker():
    """Test ExponentialWeighted - Exponential weighted moving average."""
    print("\n=== Test 8: ExponentialWeighted ===")
    worker = ExponentialWeighted()
    df = create_sample_data()
    
    result = worker.execute(df=df, span=10, adjust=True)
    
    assert result.success == True
    assert 'method' in result.data
    assert result.data['span'] == 10
    
    print(f"✓ ExponentialWeighted executed successfully")
    print(f"  - Method: {result.data['method']}")
    print(f"  - Columns processed: {len(result.data['columns_processed'])}")
    assert True


def test_lag_lead_function_worker():
    """Test LagLeadFunction - Lag and lead operations."""
    print("\n=== Test 9: LagLeadFunction ===")
    worker = LagLeadFunction()
    df = create_sample_data()
    
    result = worker.execute(df=df, lag_periods=2, lead_periods=1)
    
    assert result.success == True
    assert 'lag_periods' in result.data
    assert result.data['lag_periods'] == 2
    
    print(f"✓ LagLeadFunction executed successfully")
    print(f"  - Lag periods: {result.data['lag_periods']}")
    print(f"  - Lead periods: {result.data['lead_periods']}")
    print(f"  - Rows processed: {result.data['rows_processed']}")
    assert True


def test_window_function_worker():
    """Test WindowFunction - Rolling window operations."""
    print("\n=== Test 10: WindowFunction ===")
    worker = WindowFunction()
    df = create_sample_data()
    
    result = worker.execute(
        df=df,
        window_size=3,
        operations=['mean', 'sum', 'std']
    )
    
    assert result.success == True
    assert 'window_size' in result.data
    assert result.data['window_size'] == 3
    
    print(f"✓ WindowFunction executed successfully")
    print(f"  - Window size: {result.data['window_size']}")
    print(f"  - Operations applied: {len(result.data['operations_applied'])}")
    assert True


def test_error_tracking_aggregator():
    """Test that aggregator workers properly track errors."""
    print("\n=== Test 11: Error tracking in aggregator ===")
    ei = ErrorIntelligence()
    ei.error_tracker.clear()
    
    worker = StatisticsWorker()
    
    # This should succeed and track success
    df = create_sample_data()
    result = worker.execute(df=df, group_column='category')
    
    patterns = ei.error_tracker.get_patterns()
    assert patterns["aggregator"]["successes"] > 0
    
    print(f"✓ Error tracking working in aggregator")
    print(f"  - Successes tracked: {patterns['aggregator']['successes']}")
    assert True


def test_aggregator_with_empty_data():
    """Test aggregator workers with edge case: empty DataFrame."""
    print("\n=== Test 12: Edge case - empty DataFrame ===")
    worker = StatisticsWorker()
    df_empty = pd.DataFrame()
    
    result = worker.execute(df=df_empty, group_column='category')
    
    assert result.success == False
    assert len(result.errors) > 0
    
    print(f"✓ Empty DataFrame handled correctly")
    print(f"  - Success: {result.success}")
    print(f"  - Errors: {len(result.errors)}")
    assert True


def test_aggregator_with_missing_column():
    """Test aggregator workers with edge case: missing column."""
    print("\n=== Test 13: Edge case - missing column ===")
    worker = StatisticsWorker()
    df = create_sample_data()
    
    result = worker.execute(df=df, group_column='nonexistent_column')
    
    assert result.success == False
    assert len(result.errors) > 0
    
    print(f"✓ Missing column handled correctly")
    print(f"  - Success: {result.success}")
    print(f"  - Errors: {len(result.errors)}")
    assert True


if __name__ == "__main__":
    print("\n" + "="*70)
    print("AGGREGATOR WORKERS TEST SUITE")
    print("="*70)
    
    try:
        test_statistics_worker()
        test_crosstab_worker()
        test_groupby_worker()
        test_pivot_worker()
        test_rolling_worker()
        test_rolling_aggregation_worker()
        test_value_count_worker()
        test_exponential_weighted_worker()
        test_lag_lead_function_worker()
        test_window_function_worker()
        test_error_tracking_aggregator()
        test_aggregator_with_empty_data()
        test_aggregator_with_missing_column()
        
        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED (13/13)")
        print("="*70 + "\n")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
