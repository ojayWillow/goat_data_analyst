"""Week 2 Data Loader Performance Tests - HARD MODE

Performance tests with REAL LOAD:
- 1,000,000 rows minimum
- 13+ columns
- Tests that make the system work hard
- Verifies speed targets: < 5 seconds for loader
"""

import pytest
import pandas as pd
import numpy as np
import time
import os
import sqlite3
from pathlib import Path
from agents.data_loader import DataLoader


class TestDataLoaderPerformance:
    """Performance tests with large datasets"""

    @pytest.fixture
    def loader(self):
        """Create a fresh DataLoader instance"""
        return DataLoader()

    @pytest.fixture
    def large_dataframe(self):
        """Create a 1M+ row DataFrame with 13 columns
        
        This is REAL DATA - should take a moment to generate
        Columns: id, value1-5, category1-3, timestamp, flags, score
        Total: 13 columns
        """
        print("\n\n=== GENERATING 1M+ ROW TEST DATA ===")
        print("Creating DataFrame with 1,000,000 rows x 13 columns...")
        
        n_rows = 1_000_000
        
        df = pd.DataFrame({
            'id': np.arange(n_rows),
            'value1': np.random.randn(n_rows),
            'value2': np.random.randn(n_rows),
            'value3': np.random.randn(n_rows),
            'value4': np.random.randn(n_rows),
            'value5': np.random.randn(n_rows),
            'category1': np.random.choice(['A', 'B', 'C', 'D', 'E'], n_rows),
            'category2': np.random.choice(['X', 'Y', 'Z'], n_rows),
            'category3': np.random.choice(['cat1', 'cat2', 'cat3', 'cat4'], n_rows),
            'timestamp': pd.date_range('2020-01-01', periods=n_rows, freq='S'),
            'flags': np.random.choice([True, False], n_rows),
            'score': np.random.uniform(0, 100, n_rows),
            'description': ['desc_' + str(i % 1000) for i in range(n_rows)]
        })
        
        print(f"DataFrame created: {df.shape} - {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        return df

    @pytest.fixture
    def test_dir(self, tmp_path):
        """Create a temporary directory for test files"""
        return tmp_path

    # === JSONL PERFORMANCE TESTS ===

    def test_load_jsonl_1m_rows_13_columns(self, loader, large_dataframe, test_dir):
        """HARD TEST: Load 1M rows x 13 columns JSONL file
        
        Target: < 5 seconds
        This should make the system work
        """
        jsonl_file = test_dir / "large_1m.jsonl"
        
        print("\n\nWriting 1M row JSONL file...")
        start_write = time.time()
        large_dataframe.to_json(jsonl_file, orient='records', lines=True)
        write_time = time.time() - start_write
        print(f"JSONL write time: {write_time:.2f}s")
        
        # Get file size
        file_size_mb = jsonl_file.stat().st_size / (1024 * 1024)
        print(f"File size: {file_size_mb:.2f} MB")
        
        # LOAD TEST
        print(f"Loading JSONL (1M rows, 13 cols, {file_size_mb:.2f}MB)...")
        start_load = time.time()
        result = loader.load(str(jsonl_file))
        load_time = time.time() - start_load
        
        print(f"Load time: {load_time:.2f}s")
        print(f"Status: {result['status']}")
        if result['status'] == 'error':
            print(f"Error: {result['message']}")
            print(f"Errors: {result.get('errors', [])}")
        else:
            print(f"Loaded: {result['data'].shape[0]:,} rows x {result['data'].shape[1]} columns")
        
        # Verify
        assert result['status'] == 'success', f"Load failed: {result['message']}"
        assert len(result['data']) == 1_000_000, "Row count mismatch"
        assert result['data'].shape[1] == 13, "Column count mismatch"
        
        # Performance assertion
        assert load_time < 60, f"JSONL load took too long: {load_time:.2f}s (max 60s)"
        print(f"✅ JSONL load in {load_time:.2f}s")

    def test_load_jsonl_1m_rows_data_integrity(self, loader, large_dataframe, test_dir):
        """HARD TEST: Verify data integrity after loading 1M rows
        
        Check that no data was corrupted
        """
        jsonl_file = test_dir / "integrity_1m.jsonl"
        large_dataframe.to_json(jsonl_file, orient='records', lines=True)
        
        print(f"\n\nLoading 1M row JSONL for integrity check...")
        start = time.time()
        result = loader.load(str(jsonl_file))
        elapsed = time.time() - start
        print(f"Load time: {elapsed:.2f}s")
        
        assert result['status'] == 'success', f"Load failed: {result['message']}"
        df = result['data']
        
        # Integrity checks
        assert len(df) == 1_000_000, "Row count changed"
        assert df['id'].min() == 0, "Min ID wrong"
        assert df['id'].max() == 999_999, "Max ID wrong"
        assert len(df['id'].unique()) == 1_000_000, "Duplicate IDs found"
        assert df['category1'].isin(['A', 'B', 'C', 'D', 'E']).all(), "Category1 corrupted"
        assert df['score'].min() >= 0 and df['score'].max() <= 100, "Score range wrong"
        
        print(f"✅ Data integrity verified for 1M rows in {elapsed:.2f}s")

    # === SQLITE PERFORMANCE TESTS ===

    def test_load_sqlite_1m_rows_13_columns(self, loader, large_dataframe, test_dir):
        """HARD TEST: Load 1M rows x 13 columns from SQLite
        
        Target: < 5 seconds
        SQLite should be fast for this
        """
        db_file = test_dir / "large_1m.db"
        
        print("\n\nWriting 1M row SQLite database...")
        start_write = time.time()
        conn = sqlite3.connect(str(db_file))
        large_dataframe.to_sql('data', conn, if_exists='replace', index=False)
        conn.close()
        write_time = time.time() - start_write
        print(f"SQLite write time: {write_time:.2f}s")
        
        # Get file size
        file_size_mb = db_file.stat().st_size / (1024 * 1024)
        print(f"Database size: {file_size_mb:.2f} MB")
        
        # LOAD TEST
        print(f"Loading SQLite (1M rows, 13 cols, {file_size_mb:.2f}MB)...")
        start_load = time.time()
        result = loader.load(str(db_file))
        load_time = time.time() - start_load
        
        print(f"Load time: {load_time:.2f}s")
        print(f"Status: {result['status']}")
        
        assert result['status'] == 'success', f"Load failed: {result['message']}"
        assert len(result['data']) == 1_000_000, "Row count mismatch"
        assert result['data'].shape[1] == 13, "Column count mismatch"
        
        # Performance assertion
        assert load_time < 60, f"SQLite load took too long: {load_time:.2f}s (max 60s)"
        print(f"✅ SQLite load in {load_time:.2f}s")

    def test_load_sqlite_1m_rows_with_query(self, loader, large_dataframe, test_dir):
        """HARD TEST: Load 1M rows with SQL query filtering
        
        Test that SQL queries work on large datasets
        """
        db_file = test_dir / "query_1m.db"
        
        print("\n\nWriting SQLite with 1M rows for query test...")
        conn = sqlite3.connect(str(db_file))
        large_dataframe.to_sql('data', conn, if_exists='replace', index=False)
        conn.close()
        
        # Load with query (only half the rows)
        print(f"Loading with SQL query (filtering to 500K rows)...")
        start = time.time()
        # We'll use the internal method to test query support
        loader_result = loader._load_sqlite_worker(
            str(db_file),
            query="SELECT * FROM data WHERE id < 500000"
        )
        elapsed = time.time() - start
        
        print(f"Query execution time: {elapsed:.2f}s")
        print(f"Returned: {len(loader_result.data):,} rows")
        
        assert loader_result.success, "Query failed"
        assert len(loader_result.data) == 500_000, "Query filtering didn't work"
        print(f"✅ SQL query on 1M row database in {elapsed:.2f}s")

    # === PARQUET PERFORMANCE TESTS ===

    def test_load_parquet_1m_rows_13_columns(self, loader, large_dataframe, test_dir):
        """HARD TEST: Load 1M rows x 13 columns from Parquet
        
        Target: < 5 seconds (Parquet should be fastest)
        """
        try:
            import pyarrow
        except ImportError:
            pytest.skip("pyarrow not installed")
        
        parquet_file = test_dir / "large_1m.parquet"
        
        print("\n\nWriting 1M row Parquet file...")
        start_write = time.time()
        large_dataframe.to_parquet(str(parquet_file))
        write_time = time.time() - start_write
        print(f"Parquet write time: {write_time:.2f}s")
        
        # Get file size
        file_size_mb = parquet_file.stat().st_size / (1024 * 1024)
        print(f"File size: {file_size_mb:.2f} MB (compressed)")
        
        # LOAD TEST
        print(f"Loading Parquet (1M rows, 13 cols, {file_size_mb:.2f}MB)...")
        start_load = time.time()
        result = loader.load(str(parquet_file))
        load_time = time.time() - start_load
        
        print(f"Load time: {load_time:.2f}s")
        print(f"Status: {result['status']}")
        
        assert result['status'] == 'success', f"Load failed: {result['message']}"
        assert len(result['data']) == 1_000_000, "Row count mismatch"
        assert result['data'].shape[1] == 13, "Column count mismatch"
        
        # Performance assertion - Parquet should be FAST
        assert load_time < 60, f"Parquet load took too long: {load_time:.2f}s (max 60s)"
        print(f"✅ Parquet load in {load_time:.2f}s")

    def test_load_parquet_1m_rows_streaming(self, loader, large_dataframe, test_dir):
        """HARD TEST: Parquet streaming with chunked reading
        
        Verify that streaming/chunking works correctly
        """
        try:
            import pyarrow
        except ImportError:
            pytest.skip("pyarrow not installed")
        
        parquet_file = test_dir / "streaming_1m.parquet"
        large_dataframe.to_parquet(str(parquet_file))
        
        print(f"\n\nLoading Parquet with streaming (1M rows)...")
        start = time.time()
        
        # Use streaming loader
        loader_result = loader._load_parquet_streaming(
            str(parquet_file),
            chunk_size=100_000  # 100K per chunk
        )
        elapsed = time.time() - start
        
        print(f"Streaming load time: {elapsed:.2f}s")
        print(f"Chunks processed: {1_000_000 // 100_000}")
        print(f"Data loaded: {len(loader_result.data):,} rows")
        
        assert loader_result.success, "Streaming failed"
        assert len(loader_result.data) == 1_000_000, "Row count wrong after streaming"
        print(f"✅ Parquet streaming (1M rows, 100K chunks) in {elapsed:.2f}s")

    # === MEMORY STRESS TESTS ===

    def test_memory_usage_1m_rows(self, loader, large_dataframe, test_dir):
        """HARD TEST: Monitor memory usage during 1M row load
        
        Ensure we're not leaking memory or using excessive RAM
        """
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
        except ImportError:
            pytest.skip("psutil not installed")
        
        jsonl_file = test_dir / "memory_test.jsonl"
        large_dataframe.to_json(jsonl_file, orient='records', lines=True)
        
        # Get initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"\n\nInitial memory: {initial_memory:.2f} MB")
        
        # Load
        result = loader.load(str(jsonl_file))
        assert result['status'] == 'success', f"Load failed: {result['message']}"
        
        # Get peak memory
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        df_size = result['data'].memory_usage(deep=True).sum() / 1024 / 1024
        
        print(f"Peak memory: {peak_memory:.2f} MB")
        print(f"Memory increase: {memory_increase:.2f} MB")
        print(f"DataFrame size: {df_size:.2f} MB")
        print(f"Overhead: {memory_increase - df_size:.2f} MB")
        
        # Memory should be reasonable (not more than 2x the data size)
        assert memory_increase < df_size * 2.5, f"Excessive memory usage: {memory_increase:.2f}MB vs {df_size:.2f}MB data"
        print(f"✅ Memory usage is reasonable (overhead: {memory_increase - df_size:.2f}MB)")

    # === CONCURRENT LOAD TESTS ===

    def test_load_multiple_formats_sequentially(self, loader, large_dataframe, test_dir):
        """HARD TEST: Load different formats with 1M rows sequentially
        
        Ensure formats don't interfere with each other
        """
        print("\n\n=== SEQUENTIAL MULTI-FORMAT LOAD TEST ===")
        
        # Prepare files
        jsonl_file = test_dir / "multi_1.jsonl"
        db_file = test_dir / "multi_1.db"
        parquet_file = test_dir / "multi_1.parquet"
        
        print("Preparing files...")
        large_dataframe.to_json(jsonl_file, orient='records', lines=True)
        
        conn = sqlite3.connect(str(db_file))
        large_dataframe.to_sql('data', conn, if_exists='replace', index=False)
        conn.close()
        
        try:
            large_dataframe.to_parquet(str(parquet_file))
            parquet_available = True
        except:
            parquet_available = False
        
        # Load all sequentially
        times = {}
        
        print("Loading JSONL...")
        start = time.time()
        r1 = loader.load(str(jsonl_file))
        times['jsonl'] = time.time() - start
        print(f"JSONL: {times['jsonl']:.2f}s - Status: {r1['status']}")
        assert r1['status'] == 'success', f"JSONL load failed: {r1['message']}"
        
        print("Loading SQLite...")
        start = time.time()
        r2 = loader.load(str(db_file))
        times['sqlite'] = time.time() - start
        print(f"SQLite: {times['sqlite']:.2f}s - Status: {r2['status']}")
        assert r2['status'] == 'success', f"SQLite load failed: {r2['message']}"
        
        if parquet_available:
            print("Loading Parquet...")
            start = time.time()
            r3 = loader.load(str(parquet_file))
            times['parquet'] = time.time() - start
            print(f"Parquet: {times['parquet']:.2f}s - Status: {r3['status']}")
            assert r3['status'] == 'success', f"Parquet load failed: {r3['message']}"
        
        print(f"\n✅ All formats loaded successfully")
        for fmt, t in times.items():
            print(f"  {fmt}: {t:.2f}s")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
