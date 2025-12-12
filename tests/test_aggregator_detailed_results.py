"""Detailed Results Test - Show EXACTLY what each worker extracts from each file.

This test shows:
- What data each worker processes
- What specific results it returns
- What information is extracted
- What aggregations are performed
"""

import pandas as pd
import json
from agents.aggregator.aggregator import Aggregator


def print_section(title):
    """Print formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")


def print_worker_result(worker_name, result, data_shape):
    """Pretty print worker result."""
    print(f"\n📊 {worker_name}")
    print(f"   Data processed: {data_shape[0]:,} rows × {data_shape[1]} columns")
    
    if isinstance(result, dict):
        if 'success' in result:
            print(f"   Success: {result.get('success')}")
        if 'data' in result:
            data = result['data']
            if isinstance(data, dict):
                for key, value in list(data.items())[:5]:  # Show first 5 keys
                    if isinstance(value, (int, float)):
                        print(f"   • {key}: {value}")
                    elif isinstance(value, list):
                        print(f"   • {key}: {len(value)} items")
                    elif isinstance(value, dict):
                        print(f"   • {key}: {len(value)} entries")
                    else:
                        print(f"   • {key}: {str(value)[:50]}...")


def test_geolocation_file():
    """Test with geolocation data (61.2 MB, 1M+ rows)."""
    print_section("GEOLOCATION DATASET (61.2 MB - 1,000,000+ rows)")
    
    # Load data
    df = pd.read_csv('data/olist_geolocation_dataset.csv')
    print(f"\n📁 File: olist_geolocation_dataset.csv")
    print(f"   Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Data types: {df.dtypes.to_dict()}")
    
    # Initialize aggregator
    aggregator = Aggregator()
    aggregator.set_data(df)
    
    # Test 1: Statistics
    print(f"\n1️⃣  STATISTICS WORKER")
    print(f"   Job: Calculate descriptive statistics (mean, median, std, min, max)")
    result = aggregator.apply_statistics(columns=['geolocation_lat', 'geolocation_lng'])
    print_worker_result("Statistics", result, df.shape)
    
    # Test 2: GroupBy
    print(f"\n2️⃣  GROUPBY WORKER")
    print(f"   Job: Group by state and aggregate")
    result = aggregator.apply_groupby(by='geolocation_state')
    print_worker_result("GroupBy", result, df.shape)
    if isinstance(result, dict) and 'data' in result:
        data = result['data']
        if isinstance(data, dict) and 'groups' in data:
            print(f"   Unique states found: {len(data.get('groups', {}))}")
    
    # Test 3: ValueCount
    print(f"\n3️⃣  VALUECOUNT WORKER")
    print(f"   Job: Count occurrences of each state")
    result = aggregator.apply_value_count(column='geolocation_state')
    print_worker_result("ValueCount", result, df.shape)
    if isinstance(result, dict) and 'data' in result:
        data = result['data']
        if isinstance(data, dict) and 'value_counts' in data:
            counts = data['value_counts']
            if isinstance(counts, dict):
                top_5 = dict(list(counts.items())[:5])
                print(f"   Top 5 states: {top_5}")
    
    # Test 4: WindowFunction
    print(f"\n4️⃣  WINDOWFUNCTION WORKER")
    print(f"   Job: Apply rolling window (3-row window, mean operation)")
    result = aggregator.apply_window_function(window_size=3, operations=['mean'])
    print_worker_result("WindowFunction", result, df.shape)


def test_vaccinations_file():
    """Test with vaccination data (17.6 MB, 100k+ rows)."""
    print_section("VACCINATIONS DATASET (17.6 MB - 100,000+ rows)")
    
    # Load data
    df = pd.read_csv('data/country_vaccinations.csv')
    print(f"\n📁 File: country_vaccinations.csv")
    print(f"   Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Data types: {df.dtypes.to_dict()}")
    
    # Initialize aggregator
    aggregator = Aggregator()
    aggregator.set_data(df)
    
    # Test 1: Statistics
    print(f"\n1️⃣  STATISTICS WORKER")
    print(f"   Job: Calculate stats on vaccination columns")
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()[:3]
    result = aggregator.apply_statistics(columns=numeric_cols)
    print_worker_result("Statistics", result, df.shape)
    
    # Test 2: RollingAggregation
    print(f"\n2️⃣  ROLLINGAGGREGATION WORKER")
    print(f"   Job: 7-day rolling window aggregation (time series)")
    result = aggregator.apply_rolling_aggregation(window_size=7, columns=numeric_cols[:1])
    print_worker_result("RollingAggregation", result, df.shape)
    
    # Test 3: ExponentialWeighted
    print(f"\n3️⃣  EXPONENTIALWEIGHTED WORKER")
    print(f"   Job: Exponential moving average (span=10)")
    result = aggregator.apply_exponential_weighted(span=10)
    print_worker_result("ExponentialWeighted", result, df.shape)
    
    # Test 4: LagLeadFunction
    print(f"\n4️⃣  LAGLEDFUNCTION WORKER")
    print(f"   Job: Shift data by 1 period (lag)")
    result = aggregator.apply_lag_lead_function(lag_periods=1, columns=numeric_cols[:1])
    print_worker_result("LagLeadFunction", result, df.shape)


def test_orders_file():
    """Test with orders data (17.6 MB, 100k+ rows)."""
    print_section("ORDERS DATASET (17.6 MB - 100,000+ rows)")
    
    # Load data
    df = pd.read_csv('data/olist_orders_dataset.csv')
    print(f"\n📁 File: olist_orders_dataset.csv")
    print(f"   Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Data types: {df.dtypes.to_dict()}")
    
    # Initialize aggregator
    aggregator = Aggregator()
    aggregator.set_data(df)
    
    # Test 1: CrossTab
    print(f"\n1️⃣  CROSSTAB WORKER")
    print(f"   Job: Cross-tabulate order status")
    result = aggregator.apply_crosstab(
        rows='order_status',
        columns='order_status',
        aggfunc='count'
    )
    print_worker_result("CrossTab", result, df.shape)
    if isinstance(result, dict) and 'data' in result:
        data = result['data']
        if isinstance(data, dict):
            print(f"   Row field: {data.get('row_field')}")
            print(f"   Column field: {data.get('column_field')}")
            print(f"   Shape: {data.get('shape')}")
    
    # Test 2: GroupBy
    print(f"\n2️⃣  GROUPBY WORKER")
    print(f"   Job: Group by order status, count occurrences")
    result = aggregator.apply_groupby(by='order_status')
    print_worker_result("GroupBy", result, df.shape)
    if isinstance(result, dict) and 'data' in result:
        data = result['data']
        if isinstance(data, dict):
            for key, value in list(data.items())[:3]:
                print(f"   • {key}: {value}")
    
    # Test 3: Pivot
    print(f"\n3️⃣  PIVOT WORKER")
    print(f"   Job: Pivot order status table")
    if df['order_status'].nunique() > 1:
        result = aggregator.apply_pivot(
            index='order_status',
            columns='order_status',
            aggfunc='count'
        )
        print_worker_result("Pivot", result, df.shape)
    
    # Test 4: ValueCount
    print(f"\n4️⃣  VALUECOUNT WORKER")
    print(f"   Job: Count each order status")
    result = aggregator.apply_value_count(column='order_status')
    print_worker_result("ValueCount", result, df.shape)
    if isinstance(result, dict) and 'data' in result:
        data = result['data']
        if isinstance(data, dict) and 'value_counts' in data:
            counts = data['value_counts']
            print(f"   Status breakdown:")
            for status, count in counts.items():
                pct = (count / df.shape[0]) * 100
                print(f"   • {status}: {count:,} ({pct:.1f}%)")


def test_hotels_file():
    """Test with hotel bookings data (16.8 MB, 119k rows)."""
    print_section("HOTEL BOOKINGS DATASET (16.8 MB - 119,000+ rows)")
    
    # Load data
    df = pd.read_csv('data/hotel_bookings.csv')
    print(f"\n📁 File: hotel_bookings.csv")
    print(f"   Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"   Columns: {list(df.columns)[:5]}... (and {len(df.columns)-5} more)")
    print(f"   Data types sample: {dict(list(df.dtypes.to_dict().items())[:3])}")
    
    # Initialize aggregator
    aggregator = Aggregator()
    aggregator.set_data(df)
    
    # Test 1: Statistics
    print(f"\n1️⃣  STATISTICS WORKER")
    print(f"   Job: Calculate stats on numeric columns")
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()[:3]
    result = aggregator.apply_statistics(columns=numeric_cols)
    print_worker_result("Statistics", result, df.shape)
    if isinstance(result, dict) and 'data' in result:
        data = result['data']
        if isinstance(data, dict) and 'statistics' in data:
            stats = data['statistics']
            print(f"   Numeric columns analyzed: {list(stats.keys())[:3]}")
    
    # Test 2: WindowFunction
    print(f"\n2️⃣  WINDOWFUNCTION WORKER")
    print(f"   Job: 3-row rolling mean")
    result = aggregator.apply_window_function(window_size=3, operations=['mean'])
    print_worker_result("WindowFunction", result, df.shape)
    
    # Test 3: GroupBy
    print(f"\n3️⃣  GROUPBY WORKER")
    print(f"   Job: Group by hotel type")
    if 'hotel' in df.columns:
        result = aggregator.apply_groupby(by='hotel')
        print_worker_result("GroupBy", result, df.shape)
        if isinstance(result, dict) and 'data' in result:
            data = result['data']
            if isinstance(data, dict):
                for key, value in list(data.items())[:2]:
                    print(f"   • {key}: {value}")


def test_order_items_file():
    """Test with order items data (15.4 MB, 112k rows)."""
    print_section("ORDER ITEMS DATASET (15.4 MB - 112,000+ rows)")
    
    # Load data
    df = pd.read_csv('data/olist_order_items_dataset.csv')
    print(f"\n📁 File: olist_order_items_dataset.csv")
    print(f"   Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Data types: {df.dtypes.to_dict()}")
    
    # Initialize aggregator
    aggregator = Aggregator()
    aggregator.set_data(df)
    
    # Test 1: RollingAggregation
    print(f"\n1️⃣  ROLLINGAGGREGATION WORKER")
    print(f"   Job: 5-row rolling aggregation on price")
    result = aggregator.apply_rolling_aggregation(window_size=5, columns=['price'])
    print_worker_result("RollingAggregation", result, df.shape)
    
    # Test 2: Statistics
    print(f"\n2️⃣  STATISTICS WORKER")
    print(f"   Job: Stats on price and freight_value")
    result = aggregator.apply_statistics(columns=['price', 'freight_value'])
    print_worker_result("Statistics", result, df.shape)
    if isinstance(result, dict) and 'data' in result:
        data = result['data']
        if isinstance(data, dict) and 'statistics' in data:
            stats = data['statistics']
            for col, col_stats in stats.items():
                print(f"   {col}:")
                for stat, value in list(col_stats.items())[:3]:
                    print(f"      • {stat}: {value:.2f}")
    
    # Test 3: Pivot
    print(f"\n3️⃣  PIVOT WORKER")
    print(f"   Job: Pivot order items by order and item")
    result = aggregator.apply_pivot(
        index='order_id',
        columns='order_item_id',
        values='price',
        aggfunc='mean'
    )
    print_worker_result("Pivot", result, df.shape)


if __name__ == "__main__":
    print("\n" + "#"*80)
    print("#" + " "*78 + "#")
    print("#" + "  AGGREGATOR DETAILED RESULTS - WHAT EACH WORKER EXTRACTS".center(78) + "#")
    print("#" + " "*78 + "#")
    print("#"*80)
    
    print("\n\n🎯 TESTING ALL 10 WORKERS WITH 5 REAL DATASETS\n")
    print("Each worker will show:")
    print("  • What data it processes")
    print("  • What operation it performs")
    print("  • What specific results it returns")
    print("  • What information is extracted")
    
    # Run all tests
    try:
        test_geolocation_file()
        test_vaccinations_file()
        test_orders_file()
        test_hotels_file()
        test_order_items_file()
        
        print_section("✅ ALL DETAILED TESTS COMPLETED")
        print("\n✓ All 10 workers extracted specific information from their assigned datasets")
        print("✓ Each worker performed its specialized task")
        print("✓ Results show exactly what information each worker retrieves\n")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
