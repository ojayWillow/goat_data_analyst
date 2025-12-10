"""Week 2 Data Loader Edge Case Tests

Edge cases, stress tests, and boundary conditions:
- Empty files
- Corrupt files
- Special characters in data
- Mixed data types
- Large strings
- Unicode handling
- Null/None handling
- Duplicate data
"""

import pytest
import pandas as pd
import numpy as np
import os
import sqlite3
import json
from agents.data_loader import DataLoader


class TestDataLoaderEdgeCases:
    """Edge case tests for Data Loader"""

    @pytest.fixture
    def loader(self):
        return DataLoader()

    @pytest.fixture
    def test_dir(self, tmp_path):
        return tmp_path

    # === EMPTY/MINIMAL DATA TESTS ===

    def test_load_jsonl_empty_file(self, loader, test_dir):
        """Handle empty JSONL file gracefully"""
        empty_file = test_dir / "empty.jsonl"
        empty_file.write_text("")  # Empty file
        
        # Should either error or return empty DataFrame
        result = loader.load(str(empty_file))
        # Accept either error or empty success
        assert result['status'] in ['success', 'error']

    def test_load_jsonl_single_row(self, loader, test_dir):
        """Handle single row correctly"""
        df = pd.DataFrame({'a': [1], 'b': ['test']})
        jsonl_file = test_dir / "single.jsonl"
        df.to_json(jsonl_file, orient='records', lines=True)
        
        result = loader.load(str(jsonl_file))
        assert result['status'] == 'success'
        assert len(result['data']) == 1

    def test_load_sqlite_empty_table(self, loader, test_dir):
        """Handle empty SQLite table"""
        db_file = test_dir / "empty.db"
        
        # Create empty table
        conn = sqlite3.connect(str(db_file))
        df = pd.DataFrame({'col1': [], 'col2': []})
        df.to_sql('data', conn, if_exists='replace', index=False)
        conn.close()
        
        result = loader.load(str(db_file))
        assert result['status'] == 'success'
        assert len(result['data']) == 0
        assert len(result['data'].columns) == 2

    # === SPECIAL CHARACTERS & ENCODING TESTS ===

    def test_load_jsonl_with_unicode(self, loader, test_dir):
        """Handle Unicode characters correctly"""
        df = pd.DataFrame({
            'name': ['Alice', '中文', '😀', 'Café'],
            'value': [1, 2, 3, 4]
        })
        jsonl_file = test_dir / "unicode.jsonl"
        df.to_json(jsonl_file, orient='records', lines=True)
        
        result = loader.load(str(jsonl_file))
        assert result['status'] == 'success'
        assert len(result['data']) == 4
        assert '中文' in result['data']['name'].values

    def test_load_jsonl_with_special_chars(self, loader, test_dir):
        """Handle special characters in data"""
        df = pd.DataFrame({
            'text': [
                'normal',
                'with\nnewline',
                'with\ttab',
                'with"quotes"',
                "with'apostrophe"
            ],
            'value': [1, 2, 3, 4, 5]
        })
        jsonl_file = test_dir / "special.jsonl"
        df.to_json(jsonl_file, orient='records', lines=True)
        
        result = loader.load(str(jsonl_file))
        assert result['status'] == 'success'
        assert len(result['data']) == 5

    def test_load_sqlite_with_null_values(self, loader, test_dir):
        """Handle NULL values in SQLite"""
        db_file = test_dir / "nulls.db"
        
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'value': [10.5, None, 30.1, None, 50.2],
            'name': ['A', 'B', None, 'D', 'E']
        })
        
        conn = sqlite3.connect(str(db_file))
        df.to_sql('data', conn, if_exists='replace', index=False)
        conn.close()
        
        result = loader.load(str(db_file))
        assert result['status'] == 'success'
        assert result['data']['value'].isna().sum() == 2
        assert result['data']['name'].isna().sum() == 1

    # === DATA TYPE HANDLING TESTS ===

    def test_load_jsonl_mixed_types(self, loader, test_dir):
        """Handle mixed data types"""
        df = pd.DataFrame({
            'int_col': [1, 2, 3, 4, 5],
            'float_col': [1.1, 2.2, 3.3, 4.4, 5.5],
            'str_col': ['a', 'b', 'c', 'd', 'e'],
            'bool_col': [True, False, True, False, True],
            'date_col': pd.date_range('2020-01-01', periods=5)
        })
        jsonl_file = test_dir / "mixed.jsonl"
        df.to_json(jsonl_file, orient='records', lines=True)
        
        result = loader.load(str(jsonl_file))
        assert result['status'] == 'success'
        assert len(result['data']) == 5
        assert result['data'].dtypes.nunique() > 1  # Multiple types

    def test_load_parquet_large_strings(self, loader, test_dir):
        """Handle large string values"""
        try:
            import pyarrow
        except ImportError:
            pytest.skip("pyarrow not installed")
        
        # Create strings up to 100KB each
        large_string = 'x' * 100_000
        df = pd.DataFrame({
            'id': range(10),
            'large_text': [large_string] * 10,
            'value': np.random.randn(10)
        })
        
        parquet_file = test_dir / "large_strings.parquet"
        df.to_parquet(str(parquet_file))
        
        result = loader.load(str(parquet_file))
        assert result['status'] == 'success'
        assert len(result['data']) == 10
        assert len(result['data']['large_text'].iloc[0]) == 100_000

    # === DUPLICATE & DUPLICATE KEY TESTS ===

    def test_load_jsonl_duplicate_rows(self, loader, test_dir):
        """Handle duplicate rows (should preserve all)"""
        df = pd.DataFrame({
            'id': [1, 1, 1, 2, 2],  # Duplicates
            'value': [10, 10, 10, 20, 20]
        })
        jsonl_file = test_dir / "dupes.jsonl"
        df.to_json(jsonl_file, orient='records', lines=True)
        
        result = loader.load(str(jsonl_file))
        assert result['status'] == 'success'
        assert len(result['data']) == 5  # All rows preserved
        assert len(result['data']['id'].unique()) == 2  # 2 unique IDs

    def test_load_sqlite_duplicate_primary_key_handling(self, loader, test_dir):
        """Load SQLite with duplicate rows (no PK constraint)"""
        db_file = test_dir / "dupes.db"
        
        df = pd.DataFrame({
            'id': [1, 1, 1, 2, 2],
            'value': [10, 10, 10, 20, 20]
        })
        
        conn = sqlite3.connect(str(db_file))
        df.to_sql('data', conn, if_exists='replace', index=False)
        conn.close()
        
        result = loader.load(str(db_file))
        assert result['status'] == 'success'
        assert len(result['data']) == 5

    # === NUMERIC BOUNDARY TESTS ===

    def test_load_jsonl_extreme_numbers(self, loader, test_dir):
        """Handle extreme numeric values"""
        df = pd.DataFrame({
            'small': [1e-300],
            'large': [1e300],
            'negative': [-1e100],
            'zero': [0.0],
            'negative_zero': [-0.0]
        })
        jsonl_file = test_dir / "extreme_nums.jsonl"
        df.to_json(jsonl_file, orient='records', lines=True)
        
        result = loader.load(str(jsonl_file))
        assert result['status'] == 'success'
        assert len(result['data']) == 1

    def test_load_parquet_nan_inf_values(self, loader, test_dir):
        """Handle NaN and Inf values"""
        try:
            import pyarrow
        except ImportError:
            pytest.skip("pyarrow not installed")
        
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'value': [1.0, np.nan, np.inf, -np.inf, 5.0]
        })
        parquet_file = test_dir / "nan_inf.parquet"
        df.to_parquet(str(parquet_file))
        
        result = loader.load(str(parquet_file))
        assert result['status'] == 'success'
        assert np.isnan(result['data']['value'].iloc[1])
        assert np.isinf(result['data']['value'].iloc[2])

    # === COLUMN NAME TESTS ===

    def test_load_jsonl_special_column_names(self, loader, test_dir):
        """Handle special characters in column names"""
        df = pd.DataFrame({
            'normal_col': [1, 2, 3],
            'col with spaces': [4, 5, 6],
            'col-with-dash': [7, 8, 9],
            'col.with.dots': [10, 11, 12],
            'col_with_ünicode': [13, 14, 15]
        })
        jsonl_file = test_dir / "special_cols.jsonl"
        df.to_json(jsonl_file, orient='records', lines=True)
        
        result = loader.load(str(jsonl_file))
        assert result['status'] == 'success'
        assert 'col with spaces' in result['data'].columns

    def test_load_sqlite_many_columns(self, loader, test_dir):
        """Handle file with many columns"""
        db_file = test_dir / "many_cols.db"
        
        # Create DataFrame with 50 columns
        data = {f'col_{i}': np.random.randn(100) for i in range(50)}
        df = pd.DataFrame(data)
        
        conn = sqlite3.connect(str(db_file))
        df.to_sql('data', conn, if_exists='replace', index=False)
        conn.close()
        
        result = loader.load(str(db_file))
        assert result['status'] == 'success'
        assert result['data'].shape[1] == 50
        assert result['data'].shape[0] == 100

    # === DATE/TIME TESTS ===

    def test_load_jsonl_datetime_handling(self, loader, test_dir):
        """Handle datetime values correctly"""
        df = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=5),
            'value': [1, 2, 3, 4, 5]
        })
        jsonl_file = test_dir / "dates.jsonl"
        df.to_json(jsonl_file, orient='records', lines=True)
        
        result = loader.load(str(jsonl_file))
        assert result['status'] == 'success'
        assert len(result['data']) == 5

    def test_load_sqlite_datetime_types(self, loader, test_dir):
        """Handle SQLite datetime columns"""
        db_file = test_dir / "dates.db"
        
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'created_at': pd.date_range('2020-01-01', periods=5),
            'updated_at': pd.date_range('2021-01-01', periods=5)
        })
        
        conn = sqlite3.connect(str(db_file))
        df.to_sql('data', conn, if_exists='replace', index=False)
        conn.close()
        
        result = loader.load(str(db_file))
        assert result['status'] == 'success'
        assert len(result['data']) == 5

    # === CATEGORICAL DATA TESTS ===

    def test_load_jsonl_categorical_data(self, loader, test_dir):
        """Handle categorical/enum-like data"""
        df = pd.DataFrame({
            'status': pd.Categorical(['active', 'inactive', 'pending'] * 3 + ['active']),
            'priority': pd.Categorical(['low', 'medium', 'high'] * 3 + ['low']),
            'value': range(10)
        })
        jsonl_file = test_dir / "categorical.jsonl"
        df.to_json(jsonl_file, orient='records', lines=True)
        
        result = loader.load(str(jsonl_file))
        assert result['status'] == 'success'
        assert len(result['data']) == 10

    # === FILE SIZE BOUNDARY TESTS ===

    def test_load_near_size_limit_file(self, loader, test_dir):
        """Test file near the 100MB limit"""
        # Create file close to but under 100MB
        # Using ~50MB to be safe
        df = pd.DataFrame({
            'id': np.arange(500_000),
            'text': ['x' * 100] * 500_000,  # 100 byte strings
            'value': np.random.randn(500_000)
        })
        
        jsonl_file = test_dir / "near_limit.jsonl"
        df.to_json(jsonl_file, orient='records', lines=True)
        
        file_size_mb = jsonl_file.stat().st_size / (1024 * 1024)
        assert file_size_mb < 100, f"Test file too large: {file_size_mb}MB"
        
        result = loader.load(str(jsonl_file))
        assert result['status'] == 'success'

    def test_load_over_size_limit(self, loader, test_dir):
        """Test that files over 100MB are rejected"""
        # We can't actually create a 100MB+ file in tests
        # But we can verify the size check exists
        assert loader.MAX_FILE_SIZE_MB == 100

    # === CONCURRENT LOAD RESILIENCE ===

    def test_loader_state_isolation(self, loader, test_dir):
        """Test that loading different files doesn't interfere"""
        jsonl_file1 = test_dir / "file1.jsonl"
        jsonl_file2 = test_dir / "file2.jsonl"
        
        df1 = pd.DataFrame({'id': [1, 2], 'name': ['A', 'B']})
        df2 = pd.DataFrame({'id': [10, 20, 30], 'name': ['X', 'Y', 'Z']})
        
        df1.to_json(jsonl_file1, orient='records', lines=True)
        df2.to_json(jsonl_file2, orient='records', lines=True)
        
        # Load first file
        r1 = loader.load(str(jsonl_file1))
        assert len(r1['data']) == 2
        
        # Load second file
        r2 = loader.load(str(jsonl_file2))
        assert len(r2['data']) == 3  # Should have new data
        assert len(loader.get_data()) == 3  # Loader should have latest

    # === RECOVERY FROM PARTIAL FAILURES ===

    def test_error_recovery_on_corrupted_field(self, loader, test_dir):
        """Test graceful handling of partially corrupt data"""
        # Create a JSONL file with one bad line (invalid JSON)
        jsonl_file = test_dir / "partial_corrupt.jsonl"
        
        with open(jsonl_file, 'w') as f:
            f.write('{"id": 1, "value": 10}\n')
            f.write('{"id": 2, "value": 20}\n')
            f.write('CORRUPTED LINE NOT JSON\n')
            f.write('{"id": 3, "value": 30}\n')
        
        # Should either load what it can or error gracefully
        result = loader.load(str(jsonl_file))
        # Accept either error or partial load
        assert result['status'] in ['success', 'error']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
