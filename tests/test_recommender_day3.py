"""Week 2 Day 3: Recommender Agent Integration Tests (10 tests).

Tests:
1. Agent initialization
2. Data loading
3. Missing data analysis
4. Duplicate analysis
5. Distribution analysis
6. Correlation analysis
7. Action plan generation
8. Empty dataframe handling
9. Single row handling
10. Performance benchmark
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import time

from agents.recommender import Recommender


class TestRecommenderInitialization:
    """Test 1: Agent initialization."""

    def test_agent_initializes(self):
        """Test agent initializes successfully."""
        recommender = Recommender()
        assert recommender is not None
        assert recommender.name == "Recommender"
        assert recommender.data is None
        assert recommender.missing_data_analyzer is not None
        assert recommender.duplicate_analyzer is not None
        assert recommender.distribution_analyzer is not None
        assert recommender.correlation_analyzer is not None
        assert recommender.action_plan_generator is not None


class TestRecommenderDataLoading:
    """Test 2: Data loading and management."""

    @pytest.fixture
    def recommender(self):
        return Recommender()

    @pytest.fixture
    def sample_data(self):
        """Create sample DataFrame (100 rows, 5 columns with some missing/duplicates)."""
        np.random.seed(42)
        df = pd.DataFrame({
            'feature_1': np.random.randn(100),
            'feature_2': np.random.randn(100),
            'feature_3': np.random.randn(100),
            'category': np.random.choice(['A', 'B', 'C'], 100),
            'value': np.random.randn(100) * 10,
        })
        # Add some missing values
        df.loc[0:5, 'feature_1'] = np.nan
        # Add some duplicates
        df.loc[50] = df.loc[49]
        return df

    def test_set_data(self, recommender, sample_data):
        """Test setting data."""
        recommender.set_data(sample_data)
        assert recommender.data is not None
        assert recommender.data.shape == (100, 5)

    def test_get_data(self, recommender, sample_data):
        """Test getting data."""
        recommender.set_data(sample_data)
        retrieved = recommender.get_data()
        assert retrieved is not None
        assert retrieved.shape == sample_data.shape

    def test_data_copy(self, recommender, sample_data):
        """Test data is copied (not referenced)."""
        recommender.set_data(sample_data)
        sample_data.iloc[0, 0] = 999
        retrieved = recommender.get_data()
        assert retrieved.iloc[0, 0] != 999 or pd.isna(retrieved.iloc[0, 0])


class TestMissingDataAnalysis:
    """Test 3: Missing data analysis."""

    @pytest.fixture
    def recommender_with_data(self):
        recommender = Recommender()
        np.random.seed(42)
        df = pd.DataFrame({
            'x': np.random.randn(100),
            'y': np.random.randn(100),
            'z': np.random.randn(100),
        })
        df.loc[0:10, 'x'] = np.nan
        df.loc[20:25, 'y'] = np.nan
        recommender.set_data(df)
        return recommender

    def test_missing_data_analysis(self, recommender_with_data):
        """Test missing data analysis runs successfully."""
        result = recommender_with_data.analyze_missing_data()
        assert result is not None
        assert isinstance(result, dict)
        assert 'status' in result

    def test_missing_data_results(self, recommender_with_data):
        """Test missing data analysis returns worker results."""
        result = recommender_with_data.analyze_missing_data()
        assert result['status'] == 'success'
        assert 'worker_result' in result


class TestDuplicateAnalysis:
    """Test 4: Duplicate analysis."""

    @pytest.fixture
    def recommender_with_data(self):
        recommender = Recommender()
        np.random.seed(42)
        df = pd.DataFrame({
            'a': np.random.randn(100),
            'b': np.random.randn(100),
        })
        # Add duplicates
        df.loc[50:55] = df.loc[49:54].values
        recommender.set_data(df)
        return recommender

    def test_duplicate_analysis(self, recommender_with_data):
        """Test duplicate analysis runs successfully."""
        result = recommender_with_data.analyze_duplicates()
        assert result is not None
        assert isinstance(result, dict)
        assert 'status' in result

    def test_duplicate_results(self, recommender_with_data):
        """Test duplicate analysis returns worker results."""
        result = recommender_with_data.analyze_duplicates()
        assert result['status'] == 'success'
        assert 'worker_result' in result


class TestDistributionAnalysis:
    """Test 5: Distribution analysis."""

    @pytest.fixture
    def recommender_with_data(self):
        recommender = Recommender()
        np.random.seed(42)
        df = pd.DataFrame({
            'col1': np.random.randn(100),
            'col2': np.random.randn(100) * 2 + 5,
            'col3': np.random.randint(1, 100, 100),
        })
        recommender.set_data(df)
        return recommender

    def test_distribution_analysis(self, recommender_with_data):
        """Test distribution analysis runs successfully."""
        result = recommender_with_data.analyze_distributions()
        assert result is not None
        assert isinstance(result, dict)
        assert 'status' in result

    def test_distribution_results(self, recommender_with_data):
        """Test distribution analysis returns worker results."""
        result = recommender_with_data.analyze_distributions()
        assert result['status'] == 'success'
        assert 'worker_result' in result


class TestCorrelationAnalysis:
    """Test 6: Correlation analysis."""

    @pytest.fixture
    def recommender_with_data(self):
        recommender = Recommender()
        np.random.seed(42)
        df = pd.DataFrame({
            'x': np.random.randn(100),
            'y': np.random.randn(100),
            'z': np.random.randn(100),
            'w': np.random.randn(100),
        })
        recommender.set_data(df)
        return recommender

    def test_correlation_analysis(self, recommender_with_data):
        """Test correlation analysis runs successfully."""
        result = recommender_with_data.analyze_correlations()
        assert result is not None
        assert isinstance(result, dict)
        assert 'status' in result

    def test_correlation_results(self, recommender_with_data):
        """Test correlation analysis returns worker results."""
        result = recommender_with_data.analyze_correlations()
        assert result['status'] == 'success'
        assert 'worker_result' in result


class TestActionPlanGeneration:
    """Test 7: Action plan generation."""

    @pytest.fixture
    def recommender_with_data(self):
        recommender = Recommender()
        np.random.seed(42)
        df = pd.DataFrame({
            'feature_1': np.random.randn(100),
            'feature_2': np.random.randn(100),
            'feature_3': np.random.choice(['A', 'B'], 100),
        })
        df.loc[0:5, 'feature_1'] = np.nan
        recommender.set_data(df)
        return recommender

    def test_action_plan_generation(self, recommender_with_data):
        """Test action plan generation runs successfully."""
        result = recommender_with_data.generate_action_plan()
        assert result is not None
        assert isinstance(result, dict)
        assert 'status' in result

    def test_action_plan_results(self, recommender_with_data):
        """Test action plan generation returns worker results."""
        result = recommender_with_data.generate_action_plan()
        assert result['status'] == 'success'
        assert 'worker_result' in result


class TestSummaryInsights:
    """Test 7b: Summary insights generation."""

    @pytest.fixture
    def recommender_with_data(self):
        recommender = Recommender()
        np.random.seed(42)
        df = pd.DataFrame({
            'x': np.random.randn(100),
            'y': np.random.randn(100),
            'z': np.random.choice(['X', 'Y'], 100),
        })
        recommender.set_data(df)
        return recommender

    def test_summary_insights(self, recommender_with_data):
        """Test summary insights generation runs successfully."""
        result = recommender_with_data.get_summary_insights()
        assert result is not None
        assert isinstance(result, dict)
        assert 'status' in result

    def test_summary_insights_content(self, recommender_with_data):
        """Test summary insights returns insights list."""
        result = recommender_with_data.get_summary_insights()
        assert result['status'] == 'success'
        assert 'insights' in result
        assert isinstance(result['insights'], list)
        assert len(result['insights']) > 0


class TestEdgeCases:
    """Test 8: Empty dataframe handling."""

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        recommender = Recommender()
        empty_df = pd.DataFrame()
        recommender.set_data(empty_df)
        assert recommender.get_data() is not None
        assert recommender.get_data().shape[0] == 0

    def test_single_row_dataframe(self):
        """Test 9: Single row handling."""
        recommender = Recommender()
        single_row = pd.DataFrame({
            'x': [1.0],
            'y': [2.0],
            'z': [3.0]
        })
        recommender.set_data(single_row)
        assert recommender.get_data().shape[0] == 1

    def test_no_data_error(self):
        """Test error when no data is set."""
        recommender = Recommender()
        with pytest.raises(Exception):
            recommender.analyze_missing_data()


class TestPerformance:
    """Test 10: Performance benchmark."""

    def test_analysis_performance_1k_rows(self):
        """Test analysis on 1,000 rows completes in reasonable time."""
        recommender = Recommender()
        np.random.seed(42)
        df = pd.DataFrame({
            f'feature_{i}': np.random.randn(1000)
            for i in range(5)
        })
        df['category'] = np.random.choice(['A', 'B', 'C'], 1000)
        recommender.set_data(df)

        start = time.time()
        
        # Run multiple analyses
        result1 = recommender.analyze_missing_data()
        result2 = recommender.analyze_duplicates()
        result3 = recommender.analyze_distributions()
        
        elapsed = time.time() - start

        assert elapsed < 30  # Should complete in < 30 seconds
        assert result1 is not None
        assert result2 is not None
        assert result3 is not None


class TestComprehensiveAnalysis:
    """Test comprehensive analysis pipeline."""

    def test_full_analysis_pipeline(self):
        """Test running all analyses on same dataset."""
        recommender = Recommender()
        np.random.seed(42)
        df = pd.DataFrame({
            'x': np.random.randn(100),
            'y': np.random.randn(100),
            'z': np.random.choice(['A', 'B'], 100),
        })
        df.loc[0:5, 'x'] = np.nan
        df.loc[50] = df.loc[49]
        
        recommender.set_data(df)
        
        # Run all analyses
        result1 = recommender.analyze_missing_data()
        result2 = recommender.analyze_duplicates()
        result3 = recommender.analyze_distributions()
        result4 = recommender.analyze_correlations()
        result5 = recommender.generate_action_plan()
        
        # All should succeed
        assert result1['status'] == 'success'
        assert result2['status'] == 'success'
        assert result3['status'] == 'success'
        assert result4['status'] == 'success'
        assert result5['status'] == 'success'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
