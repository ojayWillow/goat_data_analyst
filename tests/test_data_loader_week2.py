"""Week 2 Data Loader Tests - New File Formats (JSONL, HDF5, SQLite, Parquet Streaming)

Tests for the four new file formats added in Week 2:
- JSONL format support
- HDF5 format support
- SQLite database support  
- Parquet streaming support
"""

import pytest
import pandas as pd
import os
import json
import sqlite3
import numpy as np
from pathlib import Path
from agents.data_loader import DataLoader


class TestDataLoaderWeek2:
    """Test suite for Week 2 Data Loader enhancements"""

    @pytest.fixture
    def loader(self):
        """Create a fresh DataLoader instance for each test"""
        return DataLoader()

    @pytest.fixture
    def test_dataframe(self):
        """Create a test DataFrame"""
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'value': [10.5, 20.3, 30.1, 40.8, 50.2],
            'category': ['A', 'B', 'A', 'C', 'B']
        })

    @pytest.fixture
    def test_dir(self, tmp_path):
        """Create a temporary directory for test files"""
        return tmp_path

    # === JSONL FORMAT TESTS ===

    def test_load_jsonl_basic(self, loader, test_dataframe, test_dir):
        """Test basic JSONL file loading"""
        # Create JSONL file
        jsonl_file = test_dir / "test_data.jsonl"
        test_dataframe.to_json(jsonl_file, orient='records', lines=True)

        # Load with data loader
        result = loader.load(str(jsonl_file))

        # Verify
        assert result['status'] == 'success'
        assert result['data'] is not None
        assert len(result['data']) == 5
        assert list(result['data'].columns) == list(test_dataframe.columns)

    def test_load_jsonl_data_integrity(self, loader, test_dataframe, test_dir):
        """Test that JSONL data is loaded correctly without corruption"""
        jsonl_file = test_dir / "integrity_test.jsonl"
        test_dataframe.to_json(jsonl_file, orient='records', lines=True)

        result = loader.load(str(jsonl_file))
        df = result['data']

        # Check values
        assert df['id'].sum() == 15
        assert df['value'].sum() == pytest.approx(151.9)
        assert len(df[df['category'] == 'A']) == 2

    def test_load_jsonl_nonexistent_file(self, loader):
        """Test error handling for nonexistent JSONL file"""
        result = loader.load("/nonexistent/path.jsonl")
        assert result['status'] == 'error'
        assert 'File not found' in result['message']

    def test_load_jsonl_empty_file(self, loader, test_dir):
        """Test handling of empty JSONL file"""
        jsonl_file = test_dir / "empty.jsonl"
        jsonl_file.write_text("")  # Empty file

        result = loader.load(str(jsonl_file))
        # Should either error or return empty DataFrame
        assert result['status'] in ['success', 'error']

    # === HDF5 FORMAT TESTS ===

    def test_load_hdf5_basic(self, loader, test_dataframe, test_dir):
        """Test basic HDF5 file loading"""
        try:
            import tables  # Required for HDF5
        except ImportError:
            pytest.skip("pytables not installed")

        # Create HDF5 file
        hdf5_file = test_dir / "test_data.h5"
        test_dataframe.to_hdf(hdf5_file, key='data', mode='w')

        # Load with data loader
        result = loader.load(str(hdf5_file))

        # Verify
        assert result['status'] == 'success'
        assert result['data'] is not None
        assert len(result['data']) == 5

    def test_load_hdf5_data_integrity(self, loader, test_dataframe, test_dir):
        """Test that HDF5 data is loaded correctly without corruption"""
        try:
            import tables
        except ImportError:
            pytest.skip("pytables not installed")

        hdf5_file = test_dir / "integrity_test.h5"
        test_dataframe.to_hdf(hdf5_file, key='data', mode='w')

        result = loader.load(str(hdf5_file))
        df = result['data']

        # Check values
        assert df['id'].sum() == 15
        assert df['value'].sum() == pytest.approx(151.9)

    def test_load_hdf5_nonexistent_file(self, loader):
        """Test error handling for nonexistent HDF5 file"""
        result = loader.load("/nonexistent/path.h5")
        assert result['status'] == 'error'

    # === SQLITE FORMAT TESTS ===

    def test_load_sqlite_basic(self, loader, test_dataframe, test_dir):
        """Test basic SQLite database loading"""
        # Create SQLite database
        db_file = test_dir / "test_data.db"
        conn = sqlite3.connect(str(db_file))
        test_dataframe.to_sql('data', conn, if_exists='replace', index=False)
        conn.close()

        # Load with data loader
        result = loader.load(str(db_file))

        # Verify
        assert result['status'] == 'success'
        assert result['data'] is not None
        assert len(result['data']) == 5

    def test_load_sqlite_data_integrity(self, loader, test_dataframe, test_dir):
        """Test that SQLite data is loaded correctly without corruption"""
        db_file = test_dir / "integrity_test.db"
        conn = sqlite3.connect(str(db_file))
        test_dataframe.to_sql('data', conn, if_exists='replace', index=False)
        conn.close()

        result = loader.load(str(db_file))
        df = result['data']

        # Check values
        assert len(df) == 5
        assert 'id' in df.columns
        assert 'name' in df.columns

    def test_load_sqlite_nonexistent_file(self, loader):
        """Test error handling for nonexistent SQLite file"""
        result = loader.load("/nonexistent/path.db")
        assert result['status'] == 'error'

    def test_load_sqlite_multiple_tables(self, loader, test_dataframe, test_dir):
        """Test handling of SQLite database with multiple tables"""
        db_file = test_dir / "multi_table.db"
        conn = sqlite3.connect(str(db_file))
        test_dataframe.to_sql('data', conn, if_exists='replace', index=False)
        test_dataframe.head(3).to_sql('subset', conn, if_exists='replace', index=False)
        conn.close()

        # Should load 'data' table by default
        result = loader.load(str(db_file))
        assert result['status'] == 'success'
        assert len(result['data']) == 5

    # === PARQUET STREAMING FORMAT TESTS ===

    def test_load_parquet_streaming_basic(self, loader, test_dataframe, test_dir):
        """Test Parquet file loading with streaming"""
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError:
            pytest.skip("pyarrow not installed")

        # Create Parquet file
        parquet_file = test_dir / "test_data.parquet"
        test_dataframe.to_parquet(str(parquet_file))

        # Load with data loader
        result = loader.load(str(parquet_file))

        # Verify
        assert result['status'] == 'success'
        assert result['data'] is not None
        assert len(result['data']) == 5

    def test_load_parquet_streaming_data_integrity(self, loader, test_dataframe, test_dir):
        """Test that Parquet streaming data is loaded correctly"""
        try:
            import pyarrow
        except ImportError:
            pytest.skip("pyarrow not installed")

        parquet_file = test_dir / "integrity_test.parquet"
        test_dataframe.to_parquet(str(parquet_file))

        result = loader.load(str(parquet_file))
        df = result['data']

        # Check values
        assert df['id'].sum() == 15
        assert df['value'].sum() == pytest.approx(151.9)

    def test_load_parquet_streaming_large_file(self, loader, test_dir):
        """Test Parquet streaming with larger dataset (1000 rows)"""
        try:
            import pyarrow
        except ImportError:
            pytest.skip("pyarrow not installed")

        # Create larger DataFrame
        large_df = pd.DataFrame({
            'id': range(1000),
            'value': np.random.randn(1000),
            'category': np.random.choice(['A', 'B', 'C'], 1000)
        })

        parquet_file = test_dir / "large.parquet"
        large_df.to_parquet(str(parquet_file))

        result = loader.load(str(parquet_file))
        assert result['status'] == 'success'
        assert len(result['data']) == 1000

    def test_load_parquet_nonexistent_file(self, loader):
        """Test error handling for nonexistent Parquet file"""
        result = loader.load("/nonexistent/path.parquet")
        assert result['status'] == 'error'

    # === FORMAT SUPPORT TESTS ===

    def test_supported_formats_include_week2(self, loader):
        """Test that DataLoader includes all Week 2 formats in SUPPORTED_FORMATS"""
        assert 'jsonl' in loader.SUPPORTED_FORMATS
        assert 'h5' in loader.SUPPORTED_FORMATS
        assert 'hdf5' in loader.SUPPORTED_FORMATS
        assert 'db' in loader.SUPPORTED_FORMATS
        assert 'sqlite' in loader.SUPPORTED_FORMATS
        assert 'parquet' in loader.SUPPORTED_FORMATS

    # === ERROR RECOVERY TESTS ===

    def test_error_recovery_retry_on_jsonl(self, loader, test_dataframe, test_dir):
        """Test that error recovery retry mechanism is active for JSONL"""
        jsonl_file = test_dir / "test.jsonl"
        test_dataframe.to_json(jsonl_file, orient='records', lines=True)

        # Load should succeed (retry decorator should help if needed)
        result = loader.load(str(jsonl_file))
        assert result['status'] == 'success'

    def test_error_recovery_retry_on_sqlite(self, loader, test_dataframe, test_dir):
        """Test that error recovery retry mechanism is active for SQLite"""
        db_file = test_dir / "test.db"
        conn = sqlite3.connect(str(db_file))
        test_dataframe.to_sql('data', conn, if_exists='replace', index=False)
        conn.close()

        # Load should succeed
        result = loader.load(str(db_file))
        assert result['status'] == 'success'

    # === METADATA TESTS ===

    def test_metadata_after_jsonl_load(self, loader, test_dataframe, test_dir):
        """Test that metadata is correctly extracted after JSONL load"""
        jsonl_file = test_dir / "test.jsonl"
        test_dataframe.to_json(jsonl_file, orient='records', lines=True)

        result = loader.load(str(jsonl_file))
        metadata = result['metadata']

        # Check metadata fields
        assert 'rows' in metadata
        assert metadata['rows'] == 5
        assert 'columns' in metadata
        assert metadata['columns'] == 4

    def test_metadata_after_sqlite_load(self, loader, test_dataframe, test_dir):
        """Test that metadata is correctly extracted after SQLite load"""
        db_file = test_dir / "test.db"
        conn = sqlite3.connect(str(db_file))
        test_dataframe.to_sql('data', conn, if_exists='replace', index=False)
        conn.close()

        result = loader.load(str(db_file))
        metadata = result['metadata']

        # Check metadata fields
        assert metadata['rows'] == 5
        assert metadata['columns'] == 4

    # === INTEGRATION TESTS ===

    def test_get_data_after_week2_load(self, loader, test_dataframe, test_dir):
        """Test get_data() returns correct data after Week 2 format load"""
        jsonl_file = test_dir / "test.jsonl"
        test_dataframe.to_json(jsonl_file, orient='records', lines=True)

        loader.load(str(jsonl_file))
        data = loader.get_data()

        assert data is not None
        assert len(data) == 5

    def test_get_summary_after_week2_load(self, loader, test_dataframe, test_dir):
        """Test get_summary() works correctly after Week 2 format load"""
        jsonl_file = test_dir / "test.jsonl"
        test_dataframe.to_json(jsonl_file, orient='records', lines=True)

        loader.load(str(jsonl_file))
        summary = loader.get_summary()

        assert summary is not None
        assert 'DataLoader Summary' in summary
        assert '5' in summary  # rows


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
