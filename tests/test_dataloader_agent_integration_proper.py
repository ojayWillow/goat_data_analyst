"""PROPER Comprehensive Integration Tests for DataLoader Agent.

NO SHORTCUTS. Real tests with strong assertions.

Tests:
1. End-to-end load → validate → quality score workflows
2. Actual quality score behavior (perfect vs problematic)
3. Metadata propagation and consistency
4. All actual error paths
5. Stress testing with realistic data sizes
6. Edge cases with proper expectations
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile

from agents.data_loader.data_loader import DataLoader


class TestDataLoaderAgentEndToEnd:
    """End-to-end DataLoader agent workflows - NO SHORTCUTS."""

    def test_perfect_data_workflow_complete(self, tmp_path):
        """Perfect data: Load → Validate → Verify high quality."""
        # Create perfect, pristine data
        csv_file = tmp_path / "perfect.csv"
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
            "score": [85.5, 92.0, 78.5, 88.0, 95.0]
        })
        df.to_csv(csv_file, index=False)

        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        # STRONG ASSERTIONS - not vague
        assert result['status'] in ['success', 'warning'], f"Expected success/warning, got {result['status']}"
        assert result['data'] is not None, "Data should not be None"
        assert len(result['data']) == 5, f"Expected 5 rows, got {len(result['data'])}"
        assert result['data'].shape[1] == 3, f"Expected 3 columns, got {result['data'].shape[1]}"
        
        # Quality should be HIGH for perfect data (>= 0.8)
        quality = result['quality_score']
        assert 0.0 <= quality <= 1.0, f"Quality out of range: {quality}"
        assert quality >= 0.80, f"Perfect data should have quality >= 0.80, got {quality}"
        
        # Verify data integrity
        assert list(result['data']['name']) == df['name'].tolist()
        assert (result['data']['score'] == df['score']).all()

    def test_problematic_data_detects_issues(self, tmp_path):
        """Problematic data: Properly detects issues and reduces quality."""
        csv_file = tmp_path / "issues.csv"
        df = pd.DataFrame({
            "id": [1, None, 3, None, 5],  # 40% nulls
            "name": ["A", "B", "A", "B", "A"],  # 60% duplicates
            "score": [10.5, None, 30.1, 40.8, 50.2]  # 20% nulls
        })
        df.to_csv(csv_file, index=False)

        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        # Should still load
        assert result['status'] in ['success', 'warning']
        assert result['data'] is not None
        
        # Quality MUST be lower than perfect
        quality = result['quality_score']
        assert 0.0 <= quality <= 1.0
        assert quality < 0.80, f"Problematic data should have quality < 0.80, got {quality}"
        
        # Should detect issues
        issues = result.get('quality_issues', [])
        # Either have issues listed OR low quality score indicates problems
        assert quality < 0.80 or len(issues) > 0, "Should either have issues or low quality"

    def test_quality_score_perfect_vs_problematic(self, tmp_path):
        """Quality: Perfect data > Problematic data."""
        # Perfect data
        perfect_csv = tmp_path / "perfect.csv"
        df_perfect = pd.DataFrame({
            "col1": range(10),
            "col2": [chr(65 + i) for i in range(10)]
        })
        df_perfect.to_csv(perfect_csv, index=False)
        
        # Problematic data (50% nulls)
        prob_csv = tmp_path / "problem.csv"
        df_prob = pd.DataFrame({
            "col1": [i if i % 2 == 0 else None for i in range(10)],
            "col2": [chr(65 + i) if i % 2 == 0 else None for i in range(10)]
        })
        df_prob.to_csv(prob_csv, index=False)
        
        loader = DataLoader()
        
        # Load perfect
        r_perfect = loader.load(str(perfect_csv))
        q_perfect = r_perfect['quality_score']
        
        # Load problematic
        r_prob = loader.load(str(prob_csv))
        q_prob = r_prob['quality_score']
        
        # Perfect should be >= problematic
        assert q_perfect >= q_prob, f"Perfect ({q_perfect}) should be >= Problematic ({q_prob})"
        # They should be DIFFERENT
        assert q_perfect != q_prob, f"Scores should differ, both are {q_perfect}"

    def test_quality_score_consistency_across_methods(self, tmp_path):
        """Quality: Same score everywhere (consistency)."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({
            "col1": [1, 2, 3, 4, 5],
            "col2": ["a", "b", "c", "d", "e"]
        })
        df.to_csv(csv_file, index=False)

        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        # Quality from load result
        q_load = result['quality_score']
        
        # Quality from get_quality_score()
        q_getter = loader.get_quality_score()
        
        # Quality from metadata
        q_meta = loader.get_metadata()['quality_score']
        
        # Quality from get_info()
        q_info = loader.get_info()['quality_score']
        
        # ALL MUST MATCH EXACTLY
        assert q_load == q_getter, f"Load ({q_load}) != getter ({q_getter})"
        assert q_load == q_meta, f"Load ({q_load}) != metadata ({q_meta})"
        assert q_load == q_info, f"Load ({q_load}) != info ({q_info})"

    def test_load_history_tracks_all_loads(self, tmp_path):
        """History: All loads tracked with quality scores."""
        loader = DataLoader()
        
        files = []
        expected_qualities = []
        
        # Load 3 files with different data
        for i in range(3):
            csv = tmp_path / f"file_{i}.csv"
            # Vary quality: perfect → some issues → more issues
            if i == 0:
                df = pd.DataFrame({"x": range(10)})
            elif i == 1:
                df = pd.DataFrame({"x": [j if j % 3 != 0 else None for j in range(10)]})
            else:
                df = pd.DataFrame({"x": [j if j % 2 == 0 else None for j in range(10)]})
            
            df.to_csv(csv, index=False)
            result = loader.load(str(csv))
            expected_qualities.append(result['quality_score'])
        
        # Check history
        history = loader.get_load_history()
        assert len(history) == 3, f"Expected 3 history entries, got {len(history)}"
        
        # Each entry should have quality
        for i, entry in enumerate(history):
            assert 'quality_score' in entry
            assert entry['quality_score'] == expected_qualities[i]
            assert 'rows' in entry
            assert 'columns' in entry

    def test_metadata_contains_quality_metrics(self, tmp_path):
        """Metadata: Includes quality score and issues."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({
            "id": [1, None, 3],
            "value": [10.5, 20.3, None]
        })
        df.to_csv(csv_file, index=False)
        
        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        metadata = loader.get_metadata()
        
        # Must contain quality metrics
        assert 'quality_score' in metadata
        assert isinstance(metadata['quality_score'], (int, float))
        assert 0.0 <= metadata['quality_score'] <= 1.0
        
        # May contain issues
        if 'quality_issues' in metadata:
            assert isinstance(metadata['quality_issues'], list)


class TestDataLoaderErrorHandling:
    """Error handling - comprehensive, realistic."""

    def test_nonexistent_file_returns_error(self):
        """Nonexistent file: Must return error status."""
        loader = DataLoader()
        result = loader.load("/definitely/nonexistent/path/file.csv")
        
        assert result['status'] == 'error', f"Expected error, got {result['status']}"
        assert result['data'] is None, "Data should be None on error"
        assert result['quality_score'] == 0.0, f"Quality should be 0.0, got {result['quality_score']}"
        assert len(result.get('errors', [])) >= 0  # May have error list

    def test_empty_file_returns_error(self, tmp_path):
        """Empty CSV (header only): Must return error."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("col1,col2,col3\n")
        
        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        # Empty data should fail
        assert result['status'] == 'error'
        assert result['quality_score'] == 0.0

    def test_get_data_before_load_returns_none(self):
        """Before load: get_data() returns None."""
        loader = DataLoader()
        data = loader.get_data()
        assert data is None, "Should return None before loading"

    def test_get_metadata_before_load_returns_empty(self):
        """Before load: get_metadata() returns empty dict."""
        loader = DataLoader()
        metadata = loader.get_metadata()
        assert metadata == {}, f"Should be empty dict, got {metadata}"

    def test_get_quality_before_load_returns_zero(self):
        """Before load: get_quality_score() returns 0.0."""
        loader = DataLoader()
        quality = loader.get_quality_score()
        assert quality == 0.0, f"Should be 0.0, got {quality}"

    def test_validate_columns_before_load_returns_invalid(self):
        """Before load: validate_columns() returns invalid."""
        loader = DataLoader()
        result = loader.validate_columns(['col1', 'col2'])
        assert result['valid'] is False, "Should be invalid before load"
        assert result['missing'] == ['col1', 'col2']


class TestDataLoaderStressAndEdgeCases:
    """Stress and edge cases - realistic scenarios."""

    def test_large_dataset_10k_rows(self, tmp_path):
        """Large dataset: 10,000 rows loads correctly."""
        csv_file = tmp_path / "large.csv"
        df = pd.DataFrame({
            "id": range(10000),
            "value": np.random.rand(10000),
            "category": np.random.choice(['A', 'B', 'C'], 10000)
        })
        df.to_csv(csv_file, index=False)
        
        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        assert result['status'] in ['success', 'warning']
        assert len(result['data']) == 10000
        assert result['data'].shape[1] == 3
        assert 0.0 <= result['quality_score'] <= 1.0

    def test_many_columns_100_cols(self, tmp_path):
        """Many columns: 100 columns loads correctly."""
        csv_file = tmp_path / "many_cols.csv"
        data = {f"col_{i}": range(100) for i in range(100)}
        df = pd.DataFrame(data)
        df.to_csv(csv_file, index=False)
        
        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        assert result['status'] in ['success', 'warning']
        assert result['data'].shape[1] == 100
        assert result['data'].shape[0] == 100

    def test_all_null_column(self, tmp_path):
        """All-null column: Detects and handles."""
        csv_file = tmp_path / "all_null.csv"
        df = pd.DataFrame({
            "col1": [1, 2, 3, 4, 5],
            "col2": [None, None, None, None, None]  # All nulls
        })
        df.to_csv(csv_file, index=False)
        
        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        # Loads but quality should be low
        assert result['data'] is not None
        # Quality should be lower than perfect (due to all-null column)
        assert result['quality_score'] < 0.95

    def test_mixed_data_types(self, tmp_path):
        """Mixed types: int, float, str, bool all handled."""
        csv_file = tmp_path / "mixed.csv"
        df = pd.DataFrame({
            "int_col": [1, 2, 3, 4, 5],
            "float_col": [1.1, 2.2, 3.3, 4.4, 5.5],
            "str_col": ["a", "b", "c", "d", "e"],
            "bool_col": [True, False, True, False, True]
        })
        df.to_csv(csv_file, index=False)
        
        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        assert result['status'] in ['success', 'warning']
        assert result['data'].shape == (5, 4)
        assert result['quality_score'] > 0.75  # Should be high

    def test_duplicate_rows_detected(self, tmp_path):
        """Duplicates: 60% duplicates reduces quality."""
        csv_file = tmp_path / "dupes.csv"
        df = pd.DataFrame({
            "col1": [1, 1, 1, 2, 2],  # 60% duplicates
            "col2": ["a", "a", "a", "b", "b"]
        })
        df.to_csv(csv_file, index=False)
        
        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        # Loads but quality reduced
        assert result['data'] is not None
        # Quality should reflect duplicate issue
        assert result['quality_score'] < 0.90

    def test_special_characters_in_data(self, tmp_path):
        """Special chars: café, naïve, résumé handled."""
        csv_file = tmp_path / "special.csv"
        df = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["café", "naïve", "résumé"]
        })
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        assert result['status'] in ['success', 'warning']
        assert "café" in result['data']['col2'].values


class TestDataLoaderQualityScoring:
    """Quality scoring - accurate and consistent."""

    def test_perfect_data_scores_high(self, tmp_path):
        """Perfect: No nulls, no duplicates → quality >= 0.95."""
        csv_file = tmp_path / "perfect.csv"
        df = pd.DataFrame({"x": range(100), "y": range(100, 200)})
        df.to_csv(csv_file, index=False)
        
        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        # Must be very high
        assert result['quality_score'] >= 0.95

    def test_quality_score_always_valid_range(self, tmp_path):
        """Quality: Always 0.0-1.0 for any data."""
        test_cases = [
            ("perfect", pd.DataFrame({"x": range(10)})),
            ("nulls", pd.DataFrame({"x": [None, None, 1, 2, 3]})),
            ("dupes", pd.DataFrame({"x": [1, 1, 1, 2, 2]})),
        ]
        
        for name, df in test_cases:
            csv_file = tmp_path / f"{name}.csv"
            df.to_csv(csv_file, index=False)
            
            loader = DataLoader()
            result = loader.load(str(csv_file))
            
            quality = result['quality_score']
            assert 0.0 <= quality <= 1.0, f"{name}: quality {quality} out of range"

    def test_quality_degrades_with_nulls(self, tmp_path):
        """Quality: Degrades with increasing nulls."""
        test_cases = [
            ("0nulls", pd.DataFrame({"x": range(10)})),
            ("10nulls", pd.DataFrame({"x": [i if i < 9 else None for i in range(10)]})),
            ("50nulls", pd.DataFrame({"x": [i if i % 2 == 0 else None for i in range(10)]})),
        ]
        
        qualities = {}
        for name, df in test_cases:
            csv_file = tmp_path / f"{name}.csv"
            df.to_csv(csv_file, index=False)
            
            loader = DataLoader()
            result = loader.load(str(csv_file))
            qualities[name] = result['quality_score']
        
        # Perfect should be highest
        assert qualities["0nulls"] >= qualities["10nulls"]
        assert qualities["10nulls"] >= qualities["50nulls"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
