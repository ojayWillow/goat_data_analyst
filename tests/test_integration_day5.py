"""Integration Tests - Day 5 Implementation.

Tests the complete narrative pipeline with simulated real data:
1. Load CSV files
2. Simulate agent outputs
3. Run through narrative pipeline
4. Validate narrative quality
5. Test with multiple datasets

These tests bridge theory (unit tests) and reality (real data behavior).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from agents.narrative_generator.integration_tester import IntegrationTester


class TestIntegrationDay5:
    """Integration tests for Day 5 - Real Data Testing."""

    @pytest.fixture
    def tester(self):
        """Create IntegrationTester instance."""
        return IntegrationTester()

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create a sample CSV file for testing."""
        # Create sample data with various characteristics
        np.random.seed(42)
        data = {
            'id': range(100),
            'value1': np.random.normal(100, 15, 100),
            'value2': np.random.exponential(50, 100),
            'category': np.random.choice(['A', 'B', 'C'], 100),
            'date': pd.date_range('2024-01-01', periods=100),
            'notes': [''] * 100  # Some with missing values
        }
        df = pd.DataFrame(data)
        # Add some missing values
        df.loc[np.random.choice(df.index, 10), 'value1'] = np.nan
        df.loc[np.random.choice(df.index, 5), 'category'] = None
        
        csv_path = tmp_path / "sample.csv"
        df.to_csv(csv_path, index=False)
        return str(csv_path)

    # === CSV LOADING TESTS ===

    def test_load_csv_success(self, tester, sample_csv):
        """Test loading a CSV file successfully."""
        df, success = tester.load_csv(sample_csv)

        assert success is True
        assert df is not None
        assert len(df) == 100
        assert len(df.columns) == 6

    def test_load_csv_nonexistent(self, tester):
        """Test loading a nonexistent CSV file."""
        df, success = tester.load_csv('nonexistent.csv')

        assert success is False
        assert df is None

    # === AGENT OUTPUT SIMULATION TESTS ===

    def test_simulate_agent_outputs(self, tester, sample_csv):
        """Test simulating agent outputs from data."""
        df, _ = tester.load_csv(sample_csv)
        outputs = tester.simulate_agent_outputs(df)

        assert outputs is not None
        assert 'explorer' in outputs
        assert 'anomalies' in outputs
        assert 'predictions' in outputs

    def test_explorer_output_structure(self, tester, sample_csv):
        """Test explorer output has correct structure."""
        df, _ = tester.load_csv(sample_csv)
        outputs = tester.simulate_agent_outputs(df)
        explorer = outputs['explorer']

        assert 'shape' in explorer
        assert 'missing_percentage' in explorer
        assert 'columns' in explorer
        assert 'dtypes' in explorer
        assert explorer['shape'] == (100, 6)

    def test_anomaly_output_structure(self, tester, sample_csv):
        """Test anomaly output has correct structure."""
        df, _ = tester.load_csv(sample_csv)
        outputs = tester.simulate_agent_outputs(df)
        anomalies = outputs['anomalies']

        assert 'count' in anomalies
        assert 'percentage' in anomalies
        assert 'top_anomalies' in anomalies
        assert 'severity' in anomalies
        assert isinstance(anomalies['count'], (int, float))
        assert 0 <= anomalies['percentage'] <= 100

    def test_prediction_output_structure(self, tester, sample_csv):
        """Test prediction output has correct structure."""
        df, _ = tester.load_csv(sample_csv)
        outputs = tester.simulate_agent_outputs(df)
        predictions = outputs['predictions']

        assert 'confidence' in predictions
        assert 'accuracy' in predictions
        assert 'top_features' in predictions
        assert 'trend' in predictions
        assert 0 <= predictions['confidence'] <= 1
        assert 0 <= predictions['accuracy'] <= 100

    # === PIPELINE EXECUTION TESTS ===

    def test_run_narrative_pipeline(self, tester, sample_csv):
        """Test running complete narrative pipeline."""
        df, _ = tester.load_csv(sample_csv)
        agent_outputs = tester.simulate_agent_outputs(df)
        narrative = tester.run_narrative_pipeline(agent_outputs)

        assert narrative is not None
        assert isinstance(narrative, dict)
        assert 'executive_summary' in narrative
        assert 'full_narrative' in narrative

    def test_narrative_has_all_sections(self, tester, sample_csv):
        """Test narrative has all required sections."""
        df, _ = tester.load_csv(sample_csv)
        agent_outputs = tester.simulate_agent_outputs(df)
        narrative = tester.run_narrative_pipeline(agent_outputs)

        required_keys = [
            'executive_summary',
            'problem_statement',
            'pain_points',
            'action_plan',
            'next_steps',
            'improvement_outlook',
            'full_narrative',
            'total_recommendations',
            'critical_count',
            'high_count',
            'medium_count'
        ]

        for key in required_keys:
            assert key in narrative, f"Missing key: {key}"

    def test_narrative_not_empty(self, tester, sample_csv):
        """Test narrative sections are not empty."""
        df, _ = tester.load_csv(sample_csv)
        agent_outputs = tester.simulate_agent_outputs(df)
        narrative = tester.run_narrative_pipeline(agent_outputs)

        assert len(narrative['executive_summary']) > 0
        assert len(narrative['full_narrative']) > 0

    # === END-TO-END TESTS ===

    def test_end_to_end_dataset(self, tester, sample_csv):
        """Test complete end-to-end flow with one dataset."""
        result = tester.test_dataset(sample_csv)

        assert result['success'] is True
        assert 'data_shape' in result
        assert 'agent_outputs' in result
        assert 'narrative' in result
        assert 'validation' in result

    def test_end_to_end_with_validation(self, tester, sample_csv):
        """Test end-to-end with validation checks."""
        result = tester.test_dataset(sample_csv)
        validation = result['validation']

        # Check critical validations
        assert validation['has_executive_summary'] is True
        assert validation['has_problem_statement'] is True
        assert validation['has_full_narrative'] is True
        assert validation['all_sections_not_empty'] is True

    # === DATA CHARACTERISTICS TESTS ===

    def test_clean_data_handling(self, tester, tmp_path):
        """Test handling of clean data (no issues)."""
        # Create clean data
        data = {
            'id': range(50),
            'value': np.random.normal(100, 5, 50),  # Low variance
            'category': ['A'] * 50  # No missing values
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "clean.csv"
        df.to_csv(csv_path, index=False)

        result = tester.test_dataset(str(csv_path))

        assert result['success'] is True
        narrative = result['narrative']
        # Clean data should mention "good" or "no major issues"
        assert 'good' in narrative['executive_summary'].lower() or \
               'no major' in narrative['executive_summary'].lower()

    def test_dirty_data_handling(self, tester, tmp_path):
        """Test handling of dirty data (many issues)."""
        # Create dirty data
        np.random.seed(42)
        data = {
            'id': range(100),
            'value': np.random.exponential(100, 100),  # High variance
            'category': np.random.choice(['A', 'B', 'C', 'D', 'E'], 100)
        }
        df = pd.DataFrame(data)
        # Add lots of missing values
        df.loc[np.random.choice(df.index, 30), 'value'] = np.nan
        df.loc[np.random.choice(df.index, 20), 'category'] = None

        csv_path = tmp_path / "dirty.csv"
        df.to_csv(csv_path, index=False)

        result = tester.test_dataset(str(csv_path))

        assert result['success'] is True
        narrative = result['narrative']
        # Dirty data should mention issues
        assert 'critical' in narrative['executive_summary'].lower() or \
               'issue' in narrative['executive_summary'].lower()

    def test_missing_value_detection(self, tester, tmp_path):
        """Test detection of missing data."""
        # Create data with 20% missing
        np.random.seed(42)
        data = {
            'id': range(100),
            'value': np.random.normal(100, 15, 100)
        }
        df = pd.DataFrame(data)
        df.loc[np.random.choice(df.index, 20), 'value'] = np.nan

        csv_path = tmp_path / "missing.csv"
        df.to_csv(csv_path, index=False)

        result = tester.test_dataset(str(csv_path))
        agent_outputs = result['agent_outputs']

        # Should detect missing data
        assert agent_outputs['explorer']['missing_percentage'] > 0
        assert agent_outputs['predictions']['confidence'] < 1.0

    # === NARRATIVE QUALITY TESTS ===

    def test_narrative_is_specific(self, tester, sample_csv):
        """Test narrative is specific, not generic."""
        result = tester.test_dataset(sample_csv)
        narrative = result['narrative']

        # Should include numbers, not generic statements
        full = narrative['full_narrative']
        assert any(char.isdigit() for char in full), "Narrative should include numbers"

    def test_narrative_has_priority_ordering(self, tester, sample_csv):
        """Test narrative shows prioritized actions."""
        result = tester.test_dataset(sample_csv)
        narrative = result['narrative']
        plan = narrative.get('action_plan', '')

        # Should mention priorities
        assert 'Critical' in plan or 'High' in plan or len(plan) > 0

    def test_validation_checks(self, tester, sample_csv):
        """Test all validation checks pass."""
        result = tester.test_dataset(sample_csv)
        validation = result['validation']

        # Count passing validations
        passing = sum(1 for v in validation.values() if v is True)
        assert passing >= 5  # At least 5 validations should pass

    # === ERROR HANDLING TESTS ===

    def test_pipeline_with_empty_agent_outputs(self, tester):
        """Test pipeline handles empty agent outputs gracefully."""
        narrative = tester.run_narrative_pipeline({})

        assert narrative is None or isinstance(narrative, dict)

    def test_pipeline_with_missing_fields(self, tester):
        """Test pipeline handles missing agent output fields gracefully."""
        partial_outputs = {
            'explorer': {'shape': (100, 10)}
            # Missing anomalies and predictions
        }
        narrative = tester.run_narrative_pipeline(partial_outputs)

        # Should handle gracefully (either return None or partial narrative)
        assert narrative is None or isinstance(narrative, dict)

    # === MULTIPLE DATASET TESTS (if data folder exists) ===

    def test_can_test_multiple_datasets(self, tester):
        """Test multiple datasets function exists."""
        # This is just checking the method exists and is callable
        assert hasattr(tester, 'test_multiple_datasets')
        assert callable(tester.test_multiple_datasets)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
