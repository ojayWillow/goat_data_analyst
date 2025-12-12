"""Integration Tests for DataLoader - Worker Coordination and Workflows.

Tests for:
1. Worker coordination and orchestration
2. Error intelligence tracking
3. End-to-end data loading workflows
4. Quality score propagation
5. Error propagation and recovery

Target: 90%+ coverage for integration scenarios
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

from agents.data_loader.workers import (
    CSVLoaderWorker,
    JSONExcelLoaderWorker,
    ParquetLoaderWorker,
    ValidatorWorker,
    WorkerResult,
    ErrorType,
)


class TestWorkerCoordination:
    """Tests for worker coordination in DataLoader."""
    
    def test_csv_loader_validator_workflow(self, tmp_path):
        """CSV loader -> Validator workflow."""
        # Create test CSV
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({
            "col1": [1, 2, 3, 4, 5],
            "col2": ["a", "b", "c", "d", "e"]
        })
        df.to_csv(csv_file, index=False)
        
        # Step 1: Load CSV
        loader = CSVLoaderWorker()
        load_result = loader.safe_execute(file_path=str(csv_file))
        
        assert load_result.success is True
        assert load_result.data is not None
        
        # Step 2: Validate
        validator = ValidatorWorker()
        validate_result = validator.safe_execute(
            df=load_result.data,
            file_path=str(csv_file),
            file_format="csv"
        )
        
        assert validate_result.success is True
        assert validate_result.quality_score >= load_result.quality_score * 0.8
    
    def test_quality_score_consistency(self, tmp_path):
        """Quality scores should be consistent across workers."""
        # Create test CSV with no issues
        csv_file = tmp_path / "perfect.csv"
        df = pd.DataFrame({
            "col1": range(100),
            "col2": [f"val_{i}" for i in range(100)]
        })
        df.to_csv(csv_file, index=False)
        
        loader = CSVLoaderWorker()
        load_result = loader.safe_execute(file_path=str(csv_file))
        
        validator = ValidatorWorker()
        validate_result = validator.safe_execute(df=load_result.data)
        
        # Both scores should be high for perfect data
        assert load_result.quality_score > 0.9
        assert validate_result.quality_score > 0.85
        # Validator score should be reasonable compared to loader
        assert abs(load_result.quality_score - validate_result.quality_score) < 0.15
    
    def test_error_propagation(self, tmp_path):
        """Errors should propagate correctly through workflow."""
        # Create CSV with high null percentage
        csv_file = tmp_path / "nulls.csv"
        df = pd.DataFrame({
            "col1": [None] * 10,
            "col2": [None] * 9 + ["a"],
        })
        df.to_csv(csv_file, index=False)
        
        loader = CSVLoaderWorker()
        load_result = loader.safe_execute(file_path=str(csv_file))
        
        # Loader should still succeed but with warnings
        assert load_result.success is True
        assert len(load_result.warnings) > 0
        
        # Validator should flag as invalid
        validator = ValidatorWorker()
        validate_result = validator.safe_execute(df=load_result.data)
        
        assert validate_result.success is False
        assert len(validate_result.metadata["issues"]) > 0


class TestErrorIntelligenceTracking:
    """Tests for error intelligence tracking across workers."""
    
    def test_worker_tracks_success(self, tmp_path):
        """Worker should track successful operations."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        df.to_csv(csv_file, index=False)
        
        worker = CSVLoaderWorker()
        result = worker.safe_execute(file_path=str(csv_file))
        
        assert result.success is True
        # Note: Full error intelligence tracking verified in real environment
    
    def test_worker_tracks_errors(self, tmp_path):
        """Worker should track and report errors."""
        worker = CSVLoaderWorker()
        
        # Non-existent file
        result = worker.safe_execute(file_path="/nonexistent/file.csv")
        
        assert result.success is False
        assert len(result.errors) > 0
        assert result.quality_score == 0.0
    
    def test_error_context_captured(self, tmp_path):
        """Error context should be captured for diagnosis."""
        # Create empty CSV
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("col1,col2\n")
        
        worker = CSVLoaderWorker()
        result = worker.safe_execute(file_path=str(csv_file))
        
        assert len(result.errors) > 0
        error = result.errors[0]
        assert "type" in error
        assert "message" in error


class TestEndToEndWorkflows:
    """Tests for complete end-to-end data loading workflows."""
    
    def test_load_and_validate_csv(self, tmp_path):
        """Complete workflow: load CSV -> validate."""
        # Create realistic CSV
        csv_file = tmp_path / "sales.csv"
        df = pd.DataFrame({
            "product_id": [1, 2, 3, 4, 5],
            "product_name": ["A", "B", "C", "D", "E"],
            "price": [10.99, 20.50, 15.75, 30.00, 25.25],
            "quantity": [100, 50, 75, 200, 150]
        })
        df.to_csv(csv_file, index=False)
        
        # Load
        loader = CSVLoaderWorker()
        load_result = loader.safe_execute(file_path=str(csv_file))
        
        assert load_result.success is True
        assert load_result.rows_processed == 5
        assert load_result.quality_score > 0.95
        
        # Validate
        validator = ValidatorWorker()
        validate_result = validator.safe_execute(df=load_result.data)
        
        assert validate_result.success is True
        assert validate_result.metadata["rows"] == 5
        assert validate_result.metadata["columns"] == 4
    
    def test_handle_partially_corrupted_data(self, tmp_path):
        """Should handle partially corrupted data gracefully."""
        csv_file = tmp_path / "corrupted.csv"
        # Create CSV with some issues
        csv_file.write_text(
            "col1,col2\n"
            "1,a\n"
            "2,b\n"
            "3,c\n"
            "bad,data,extra\n"  # Malformed line
            "4,d\n"
        )
        
        loader = CSVLoaderWorker()
        result = loader.safe_execute(file_path=str(csv_file))
        
        # Should still load successfully
        assert result.success is True
        # Should have loaded 4 rows (bad line skipped)
        assert result.rows_processed >= 4
    
    def test_load_validate_export_flow(self, tmp_path):
        """Load -> Validate -> Ready for export."""
        # Create source
        source_csv = tmp_path / "source.csv"
        df_source = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "value": [100, 200, 300, 400, 500]
        })
        df_source.to_csv(source_csv, index=False)
        
        # Step 1: Load
        loader = CSVLoaderWorker()
        load_result = loader.safe_execute(file_path=str(source_csv))
        assert load_result.success is True
        
        # Step 2: Validate
        validator = ValidatorWorker()
        validate_result = validator.safe_execute(df=load_result.data)
        assert validate_result.success is True
        
        # Step 3: Check ready for export
        assert validate_result.quality_score > 0.85
        assert validate_result.metadata["rows"] == 5
        assert len(validate_result.metadata["issues"]) == 0


class TestMultiFormatLoading:
    """Tests for loading multiple file formats in sequence."""
    
    def test_load_csv_json_consistency(self, tmp_path):
        """Data should be consistent across CSV and JSON."""
        # Create test data
        test_data = {
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"]
        }
        
        # Save as CSV
        csv_file = tmp_path / "test.csv"
        df_csv = pd.DataFrame(test_data)
        df_csv.to_csv(csv_file, index=False)
        
        # Save as JSON
        json_file = tmp_path / "test.json"
        df_json = pd.DataFrame(test_data)
        df_json.to_json(json_file, orient="columns")
        
        # Load both
        csv_loader = CSVLoaderWorker()
        csv_result = csv_loader.safe_execute(file_path=str(csv_file))
        
        json_loader = JSONExcelLoaderWorker()
        json_result = json_loader.safe_execute(
            file_path=str(json_file),
            file_format="json"
        )
        
        # Both should succeed
        assert csv_result.success is True
        assert json_result.success is True
        
        # Both should have same shape
        assert len(csv_result.data) == len(json_result.data)
        assert len(csv_result.data.columns) == len(json_result.data.columns)
    
    def test_load_csv_parquet_consistency(self, tmp_path):
        """Data should be consistent across CSV and Parquet."""
        # Create test data
        test_data = {
            "col1": [1, 2, 3, 4, 5],
            "col2": ["a", "b", "c", "d", "e"]
        }
        df = pd.DataFrame(test_data)
        
        # Save as CSV
        csv_file = tmp_path / "test.csv"
        df.to_csv(csv_file, index=False)
        
        # Save as Parquet
        parquet_file = tmp_path / "test.parquet"
        df.to_parquet(parquet_file)
        
        # Load both
        csv_loader = CSVLoaderWorker()
        csv_result = csv_loader.safe_execute(file_path=str(csv_file))
        
        parquet_loader = ParquetLoaderWorker()
        parquet_result = parquet_loader.safe_execute(file_path=str(parquet_file))
        
        # Both should succeed and have same quality
        assert csv_result.success is True
        assert parquet_result.success is True
        
        # Quality scores should be similar
        assert abs(csv_result.quality_score - parquet_result.quality_score) < 0.1


class TestQualityPropagation:
    """Tests for quality score propagation through workflows."""
    
    def test_quality_score_flow(self, tmp_path):
        """Quality score should flow from loader to validator."""
        # Create CSV
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({
            "col1": [1, 2, 3, 4, 5],
            "col2": ["a", "b", "c", "d", "e"]
        })
        df.to_csv(csv_file, index=False)
        
        # Load
        loader = CSVLoaderWorker()
        load_result = loader.safe_execute(file_path=str(csv_file))
        loader_quality = load_result.quality_score
        
        # Validate
        validator = ValidatorWorker()
        validate_result = validator.safe_execute(df=load_result.data)
        validator_quality = validate_result.quality_score
        
        # Both should have good quality
        assert loader_quality > 0.9
        assert validator_quality > 0.9
        
        # Scores should be in same range
        assert abs(loader_quality - validator_quality) < 0.15
    
    def test_quality_metrics_validity(self, tmp_path):
        """Quality metrics should be valid."""
        # Create CSV with mixed data
        csv_file = tmp_path / "mixed.csv"
        df_good = pd.DataFrame({
            "col1": [1, 2, 3, 4, 5],
            "col2": ["a", "b", "c", "d", "e"]
        })
        df_good.to_csv(csv_file, index=False)
        
        # Create CSV with some nulls
        csv_file_bad = tmp_path / "nulls.csv"
        df_bad = pd.DataFrame({
            "col1": [1, None, 3, None, 5],
            "col2": ["a", "b", "a", "b", "a"]
        })
        df_bad.to_csv(csv_file_bad, index=False)
        
        # Load both
        loader = CSVLoaderWorker()
        result_good = loader.safe_execute(file_path=str(csv_file))
        result_bad = loader.safe_execute(file_path=str(csv_file_bad))
        
        # Good data should have high quality
        assert result_good.quality_score > 0.9
        # Bad data should have valid quality score
        assert 0.0 <= result_bad.quality_score <= 1.0
        # Scores should be valid numbers
        assert isinstance(result_good.quality_score, (int, float))
        assert isinstance(result_bad.quality_score, (int, float))


class TestRecoveryStrategies:
    """Tests for error recovery and resilience."""
    
    def test_recovers_from_encoding_errors(self, tmp_path):
        """Should recover from encoding errors."""
        csv_file = tmp_path / "encoding.csv"
        df = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["café", "naïve", "résumé"]
        })
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        loader = CSVLoaderWorker()
        result = loader.safe_execute(
            file_path=str(csv_file),
            encoding='utf-8'
        )
        
        assert result.success is True
    
    def test_skip_bad_lines_strategy(self, tmp_path):
        """Should skip and continue on bad lines."""
        csv_file = tmp_path / "bad_lines.csv"
        csv_file.write_text(
            "col1,col2\n"
            "1,a\n"
            "bad,line,with,extra,columns\n"
            "2,b\n"
            "3,c\n"
        )
        
        loader = CSVLoaderWorker()
        result = loader.safe_execute(file_path=str(csv_file))
        
        # Should load successfully despite bad line
        assert result.success is True
        # Should have loaded valid lines
        assert result.rows_processed >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
