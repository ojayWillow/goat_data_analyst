"""Comprehensive Integration Tests for DataLoader Agent.

Tests:
1. End-to-end load → validate → quality score workflows
2. Quality score tracking through pipeline
3. Metadata propagation
4. All error paths and recovery
5. Stress testing with various data sizes
6. Edge case handling
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile

from agents.data_loader.data_loader import DataLoader


class TestDataLoaderAgentEndToEnd:
    """End-to-end DataLoader agent workflows."""

    def test_complete_workflow_perfect_data(self, tmp_path):
        """Complete workflow: Load → Validate → Export with perfect data."""
        # Create perfect CSV
        csv_file = tmp_path / "perfect.csv"
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "name": ["A", "B", "C", "D", "E"],
            "value": [10.5, 20.3, 30.1, 40.8, 50.2]
        })
        df.to_csv(csv_file, index=False)

        # Initialize agent
        loader = DataLoader()

        # Step 1: Load
        result = loader.load(str(csv_file))
        assert result['status'] == 'success'
        assert result['data'] is not None
        assert len(result['data']) == 5

        # Step 2: Check quality score
        quality = result['quality_score']
        assert 0.9 <= quality <= 1.0, f"Expected quality >= 0.9, got {quality}"

        # Step 3: Get data
        data = loader.get_data()
        assert data is not None
        assert len(data) == 5

        # Step 4: Get metadata
        metadata = loader.get_metadata()
        assert metadata['rows'] == 5
        assert metadata['columns'] == 3
        assert metadata['quality_score'] == quality

        # Step 5: Get quality score
        stored_quality = loader.get_quality_score()
        assert stored_quality == quality

    def test_complete_workflow_with_issues(self, tmp_path):
        """Complete workflow with data quality issues."""
        # Create CSV with issues
        csv_file = tmp_path / "issues.csv"
        df = pd.DataFrame({
            "id": [1, None, 3, None, 5],
            "name": ["A", "B", "A", "B", "A"],  # Duplicates
            "value": [10.5, None, 30.1, 40.8, 50.2]
        })
        df.to_csv(csv_file, index=False)

        loader = DataLoader()
        result = loader.load(str(csv_file))

        # Should still succeed but with lower quality
        assert result['status'] in ['success', 'warning']
        quality = result['quality_score']
        assert 0.0 <= quality < 1.0, f"Expected quality < 1.0, got {quality}"
        
        # Should detect issues
        issues = result.get('quality_issues', [])
        # Issues should be detected or quality should be low
        assert quality < 0.95 or len(issues) > 0

    def test_quality_score_propagation(self, tmp_path):
        """Quality score propagates correctly through pipeline."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({
            "col1": [1, 2, 3, 4, 5],
            "col2": ["a", "b", "c", "d", "e"]
        })
        df.to_csv(csv_file, index=False)

        loader = DataLoader()
        result = loader.load(str(csv_file))

        # Quality in result
        result_quality = result['quality_score']
        
        # Quality in agent
        agent_quality = loader.get_quality_score()
        
        # Quality in metadata
        metadata_quality = loader.get_metadata()['quality_score']

        # All should match
        assert result_quality == agent_quality == metadata_quality

    def test_load_history_tracking(self, tmp_path):
        """Load history is tracked correctly."""
        loader = DataLoader()
        
        # Load first file
        csv1 = tmp_path / "file1.csv"
        df1 = pd.DataFrame({"a": [1, 2, 3]})
        df1.to_csv(csv1, index=False)
        loader.load(str(csv1))

        # Load second file
        csv2 = tmp_path / "file2.csv"
        df2 = pd.DataFrame({"b": [4, 5, 6]})
        df2.to_csv(csv2, index=False)
        loader.load(str(csv2))

        # Check history
        history = loader.get_load_history()
        assert len(history) == 2
        assert history[0]['file_path'] == str(csv1)
        assert history[1]['file_path'] == str(csv2)
        assert all('quality_score' in h for h in history)

    def test_get_info_with_quality(self, tmp_path):
        """get_info() includes quality score."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({"x": [1, 2, 3]})
        df.to_csv(csv_file, index=False)

        loader = DataLoader()
        loader.load(str(csv_file))

        info = loader.get_info()
        assert info['status'] == 'success'
        assert 'quality_score' in info
        assert 0.0 <= info['quality_score'] <= 1.0

    def test_get_sample_with_quality(self, tmp_path):
        """get_sample() includes quality score."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({"x": range(100)})
        df.to_csv(csv_file, index=False)

        loader = DataLoader()
        loader.load(str(csv_file))

        sample = loader.get_sample(n_rows=5)
        assert sample['status'] == 'success'
        assert len(sample['data']) == 5
        assert 'quality_score' in sample['metadata']

    def test_get_summary_with_quality(self, tmp_path):
        """get_summary() includes quality metrics."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({"x": [1, 2, 3]})
        df.to_csv(csv_file, index=False)

        loader = DataLoader()
        loader.load(str(csv_file))

        summary = loader.get_summary()
        assert 'Quality Score' in summary
        assert 'Quality Issues' in summary


class TestDataLoaderErrorPaths:
    """Test all error paths and recovery."""

    def test_nonexistent_file(self):
        """Handle non-existent file gracefully."""
        loader = DataLoader()
        result = loader.load("/nonexistent/file.csv")
        
        assert result['status'] == 'error'
        assert result['data'] is None
        assert result['quality_score'] == 0.0
        assert len(result['errors']) > 0

    def test_empty_csv(self, tmp_path):
        """Handle empty CSV gracefully."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("col1,col2\n")

        loader = DataLoader()
        result = loader.load(str(csv_file))

        assert result['status'] == 'error'
        assert result['quality_score'] == 0.0

    def test_malformed_csv(self, tmp_path):
        """Handle malformed CSV gracefully."""
        csv_file = tmp_path / "malformed.csv"
        csv_file.write_text("col1,col2\n1,a,extra\n2,b")

        loader = DataLoader()
        result = loader.load(str(csv_file))

        # Should handle gracefully with on_bad_lines='skip'
        assert result['status'] == 'success'
        assert result['data'] is not None

    def test_unsupported_format(self, tmp_path):
        """Handle unsupported format gracefully."""
        unsupported = tmp_path / "file.xyz"
        unsupported.write_text("data")

        loader = DataLoader()
        result = loader.load(str(unsupported))

        assert result['status'] == 'error'
        assert result['quality_score'] == 0.0

    def test_get_data_before_load(self):
        """get_data() returns None before loading."""
        loader = DataLoader()
        data = loader.get_data()
        assert data is None

    def test_get_metadata_before_load(self):
        """get_metadata() returns empty dict before loading."""
        loader = DataLoader()
        metadata = loader.get_metadata()
        assert metadata == {}

    def test_get_quality_before_load(self):
        """get_quality_score() returns 0.0 before loading."""
        loader = DataLoader()
        quality = loader.get_quality_score()
        assert quality == 0.0

    def test_validate_columns_before_load(self):
        """validate_columns() returns error before loading."""
        loader = DataLoader()
        result = loader.validate_columns(['col1', 'col2'])
        assert result['valid'] is False

    def test_get_summary_before_load(self):
        """get_summary() returns appropriate message before loading."""
        loader = DataLoader()
        summary = loader.get_summary()
        assert "No data loaded" in summary


class TestDataLoaderStressAndEdgeCases:
    """Stress tests and edge cases."""

    def test_large_dataset(self, tmp_path):
        """Handle large dataset (10000 rows)."""
        csv_file = tmp_path / "large.csv"
        df = pd.DataFrame({
            "id": range(10000),
            "value": np.random.rand(10000)
        })
        df.to_csv(csv_file, index=False)

        loader = DataLoader()
        result = loader.load(str(csv_file))

        assert result['status'] == 'success'
        assert len(result['data']) == 10000
        assert 0.0 <= result['quality_score'] <= 1.0

    def test_many_columns(self, tmp_path):
        """Handle dataset with many columns (100)."""
        csv_file = tmp_path / "many_cols.csv"
        data = {f"col{i}": range(100) for i in range(100)}
        df = pd.DataFrame(data)
        df.to_csv(csv_file, index=False)

        loader = DataLoader()
        result = loader.load(str(csv_file))

        assert result['status'] == 'success'
        assert result['data'].shape[1] == 100

    def test_all_null_column(self, tmp_path):
        """Handle column with all null values."""
        csv_file = tmp_path / "all_null.csv"
        df = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": [None, None, None]
        })
        df.to_csv(csv_file, index=False)

        loader = DataLoader()
        result = loader.load(str(csv_file))

        assert result['status'] in ['success', 'warning']
        assert result['quality_score'] < 1.0  # Should be lower

    def test_mixed_types(self, tmp_path):
        """Handle mixed data types."""
        csv_file = tmp_path / "mixed.csv"
        df = pd.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.1, 2.2, 3.3],
            "str_col": ["a", "b", "c"],
            "bool_col": [True, False, True]
        })
        df.to_csv(csv_file, index=False)

        loader = DataLoader()
        result = loader.load(str(csv_file))

        assert result['status'] == 'success'
        assert result['data'].shape[1] == 4

    def test_duplicate_rows(self, tmp_path):
        """Handle duplicate rows."""
        csv_file = tmp_path / "dupes.csv"
        df = pd.DataFrame({
            "col1": [1, 1, 2, 2, 3],
            "col2": ["a", "a", "b", "b", "c"]
        })
        df.to_csv(csv_file, index=False)

        loader = DataLoader()
        result = loader.load(str(csv_file))

        assert result['status'] == 'success'
        # Quality should detect duplicates
        issues = result.get('quality_issues', [])
        quality = result['quality_score']
        assert quality < 1.0 or len(issues) > 0

    def test_special_characters(self, tmp_path):
        """Handle special characters."""
        csv_file = tmp_path / "special.csv"
        df = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["café", "naïve", "résumé"]
        })
        df.to_csv(csv_file, index=False, encoding='utf-8')

        loader = DataLoader()
        result = loader.load(str(csv_file))

        assert result['status'] == 'success'
        assert "café" in result['data']['col2'].values

    def test_whitespace_handling(self, tmp_path):
        """Handle whitespace in data."""
        csv_file = tmp_path / "whitespace.csv"
        df = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": [" a ", "  b  ", " c"]
        })
        df.to_csv(csv_file, index=False)

        loader = DataLoader()
        result = loader.load(str(csv_file))

        assert result['status'] == 'success'

    def test_numeric_strings(self, tmp_path):
        """Handle numeric strings correctly."""
        csv_file = tmp_path / "num_str.csv"
        df = pd.DataFrame({
            "id": ["001", "002", "003"],
            "value": [1, 2, 3]
        })
        df.to_csv(csv_file, index=False)

        loader = DataLoader()
        result = loader.load(str(csv_file))

        assert result['status'] == 'success'
        assert result['data']['id'].dtype == 'object'  # Should stay as string


class TestDataLoaderQualityMetrics:
    """Advanced quality score verification."""

    def test_quality_score_range(self, tmp_path):
        """Quality score is always 0.0-1.0."""
        for _ in range(5):
            csv_file = tmp_path / f"test_{_}.csv"
            df = pd.DataFrame({
                "col1": np.random.rand(10),
                "col2": np.random.choice([None, 1, 2, 3], 10)
            })
            df.to_csv(csv_file, index=False)

            loader = DataLoader()
            result = loader.load(str(csv_file))

            quality = result['quality_score']
            assert 0.0 <= quality <= 1.0, f"Quality out of range: {quality}"

    def test_quality_degrades_with_issues(self, tmp_path):
        """Quality score decreases with more data issues."""
        # Perfect data
        csv_perfect = tmp_path / "perfect.csv"
        df_perfect = pd.DataFrame({
            "col1": [1, 2, 3, 4, 5],
            "col2": ["a", "b", "c", "d", "e"]
        })
        df_perfect.to_csv(csv_perfect, index=False)

        # Data with some nulls
        csv_nulls = tmp_path / "nulls.csv"
        df_nulls = pd.DataFrame({
            "col1": [1, None, 3, None, 5],
            "col2": ["a", "b", "c", "d", "e"]
        })
        df_nulls.to_csv(csv_nulls, index=False)

        loader = DataLoader()
        result_perfect = loader.load(str(csv_perfect))
        quality_perfect = result_perfect['quality_score']

        result_nulls = loader.load(str(csv_nulls))
        quality_nulls = result_nulls['quality_score']

        # Perfect should have higher quality
        assert quality_perfect > quality_nulls

    def test_quality_in_all_outputs(self, tmp_path):
        """Quality score present in all relevant outputs."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({"x": [1, 2, 3]})
        df.to_csv(csv_file, index=False)

        loader = DataLoader()
        result = loader.load(str(csv_file))

        # Check load result
        assert 'quality_score' in result

        # Check metadata
        metadata = loader.get_metadata()
        assert 'quality_score' in metadata

        # Check get_quality_score method
        quality = loader.get_quality_score()
        assert isinstance(quality, float)
        assert 0.0 <= quality <= 1.0

        # Check info
        info = loader.get_info()
        assert 'quality_score' in info


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
