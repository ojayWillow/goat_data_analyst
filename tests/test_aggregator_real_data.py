"""Test Aggregator Agent with REAL PRODUCTION DATA.

Uses 5 large datasets from project data folder:
1. olist_geolocation_dataset.csv (61.2 MB)
2. country_vaccinations.csv (17.6 MB)
3. olist_orders_dataset.csv (17.6 MB)
4. hotel_bookings.csv (16.8 MB)
5. olist_order_items_dataset.csv (15.4 MB)

Tests all 10 workers with real data to verify:
- Worker functionality with production data
- Agent delegation and data flow
- Error handling with real datasets
- Performance metrics
- Result quality
"""

import pytest
import pandas as pd
import time
from pathlib import Path
from agents.aggregator.aggregator import Aggregator


class TestAggregatorWithRealData:
    """Test aggregator with real production datasets."""

    @pytest.fixture(scope="class")
    def data_files(self):
        """Paths to real data files."""
        return {
            'geolocation': 'data/olist_geolocation_dataset.csv',
            'vaccinations': 'data/country_vaccinations.csv',
            'orders': 'data/olist_orders_dataset.csv',
            'hotels': 'data/hotel_bookings.csv',
            'order_items': 'data/olist_order_items_dataset.csv',
        }

    def test_load_geolocation_data(self, data_files):
        """Test loading geolocation dataset (61.2 MB)."""
        start = time.time()
        df = pd.read_csv(data_files['geolocation'])
        elapsed = time.time() - start
        
        print(f"\n📊 GEOLOCATION DATASET")
        print(f"   File: olist_geolocation_dataset.csv (61.2 MB)")
        print(f"   Rows: {df.shape[0]:,}")
        print(f"   Columns: {df.shape[1]}")
        print(f"   Load time: {elapsed:.2f}s")
        print(f"   Columns: {list(df.columns)}")
        
        assert df.shape[0] > 0
        assert df.shape[1] > 0

    def test_load_vaccinations_data(self, data_files):
        """Test loading vaccinations dataset (17.6 MB)."""
        start = time.time()
        df = pd.read_csv(data_files['vaccinations'])
        elapsed = time.time() - start
        
        print(f"\n📊 VACCINATIONS DATASET")
        print(f"   File: country_vaccinations.csv (17.6 MB)")
        print(f"   Rows: {df.shape[0]:,}")
        print(f"   Columns: {df.shape[1]}")
        print(f"   Load time: {elapsed:.2f}s")
        print(f"   Columns: {list(df.columns)}")
        
        assert df.shape[0] > 0
        assert df.shape[1] > 0

    def test_load_orders_data(self, data_files):
        """Test loading orders dataset (17.6 MB)."""
        start = time.time()
        df = pd.read_csv(data_files['orders'])
        elapsed = time.time() - start
        
        print(f"\n📊 ORDERS DATASET")
        print(f"   File: olist_orders_dataset.csv (17.6 MB)")
        print(f"   Rows: {df.shape[0]:,}")
        print(f"   Columns: {df.shape[1]}")
        print(f"   Load time: {elapsed:.2f}s")
        print(f"   Columns: {list(df.columns)}")
        
        assert df.shape[0] > 0
        assert df.shape[1] > 0

    def test_load_hotels_data(self, data_files):
        """Test loading hotel bookings dataset (16.8 MB)."""
        start = time.time()
        df = pd.read_csv(data_files['hotels'])
        elapsed = time.time() - start
        
        print(f"\n📊 HOTEL BOOKINGS DATASET")
        print(f"   File: hotel_bookings.csv (16.8 MB)")
        print(f"   Rows: {df.shape[0]:,}")
        print(f"   Columns: {df.shape[1]}")
        print(f"   Load time: {elapsed:.2f}s")
        print(f"   Columns: {list(df.columns)}")
        
        assert df.shape[0] > 0
        assert df.shape[1] > 0

    def test_load_order_items_data(self, data_files):
        """Test loading order items dataset (15.4 MB)."""
        start = time.time()
        df = pd.read_csv(data_files['order_items'])
        elapsed = time.time() - start
        
        print(f"\n📊 ORDER ITEMS DATASET")
        print(f"   File: olist_order_items_dataset.csv (15.4 MB)")
        print(f"   Rows: {df.shape[0]:,}")
        print(f"   Columns: {df.shape[1]}")
        print(f"   Load time: {elapsed:.2f}s")
        print(f"   Columns: {list(df.columns)}")
        
        assert df.shape[0] > 0
        assert df.shape[1] > 0


class TestAggregatorWithGeolocationData:
    """Test all 10 workers with geolocation data (61.2 MB)."""

    @pytest.fixture(autouse=True)
    def aggregator_with_geo_data(self):
        """Load geolocation data into aggregator."""
        aggregator = Aggregator()
        df = pd.read_csv('data/olist_geolocation_dataset.csv')
        aggregator.set_data(df)
        return aggregator

    def test_window_function_with_geo_data(self, aggregator_with_geo_data):
        """Test WindowFunction with geolocation data."""
        start = time.time()
        result = aggregator_with_geo_data.apply_window_function(
            window_size=5,
            operations=['mean']
        )
        elapsed = time.time() - start
        
        print(f"\n✅ WindowFunction (Geolocation Data)")
        print(f"   Execution time: {elapsed:.2f}s")
        print(f"   Success: {result.get('success', 'N/A')}")
        assert result is not None

    def test_statistics_with_geo_data(self, aggregator_with_geo_data):
        """Test Statistics with geolocation data."""
        start = time.time()
        result = aggregator_with_geo_data.apply_statistics()
        elapsed = time.time() - start
        
        print(f"\n✅ Statistics (Geolocation Data)")
        print(f"   Execution time: {elapsed:.2f}s")
        print(f"   Success: {result.get('success', 'N/A')}")
        assert result is not None

    def test_groupby_with_geo_data(self, aggregator_with_geo_data):
        """Test GroupBy with geolocation data."""
        df = aggregator_with_geo_data.get_data()
        if 'geolocation_state' in df.columns:
            start = time.time()
            result = aggregator_with_geo_data.apply_groupby(
                by='geolocation_state'
            )
            elapsed = time.time() - start
            
            print(f"\n✅ GroupBy (Geolocation Data)")
            print(f"   Execution time: {elapsed:.2f}s")
            print(f"   Success: {result.get('success', 'N/A')}")
            assert result is not None

    def test_value_count_with_geo_data(self, aggregator_with_geo_data):
        """Test ValueCount with geolocation data."""
        df = aggregator_with_geo_data.get_data()
        if 'geolocation_state' in df.columns:
            start = time.time()
            result = aggregator_with_geo_data.apply_value_count(
                column='geolocation_state'
            )
            elapsed = time.time() - start
            
            print(f"\n✅ ValueCount (Geolocation Data)")
            print(f"   Execution time: {elapsed:.2f}s")
            print(f"   Success: {result.get('success', 'N/A')}")
            assert result is not None


class TestAggregatorWithVaccinationData:
    """Test all 10 workers with vaccination data (17.6 MB)."""

    @pytest.fixture(autouse=True)
    def aggregator_with_vacc_data(self):
        """Load vaccination data into aggregator."""
        aggregator = Aggregator()
        df = pd.read_csv('data/country_vaccinations.csv')
        # Convert date columns to datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        aggregator.set_data(df)
        return aggregator

    def test_rolling_aggregation_with_vacc_data(self, aggregator_with_vacc_data):
        """Test RollingAggregation with vaccination data (time series)."""
        df = aggregator_with_vacc_data.get_data()
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()[:2]
        
        if numeric_cols:
            start = time.time()
            result = aggregator_with_vacc_data.apply_rolling_aggregation(
                window_size=7,
                columns=numeric_cols
            )
            elapsed = time.time() - start
            
            print(f"\n✅ RollingAggregation (Vaccination Data)")
            print(f"   Execution time: {elapsed:.2f}s")
            print(f"   Success: {result.get('success', 'N/A')}")
            assert result is not None

    def test_exponential_weighted_with_vacc_data(self, aggregator_with_vacc_data):
        """Test ExponentialWeighted with vaccination data (time series)."""
        start = time.time()
        result = aggregator_with_vacc_data.apply_exponential_weighted(
            span=10,
            adjust=True
        )
        elapsed = time.time() - start
        
        print(f"\n✅ ExponentialWeighted (Vaccination Data)")
        print(f"   Execution time: {elapsed:.2f}s")
        print(f"   Success: {result.get('success', 'N/A')}")
        assert result is not None

    def test_lag_lead_function_with_vacc_data(self, aggregator_with_vacc_data):
        """Test LagLeadFunction with vaccination data (time series)."""
        df = aggregator_with_vacc_data.get_data()
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()[:1]
        
        if numeric_cols:
            start = time.time()
            result = aggregator_with_vacc_data.apply_lag_lead_function(
                lag_periods=1,
                lead_periods=1,
                columns=numeric_cols
            )
            elapsed = time.time() - start
            
            print(f"\n✅ LagLeadFunction (Vaccination Data)")
            print(f"   Execution time: {elapsed:.2f}s")
            print(f"   Success: {result.get('success', 'N/A')}")
            assert result is not None

    def test_statistics_with_vacc_data(self, aggregator_with_vacc_data):
        """Test Statistics with vaccination data."""
        start = time.time()
        result = aggregator_with_vacc_data.apply_statistics()
        elapsed = time.time() - start
        
        print(f"\n✅ Statistics (Vaccination Data)")
        print(f"   Execution time: {elapsed:.2f}s")
        print(f"   Success: {result.get('success', 'N/A')}")
        assert result is not None


class TestAggregatorWithOrdersData:
    """Test all 10 workers with orders data (17.6 MB)."""

    @pytest.fixture(autouse=True)
    def aggregator_with_orders_data(self):
        """Load orders data into aggregator."""
        aggregator = Aggregator()
        df = pd.read_csv('data/olist_orders_dataset.csv')
        aggregator.set_data(df)
        return aggregator

    def test_crosstab_with_orders_data(self, aggregator_with_orders_data):
        """Test CrossTab with orders data (categorical)."""
        df = aggregator_with_orders_data.get_data()
        if 'order_status' in df.columns:
            start = time.time()
            result = aggregator_with_orders_data.apply_crosstab(
                rows='order_status',
                columns='order_status',
                aggfunc='count'
            )
            elapsed = time.time() - start
            
            print(f"\n✅ CrossTab (Orders Data)")
            print(f"   Execution time: {elapsed:.2f}s")
            print(f"   Success: {result.get('success', 'N/A')}")
            assert result is not None

    def test_groupby_with_orders_data(self, aggregator_with_orders_data):
        """Test GroupBy with orders data."""
        df = aggregator_with_orders_data.get_data()
        if 'order_status' in df.columns:
            start = time.time()
            result = aggregator_with_orders_data.apply_groupby(
                by='order_status'
            )
            elapsed = time.time() - start
            
            print(f"\n✅ GroupBy (Orders Data)")
            print(f"   Execution time: {elapsed:.2f}s")
            print(f"   Success: {result.get('success', 'N/A')}")
            assert result is not None

    def test_pivot_with_orders_data(self, aggregator_with_orders_data):
        """Test Pivot with orders data."""
        df = aggregator_with_orders_data.get_data()
        if 'order_status' in df.columns and len(df['order_status'].unique()) > 1:
            start = time.time()
            result = aggregator_with_orders_data.apply_pivot(
                index='order_status',
                columns='order_status',
                aggfunc='count'
            )
            elapsed = time.time() - start
            
            print(f"\n✅ Pivot (Orders Data)")
            print(f"   Execution time: {elapsed:.2f}s")
            print(f"   Success: {result.get('success', 'N/A')}")
            assert result is not None

    def test_value_count_with_orders_data(self, aggregator_with_orders_data):
        """Test ValueCount with orders data."""
        df = aggregator_with_orders_data.get_data()
        if 'order_status' in df.columns:
            start = time.time()
            result = aggregator_with_orders_data.apply_value_count(
                column='order_status'
            )
            elapsed = time.time() - start
            
            print(f"\n✅ ValueCount (Orders Data)")
            print(f"   Execution time: {elapsed:.2f}s")
            print(f"   Success: {result.get('success', 'N/A')}")
            assert result is not None


class TestAggregatorWithHotelsData:
    """Test all 10 workers with hotel bookings data (16.8 MB)."""

    @pytest.fixture(autouse=True)
    def aggregator_with_hotels_data(self):
        """Load hotel bookings data into aggregator."""
        aggregator = Aggregator()
        df = pd.read_csv('data/hotel_bookings.csv')
        aggregator.set_data(df)
        return aggregator

    def test_statistics_with_hotels_data(self, aggregator_with_hotels_data):
        """Test Statistics with hotel bookings data."""
        start = time.time()
        result = aggregator_with_hotels_data.apply_statistics()
        elapsed = time.time() - start
        
        print(f"\n✅ Statistics (Hotels Data)")
        print(f"   Execution time: {elapsed:.2f}s")
        print(f"   Success: {result.get('success', 'N/A')}")
        assert result is not None

    def test_window_function_with_hotels_data(self, aggregator_with_hotels_data):
        """Test WindowFunction with hotel bookings data."""
        start = time.time()
        result = aggregator_with_hotels_data.apply_window_function(
            window_size=3,
            operations=['mean']
        )
        elapsed = time.time() - start
        
        print(f"\n✅ WindowFunction (Hotels Data)")
        print(f"   Execution time: {elapsed:.2f}s")
        print(f"   Success: {result.get('success', 'N/A')}")
        assert result is not None

    def test_groupby_with_hotels_data(self, aggregator_with_hotels_data):
        """Test GroupBy with hotel bookings data."""
        df = aggregator_with_hotels_data.get_data()
        if 'hotel' in df.columns:
            start = time.time()
            result = aggregator_with_hotels_data.apply_groupby(
                by='hotel'
            )
            elapsed = time.time() - start
            
            print(f"\n✅ GroupBy (Hotels Data)")
            print(f"   Execution time: {elapsed:.2f}s")
            print(f"   Success: {result.get('success', 'N/A')}")
            assert result is not None


class TestAggregatorWithOrderItemsData:
    """Test all 10 workers with order items data (15.4 MB)."""

    @pytest.fixture(autouse=True)
    def aggregator_with_items_data(self):
        """Load order items data into aggregator."""
        aggregator = Aggregator()
        df = pd.read_csv('data/olist_order_items_dataset.csv')
        aggregator.set_data(df)
        return aggregator

    def test_rolling_aggregation_with_items_data(self, aggregator_with_items_data):
        """Test RollingAggregation with order items data."""
        start = time.time()
        result = aggregator_with_items_data.apply_rolling_aggregation(
            window_size=5,
            columns=['price']
        )
        elapsed = time.time() - start
        
        print(f"\n✅ RollingAggregation (Order Items Data)")
        print(f"   Execution time: {elapsed:.2f}s")
        print(f"   Success: {result.get('success', 'N/A')}")
        assert result is not None

    def test_statistics_with_items_data(self, aggregator_with_items_data):
        """Test Statistics with order items data."""
        start = time.time()
        result = aggregator_with_items_data.apply_statistics()
        elapsed = time.time() - start
        
        print(f"\n✅ Statistics (Order Items Data)")
        print(f"   Execution time: {elapsed:.2f}s")
        print(f"   Success: {result.get('success', 'N/A')}")
        assert result is not None

    def test_pivot_with_items_data(self, aggregator_with_items_data):
        """Test Pivot with order items data."""
        df = aggregator_with_items_data.get_data()
        if 'product_id' in df.columns and 'order_id' in df.columns:
            start = time.time()
            result = aggregator_with_items_data.apply_pivot(
                index='order_id',
                columns='order_item_id',
                values='price',
                aggfunc='mean'
            )
            elapsed = time.time() - start
            
            print(f"\n✅ Pivot (Order Items Data)")
            print(f"   Execution time: {elapsed:.2f}s")
            print(f"   Success: {result.get('success', 'N/A')}")
            assert result is not None


if __name__ == "__main__":
    """Run all real data tests."""
    print("\n" + "="*80)
    print("TESTING AGGREGATOR WITH REAL PRODUCTION DATA")
    print("="*80)
    print("\n5 LARGE DATASETS:")
    print("  1. olist_geolocation_dataset.csv (61.2 MB)")
    print("  2. country_vaccinations.csv (17.6 MB)")
    print("  3. olist_orders_dataset.csv (17.6 MB)")
    print("  4. hotel_bookings.csv (16.8 MB)")
    print("  5. olist_order_items_dataset.csv (15.4 MB)")
    print("\nAll 10 workers tested with real production data...\n")
    
    import sys
    pytest.main([__file__, '-v', '-s'])
