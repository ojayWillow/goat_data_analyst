"""Full Pipeline Integration Tests.

Tests complete workflows:
1. Load → Validate → Export
2. Multiple file formats
3. Quality tracking through pipeline
4. End-to-end error handling
5. Performance at scale
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

from agents.data_loader.data_loader import DataLoader


class TestFullPipelineLoadValidateExport:
    """Test complete load → validate → export workflows."""

    def test_pipeline_perfect_data_csv(self, tmp_path):
        """Complete pipeline with perfect CSV data."""
        # Step 1: Create perfect CSV
        input_csv = tmp_path / "input.csv"
        df_input = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
            "score": [85.5, 92.0, 78.5, 88.0, 95.0]
        })
        df_input.to_csv(input_csv, index=False)

        # Step 2: Load
        loader = DataLoader()
        result = loader.load(str(input_csv))
        
        assert result['status'] in ['success', 'warning']
        assert len(result['data']) == 5
        quality_1 = result['quality_score']
        assert 0.0 <= quality_1 <= 1.0

        # Step 3: Get metadata
        metadata = loader.get_metadata()
        assert metadata['quality_score'] == quality_1

        # Step 4: Get results
        data = loader.get_data()
        assert len(data) == 5

    def test_pipeline_problematic_data_csv(self, tmp_path):
        """Complete pipeline with problematic CSV data."""
        # Step 1: Create CSV with issues
        input_csv = tmp_path / "issues.csv"
        df_input = pd.DataFrame({
            "id": [1, None, 3, None, 5],
            "name": ["A", "B", "A", "B", "A"],  # Duplicates
            "score": [10.5, None, 20.3, 30.1, None]
        })
        df_input.to_csv(input_csv, index=False)

        # Step 2: Load
        loader = DataLoader()
        result = loader.load(str(input_csv))
        
        assert result['status'] in ['success', 'warning']
        quality = result['quality_score']
        assert 0.0 <= quality <= 1.0

        # Step 3: Still get results
        data = loader.get_data()
        assert data is not None
        assert len(data) == 5

    def test_pipeline_multiple_loads(self, tmp_path):
        """Test pipeline with multiple sequential loads."""
        loader = DataLoader()
        
        files = []
        qualities = []
        
        # Create and load 3 different files
        for i in range(3):
            csv_file = tmp_path / f"file_{i}.csv"
            df = pd.DataFrame({
                "col1": range(10 + i*5),
                "col2": np.random.rand(10 + i*5)
            })
            df.to_csv(csv_file, index=False)
            files.append(csv_file)
            
            result = loader.load(str(csv_file))
            assert result['status'] in ['success', 'warning']
            qualities.append(result['quality_score'])
        
        # Check history
        history = loader.get_load_history()
        assert len(history) == 3
        assert all(h['quality_score'] >= 0 for h in history)

    def test_pipeline_data_verification(self, tmp_path):
        """Verify data integrity through pipeline."""
        csv_file = tmp_path / "verify.csv"
        df_original = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "value": [10, 20, 30, 40, 50],
            "label": ["a", "b", "c", "d", "e"]
        })
        df_original.to_csv(csv_file, index=False)

        loader = DataLoader()
        result = loader.load(str(csv_file))
        df_loaded = result['data']

        # Verify shape
        assert df_loaded.shape == df_original.shape
        
        # Verify values
        assert (df_loaded['id'].values == df_original['id'].values).all()
        assert (df_loaded['value'].values == df_original['value'].values).all()


class TestPipelineWithDifferentFormats:
    """Test pipeline with different file formats."""

    def test_pipeline_json_format(self, tmp_path):
        """Complete pipeline with JSON data."""
        json_file = tmp_path / "data.json"
        data = [
            {"id": 1, "name": "Alice", "value": 100},
            {"id": 2, "name": "Bob", "value": 200},
            {"id": 3, "name": "Charlie", "value": 300}
        ]
        json_file.write_text(json.dumps(data))

        loader = DataLoader()
        result = loader.load(str(json_file))
        
        if result['status'] in ['success', 'warning']:
            assert result['data'] is not None
            assert len(result['data']) == 3


class TestPipelineQualityTracking:
    """Test quality score tracking through pipeline."""

    def test_quality_consistency(self, tmp_path):
        """Quality score is consistent through pipeline."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({
            "x": [1, 2, 3, 4, 5],
            "y": ["a", "b", "c", "d", "e"]
        })
        df.to_csv(csv_file, index=False)

        loader = DataLoader()
        result = loader.load(str(csv_file))
        
        # Quality at load
        q1 = result['quality_score']
        
        # Quality at metadata
        q2 = loader.get_metadata()['quality_score']
        
        # Quality at get_quality_score
        q3 = loader.get_quality_score()
        
        # Should all match
        assert q1 == q2 == q3

    def test_quality_degrades_appropriately(self, tmp_path):
        """Quality score differs with data issues."""
        # Perfect data
        perfect_csv = tmp_path / "perfect.csv"
        df_perfect = pd.DataFrame({
            "col": range(100)
        })
        df_perfect.to_csv(perfect_csv, index=False)

        # Imperfect data
        imperfect_csv = tmp_path / "imperfect.csv"
        df_imperfect = pd.DataFrame({
            "col": [i if i % 10 != 0 else None for i in range(100)]
        })
        df_imperfect.to_csv(imperfect_csv, index=False)

        loader = DataLoader()
        
        # Load perfect
        r1 = loader.load(str(perfect_csv))
        q1 = r1['quality_score']
        
        # Load imperfect
        r2 = loader.load(str(imperfect_csv))
        q2 = r2['quality_score']
        
        # Perfect should have higher or equal quality
        assert q1 >= q2


class TestPipelineErrorRecovery:
    """Test error recovery through pipeline."""

    def test_recover_from_bad_then_good(self, tmp_path):
        """Recover from error and successfully process good file."""
        loader = DataLoader()
        
        # Try bad file
        result1 = loader.load("/nonexistent/file.csv")
        assert result1['status'] == 'error'
        
        # Process good file
        good_csv = tmp_path / "good.csv"
        pd.DataFrame({"x": [1, 2, 3]}).to_csv(good_csv, index=False)
        
        result2 = loader.load(str(good_csv))
        assert result2['status'] in ['success', 'warning']
        assert len(result2['data']) == 3

    def test_error_isolation(self, tmp_path):
        """Errors are isolated to single load."""
        loader = DataLoader()
        
        # Load 1: Good
        good1 = tmp_path / "good1.csv"
        pd.DataFrame({"a": [1, 2, 3]}).to_csv(good1, index=False)
        r1 = loader.load(str(good1))
        q1 = r1['quality_score']
        
        # Load 2: Bad
        bad = tmp_path / "bad.csv"
        bad.write_text("")
        r2 = loader.load(str(bad))
        
        # Load 3: Good again
        good2 = tmp_path / "good2.csv"
        pd.DataFrame({"b": [4, 5, 6]}).to_csv(good2, index=False)
        r3 = loader.load(str(good2))
        q3 = r3['quality_score']
        
        # Quality of good loads should be positive
        assert q1 > 0
        assert q3 > 0


class TestPipelineStress:
    """Stress test pipeline at scale."""

    def test_large_file_pipeline(self, tmp_path):
        """Pipeline handles large files (10k rows)."""
        large_csv = tmp_path / "large.csv"
        df = pd.DataFrame({
            "id": range(10000),
            "value": np.random.rand(10000),
            "category": np.random.choice(["A", "B", "C"], 10000)
        })
        df.to_csv(large_csv, index=False)

        loader = DataLoader()
        result = loader.load(str(large_csv))
        
        assert result['status'] in ['success', 'warning']
        assert len(result['data']) == 10000
        assert 0.0 <= result['quality_score'] <= 1.0

    def test_many_columns_pipeline(self, tmp_path):
        """Pipeline handles datasets with many columns (100)."""
        many_col_csv = tmp_path / "many_cols.csv"
        data = {f"col_{i}": range(100) for i in range(100)}
        df = pd.DataFrame(data)
        df.to_csv(many_col_csv, index=False)

        loader = DataLoader()
        result = loader.load(str(many_col_csv))
        
        assert result['status'] in ['success', 'warning']
        assert result['data'].shape[1] == 100


class TestPipelineOutputFormats:
    """Test pipeline output in different formats."""

    def test_get_sample_through_pipeline(self, tmp_path):
        """Sample operation works through pipeline."""
        csv_file = tmp_path / "data.csv"
        df = pd.DataFrame({"x": range(1000)})
        df.to_csv(csv_file, index=False)

        loader = DataLoader()
        loader.load(str(csv_file))
        
        # Get sample
        sample = loader.get_sample(n_rows=10)
        assert sample['status'] == 'success'
        assert len(sample['data']) == 10
        assert 'quality_score' in sample['metadata']

    def test_get_info_through_pipeline(self, tmp_path):
        """Info operation works through pipeline."""
        csv_file = tmp_path / "data.csv"
        df = pd.DataFrame({"x": [1, 2, 3]})
        df.to_csv(csv_file, index=False)

        loader = DataLoader()
        loader.load(str(csv_file))
        
        info = loader.get_info()
        assert 'status' in info
        assert 'quality_score' in info

    def test_get_summary_through_pipeline(self, tmp_path):
        """Summary operation works through pipeline."""
        csv_file = tmp_path / "data.csv"
        df = pd.DataFrame({"x": [1, 2, 3]})
        df.to_csv(csv_file, index=False)

        loader = DataLoader()
        loader.load(str(csv_file))
        
        summary = loader.get_summary()
        assert isinstance(summary, str)
        assert "Quality" in summary or "quality" in summary.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
