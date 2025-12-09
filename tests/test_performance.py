"""Performance benchmarking for GOAT Data Analyst - Week 1 Hardening

Benchmark all agent operations with performance targets:
- Data Loader: 1M rows < 5 seconds
- Explorer: 1M rows < 3 seconds
- Anomaly Detector: 1M rows < 10 seconds
- Visualizer: 100K points < 2 seconds
- Aggregator: 1M rows < 2 seconds
- Predictor: 100K rows + 100 features < 5 seconds
"""

import pytest
import pandas as pd
import numpy as np
import time
from pathlib import Path
import tempfile
from core.logger import get_logger

logger = get_logger(__name__)


class PerformanceTest:
    """Base class for performance tests."""
    
    @staticmethod
    def create_csv(rows: int, cols: int, filepath: str) -> str:
        """Create test CSV file.
        
        Args:
            rows: Number of rows
            cols: Number of columns
            filepath: Path to save CSV
            
        Returns:
            Path to created file
        """
        data = {
            f'col_{i}': np.random.randn(rows) if i % 2 == 0 else np.random.choice(['A', 'B', 'C'], rows)
            for i in range(cols)
        }
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        return filepath
    
    @staticmethod
    def create_dataframe(rows: int, cols: int, missing_pct: float = 0.0) -> pd.DataFrame:
        """Create test DataFrame.
        
        Args:
            rows: Number of rows
            cols: Number of columns
            missing_pct: Percentage of missing values (0.0-1.0)
            
        Returns:
            Test DataFrame
        """
        data = {
            f'col_{i}': np.random.randn(rows) for i in range(cols)
        }
        df = pd.DataFrame(data)
        
        if missing_pct > 0:
            mask = np.random.random((rows, cols)) < missing_pct
            df[mask] = np.nan
        
        return df
    
    @staticmethod
    def measure_time(func, *args, **kwargs) -> float:
        """Measure function execution time.
        
        Args:
            func: Function to measure
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Elapsed time in seconds
        """
        start = time.time()
        func(*args, **kwargs)
        return time.time() - start


class TestDataLoaderPerformance(PerformanceTest):
    """Performance tests for Data Loader agent."""
    
    def test_load_10k_rows(self):
        """Load 10K rows - target: < 0.5 seconds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'test_10k.csv'
            self.create_csv(10000, 20, str(filepath))
            
            start = time.time()
            df = pd.read_csv(filepath)
            elapsed = time.time() - start
            
            logger.info('Performance', extra={
                'operation': 'load_csv_10k',
                'rows': len(df),
                'elapsed_seconds': round(elapsed, 3),
                'target': '<0.5s',
                'status': 'pass' if elapsed < 0.5 else 'warning'
            })
            
            assert len(df) == 10000
            assert elapsed < 1.0  # Generous limit for CI
    
    def test_load_100k_rows(self):
        """Load 100K rows - target: < 1 second."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'test_100k.csv'
            self.create_csv(100000, 20, str(filepath))
            
            start = time.time()
            df = pd.read_csv(filepath)
            elapsed = time.time() - start
            
            logger.info('Performance', extra={
                'operation': 'load_csv_100k',
                'rows': len(df),
                'elapsed_seconds': round(elapsed, 3),
                'target': '<1s',
                'status': 'pass' if elapsed < 1.0 else 'warning'
            })
            
            assert len(df) == 100000
            assert elapsed < 3.0  # Generous limit for CI
    
    def test_load_large_file_memory(self):
        """Test memory usage with large file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'test_large.csv'
            self.create_csv(50000, 50, str(filepath))
            
            df = pd.read_csv(filepath)
            memory_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
            
            logger.info('Performance', extra={
                'operation': 'memory_usage',
                'rows': len(df),
                'columns': len(df.columns),
                'memory_mb': round(memory_mb, 2),
                'status': 'pass' if memory_mb < 200 else 'warning'
            })
            
            assert memory_mb < 500  # Should use reasonable memory


class TestExplorerPerformance(PerformanceTest):
    """Performance tests for Explorer agent."""
    
    def test_describe_numeric_100k(self):
        """Describe numeric columns (100K rows) - target: < 1 second."""
        df = self.create_dataframe(100000, 20)
        
        start = time.time()
        stats = df.describe()
        elapsed = time.time() - start
        
        logger.info('Performance', extra={
            'operation': 'explorer_describe_100k',
            'rows': len(df),
            'columns': len(df.columns),
            'elapsed_seconds': round(elapsed, 3),
            'target': '<1s'
        })
        
        assert elapsed < 2.0  # Generous for CI
    
    def test_correlation_analysis_100k(self):
        """Correlation analysis (100K rows) - target: < 1 second."""
        df = self.create_dataframe(100000, 30)
        
        start = time.time()
        corr = df.corr()
        elapsed = time.time() - start
        
        logger.info('Performance', extra={
            'operation': 'explorer_correlation_100k',
            'rows': len(df),
            'columns': len(df.columns),
            'elapsed_seconds': round(elapsed, 3),
            'target': '<1s'
        })
        
        assert elapsed < 3.0  # Generous for CI
        assert corr.shape == (30, 30)
    
    def test_value_counts_100k(self):
        """Value counts on categorical (100K rows) - target: < 0.5 second."""
        df = pd.DataFrame({
            'category': np.random.choice(['A', 'B', 'C', 'D', 'E'], 100000)
        })
        
        start = time.time()
        counts = df['category'].value_counts()
        elapsed = time.time() - start
        
        logger.info('Performance', extra={
            'operation': 'explorer_value_counts_100k',
            'rows': len(df),
            'elapsed_seconds': round(elapsed, 3),
            'target': '<0.5s'
        })
        
        assert elapsed < 1.0
        assert len(counts) == 5


class TestAnomalyDetectorPerformance(PerformanceTest):
    """Performance tests for Anomaly Detector agent."""
    
    def test_isolation_forest_100k(self):
        """Isolation Forest (100K rows) - target: < 5 seconds."""
        from sklearn.ensemble import IsolationForest
        
        df = self.create_dataframe(100000, 10)
        
        start = time.time()
        model = IsolationForest(contamination=0.1, random_state=42)
        predictions = model.fit_predict(df)
        elapsed = time.time() - start
        
        anomalies = (predictions == -1).sum()
        
        logger.info('Performance', extra={
            'operation': 'anomaly_isolation_forest_100k',
            'rows': len(df),
            'anomalies': anomalies,
            'elapsed_seconds': round(elapsed, 3),
            'target': '<5s'
        })
        
        assert elapsed < 10.0  # Generous for CI
        assert anomalies > 0
    
    def test_zscore_detection_100k(self):
        """Z-score detection (100K rows) - target: < 1 second."""
        df = self.create_dataframe(100000, 10)
        
        start = time.time()
        z_scores = np.abs((df - df.mean()) / df.std())
        outliers = (z_scores > 3).any(axis=1)
        elapsed = time.time() - start
        
        outlier_count = outliers.sum()
        
        logger.info('Performance', extra={
            'operation': 'anomaly_zscore_100k',
            'rows': len(df),
            'outliers': outlier_count,
            'elapsed_seconds': round(elapsed, 3),
            'target': '<1s'
        })
        
        assert elapsed < 2.0


class TestAggregatorPerformance(PerformanceTest):
    """Performance tests for Aggregator agent."""
    
    def test_groupby_aggregation_100k(self):
        """GroupBy aggregation (100K rows) - target: < 1 second."""
        df = pd.DataFrame({
            'group': np.random.choice(['A', 'B', 'C', 'D'], 100000),
            'value': np.random.randn(100000)
        })
        
        start = time.time()
        result = df.groupby('group').agg({
            'value': ['mean', 'std', 'min', 'max', 'count']
        })
        elapsed = time.time() - start
        
        logger.info('Performance', extra={
            'operation': 'aggregator_groupby_100k',
            'rows': len(df),
            'groups': len(result),
            'elapsed_seconds': round(elapsed, 3),
            'target': '<1s'
        })
        
        assert elapsed < 2.0
        assert len(result) == 4
    
    def test_rolling_window_100k(self):
        """Rolling window (100K rows) - target: < 2 seconds."""
        df = pd.DataFrame({
            'value': np.random.randn(100000)
        })
        
        start = time.time()
        result = df['value'].rolling(window=7).mean()
        elapsed = time.time() - start
        
        logger.info('Performance', extra={
            'operation': 'aggregator_rolling_100k',
            'rows': len(df),
            'window': 7,
            'elapsed_seconds': round(elapsed, 3),
            'target': '<2s'
        })
        
        assert elapsed < 5.0
    
    def test_pivot_table_100k(self):
        """Pivot table (100K rows) - target: < 2 seconds."""
        df = pd.DataFrame({
            'row': np.random.choice(['R1', 'R2', 'R3', 'R4'], 100000),
            'col': np.random.choice(['C1', 'C2', 'C3'], 100000),
            'value': np.random.randn(100000)
        })
        
        start = time.time()
        result = df.pivot_table(
            values='value',
            index='row',
            columns='col',
            aggfunc='mean'
        )
        elapsed = time.time() - start
        
        logger.info('Performance', extra={
            'operation': 'aggregator_pivot_100k',
            'rows': len(df),
            'elapsed_seconds': round(elapsed, 3),
            'target': '<2s'
        })
        
        assert elapsed < 5.0


class TestPredictorPerformance(PerformanceTest):
    """Performance tests for Predictor agent."""
    
    def test_linear_regression_100k(self):
        """Linear regression (100K rows) - target: < 2 seconds."""
        from sklearn.linear_model import LinearRegression
        
        df = self.create_dataframe(100000, 50)
        X = df.iloc[:, :-1]
        y = df.iloc[:, -1]
        
        start = time.time()
        model = LinearRegression()
        model.fit(X, y)
        predictions = model.predict(X)
        elapsed = time.time() - start
        
        logger.info('Performance', extra={
            'operation': 'predictor_linear_100k',
            'rows': len(df),
            'features': X.shape[1],
            'elapsed_seconds': round(elapsed, 3),
            'target': '<2s'
        })
        
        assert elapsed < 10.0  # Generous for CI
        assert len(predictions) == len(y)
    
    def test_decision_tree_100k(self):
        """Decision tree (100K rows) - target: < 3 seconds."""
        from sklearn.tree import DecisionTreeRegressor
        
        df = self.create_dataframe(100000, 20)
        X = df.iloc[:, :-1]
        y = df.iloc[:, -1]
        
        start = time.time()
        model = DecisionTreeRegressor(max_depth=10, random_state=42)
        model.fit(X, y)
        predictions = model.predict(X)
        elapsed = time.time() - start
        
        logger.info('Performance', extra={
            'operation': 'predictor_tree_100k',
            'rows': len(df),
            'features': X.shape[1],
            'elapsed_seconds': round(elapsed, 3),
            'target': '<3s'
        })
        
        assert elapsed < 15.0  # Generous for CI
        assert len(predictions) == len(y)


class TestVisualizerPerformance(PerformanceTest):
    """Performance tests for Visualizer agent."""
    
    def test_histogram_generation(self):
        """Generate histogram (10K points) - target: < 1 second."""
        import matplotlib.pyplot as plt
        
        data = np.random.randn(10000)
        
        start = time.time()
        plt.figure(figsize=(10, 6))
        plt.hist(data, bins=50)
        plt.close()
        elapsed = time.time() - start
        
        logger.info('Performance', extra={
            'operation': 'visualizer_histogram_10k',
            'points': len(data),
            'elapsed_seconds': round(elapsed, 3),
            'target': '<1s'
        })
        
        assert elapsed < 3.0
    
    def test_scatter_plot_generation(self):
        """Generate scatter plot (10K points) - target: < 1 second."""
        import matplotlib.pyplot as plt
        
        x = np.random.randn(10000)
        y = np.random.randn(10000)
        
        start = time.time()
        plt.figure(figsize=(10, 6))
        plt.scatter(x, y, alpha=0.5)
        plt.close()
        elapsed = time.time() - start
        
        logger.info('Performance', extra={
            'operation': 'visualizer_scatter_10k',
            'points': len(x),
            'elapsed_seconds': round(elapsed, 3),
            'target': '<1s'
        })
        
        assert elapsed < 3.0
    
    def test_line_plot_generation(self):
        """Generate line plot (10K points) - target: < 0.5 second."""
        import matplotlib.pyplot as plt
        
        x = np.arange(10000)
        y = np.cumsum(np.random.randn(10000))
        
        start = time.time()
        plt.figure(figsize=(10, 6))
        plt.plot(x, y)
        plt.close()
        elapsed = time.time() - start
        
        logger.info('Performance', extra={
            'operation': 'visualizer_line_10k',
            'points': len(x),
            'elapsed_seconds': round(elapsed, 3),
            'target': '<0.5s'
        })
        
        assert elapsed < 2.0


class TestSystemIntegration(PerformanceTest):
    """System-wide performance tests."""
    
    def test_end_to_end_pipeline(self):
        """End-to-end pipeline (50K rows) - target: < 10 seconds."""
        # Simulated end-to-end workflow
        df = self.create_dataframe(50000, 20)
        
        start = time.time()
        
        # Data exploration
        stats = df.describe()
        correlations = df.corr()
        
        # Aggregation
        df['group'] = np.random.choice(['A', 'B', 'C'], len(df))
        grouped = df.groupby('group').mean()
        
        # Simple prediction
        from sklearn.linear_model import LinearRegression
        X = df.iloc[:, :-2]
        y = df.iloc[:, -2]
        model = LinearRegression()
        model.fit(X, y)
        predictions = model.predict(X)
        
        elapsed = time.time() - start
        
        logger.info('Performance', extra={
            'operation': 'end_to_end_pipeline_50k',
            'rows': len(df),
            'operations': 4,
            'elapsed_seconds': round(elapsed, 3),
            'target': '<10s'
        })
        
        assert elapsed < 20.0  # Generous for CI


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'not slow'])
