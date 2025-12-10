import time
import pandas as pd
import numpy as np
import pytest
from scipy import stats

from agents.explorer.explorer import Explorer


def test_shapiro_wilk_normality():
    """Test Shapiro-Wilk normality test on numeric data."""
    explorer = Explorer()
    
    # Normal distribution
    normal_data = np.random.normal(0, 1, 100)
    df_normal = pd.DataFrame({'value': normal_data})
    explorer.set_data(df_normal)
    
    result = explorer.test_normality('value')
    assert result is not None
    assert 'statistic' in result or 'p_value' in result


def test_kolmogorov_smirnov_test():
    """Test Kolmogorov-Smirnov test for distribution comparison."""
    explorer = Explorer()
    
    df = pd.DataFrame({
        'sample1': np.random.normal(0, 1, 100),
        'sample2': np.random.normal(0.5, 1, 100)
    })
    explorer.set_data(df)
    
    result = explorer.ks_test('sample1', 'sample2')
    assert result is not None


def test_distribution_fitting():
    """Test fitting common distributions to data."""
    explorer = Explorer()
    
    # Create data from normal distribution
    data = np.random.normal(10, 2, 500)
    df = pd.DataFrame({'value': data})
    explorer.set_data(df)
    
    result = explorer.fit_distribution('value')
    assert result is not None
    assert 'normal' in result or len(result) > 0


def test_skewness_kurtosis():
    """Test skewness and kurtosis calculations."""
    explorer = Explorer()
    
    # Symmetric data (skewness ~0)
    symmetric = np.random.normal(0, 1, 100)
    df = pd.DataFrame({'value': symmetric})
    explorer.set_data(df)
    
    result = explorer.calculate_skewness_kurtosis('value')
    assert result is not None
    assert 'skewness' in result
    assert 'kurtosis' in result


def test_outlier_detection_zscore():
    """Test z-score outlier detection."""
    explorer = Explorer()
    
    # Create data with outliers
    data = np.concatenate([np.random.normal(0, 1, 95), [10, 11, 12, 13, 14]])
    df = pd.DataFrame({'value': data})
    explorer.set_data(df)
    
    outliers = explorer.detect_outliers_zscore('value', threshold=3)
    assert outliers is not None
    assert len(outliers) > 0


def test_correlation_analysis():
    """Test correlation analysis with multiple columns."""
    explorer = Explorer()
    
    df = pd.DataFrame({
        'x': np.arange(100),
        'y': np.arange(100) + np.random.normal(0, 5, 100),
        'z': np.random.normal(0, 1, 100)
    })
    explorer.set_data(df)
    
    result = explorer.correlation_matrix()
    assert result is not None
    assert result.shape == (3, 3)


def test_statistical_summary():
    """Test comprehensive statistical summary."""
    explorer = Explorer()
    
    df = pd.DataFrame({
        'col1': np.random.normal(10, 2, 100),
        'col2': np.random.poisson(5, 100),
        'col3': np.random.exponential(2, 100)
    })
    explorer.set_data(df)
    
    result = explorer.get_statistical_summary()
    assert result is not None
    assert len(result) > 0


def test_statistical_performance_100k():
    """Test statistical analysis performance on 100K rows."""
    explorer = Explorer()
    
    df = pd.DataFrame({
        'value': np.random.normal(0, 1, 100_000),
        'category': np.random.choice(['A', 'B', 'C'], 100_000)
    })
    explorer.set_data(df)
    
    start = time.time()
    result = explorer.get_statistical_summary()
    duration = time.time() - start
    
    assert result is not None
    assert duration < 2.0, f"Statistical summary too slow: {duration}s (target <2s)"
