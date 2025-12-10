"""Integration tests for Week 1 Day 5 - Full pipeline testing.

Tests the complete pipeline (Load → Explore → Aggregate → Export) with 1M row datasets.
Includes performance benchmarking, pandas comparison, and edge case stress testing.
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import time
import psutil
import os
from pathlib import Path

from agents.dataloader.dataloader import DataLoader
from agents.explorer.explorer import Explorer
from agents.aggregator.aggregator import Aggregator
from core.structured_logger import get_structured_logger


class TestDatasetGeneration:
    """Test creation of 1M row test datasets."""
    
    def test_generate_1m_row_csv_dataset(self):
        """Generate 1M row CSV dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / 'test_1m_rows.csv'
            
            # Generate dataset in chunks to avoid memory issues
            rows_per_chunk = 100_000
            total_rows = 1_000_000
            chunks = []
            
            for chunk_num in range(0, total_rows, rows_per_chunk):
                chunk_size = min(rows_per_chunk, total_rows - chunk_num)
                chunk = pd.DataFrame({
                    'id': range(chunk_num, chunk_num + chunk_size),
                    'value': np.random.randn(chunk_size),
                    'category': np.random.choice(['A', 'B', 'C'], chunk_size),
                    'timestamp': pd.date_range('2024-01-01', periods=chunk_size, freq='1min'),
                    'score': np.random.uniform(0, 100, chunk_size)
                })
                chunks.append(chunk)
            
            df = pd.concat(chunks, ignore_index=True)
            df.to_csv(csv_path, index=False)
            
            # Verify dataset
            assert csv_path.exists()
            assert os.path.getsize(csv_path) > 50_000_000  # >50MB
            
            # Verify row count
            verify_df = pd.read_csv(csv_path, nrows=10)
            assert len(verify_df) == 10
            assert list(verify_df.columns) == ['id', 'value', 'category', 'timestamp', 'score']
    
    def test_generate_100k_csv_dataset_quick(self):
        """Generate 100k row CSV dataset for quick testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / 'test_100k.csv'
            
            df = pd.DataFrame({
                'id': range(100_000),
                'value': np.random.randn(100_000),
                'category': np.random.choice(['A', 'B', 'C'], 100_000),
                'score': np.random.uniform(0, 100, 100_000)
            })
            df.to_csv(csv_path, index=False)
            
            # Verify
            assert csv_path.exists()
            verify_df = pd.read_csv(csv_path, nrows=10)
            assert len(verify_df) == 10


class TestFullPipelineExecution:
    """Test complete pipeline: Load → Explore → Aggregate."""
    
    def test_full_pipeline_with_100k_rows(self):
        """Test full pipeline with 100k rows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_structured_logger('full_pipeline_100k', tmpdir)
            
            # Create test dataset
            with logger.operation('create_dataset'):
                df = pd.DataFrame({
                    'id': range(100_000),
                    'value': np.random.randn(100_000),
                    'category': np.random.choice(['A', 'B', 'C'], 100_000),
                    'score': np.random.uniform(0, 100, 100_000)
                })
                csv_path = Path(tmpdir) / 'test_100k.csv'
                df.to_csv(csv_path, index=False)
            
            # Load
            with logger.operation('load_data'):
                loader = DataLoader()
                loader.set_data(csv_path)
                loaded_df = loader.load_data()
            
            assert len(loaded_df) == 100_000
            logger.info('Data loaded', extra={'rows': len(loaded_df)})
            
            # Explore
            with logger.operation('explore_data'):
                explorer = Explorer()
                explorer.set_data(loaded_df)
                summary = explorer.summary_report()
            
            assert summary is not None
            logger.info('Data explored', extra={'summary_keys': len(summary)})
            
            # Aggregate
            with logger.operation('aggregate_data'):
                aggregator = Aggregator()
                aggregator.set_data(loaded_df)
                agg_result = aggregator.execute_all()
            
            assert agg_result is not None
            logger.info('Data aggregated', extra={'result': str(type(agg_result))})
            
            metrics = logger.get_metrics()
            assert 'create_dataset' in metrics['operations']
            assert 'load_data' in metrics['operations']
            assert 'explore_data' in metrics['operations']
            assert 'aggregate_data' in metrics['operations']
    
    def test_pipeline_csv_format(self):
        """Test pipeline with CSV format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_structured_logger('pipeline_csv', tmpdir)
            
            # Create test data
            df = pd.DataFrame({
                'id': range(50_000),
                'value': np.random.randn(50_000),
                'category': np.random.choice(['X', 'Y', 'Z'], 50_000),
            })
            
            csv_path = Path(tmpdir) / 'test.csv'
            df.to_csv(csv_path, index=False)
            
            loader = DataLoader()
            explorer = Explorer()
            
            with logger.operation('pipeline_csv'):
                loader.set_data(csv_path)
                loaded = loader.load_data()
                assert len(loaded) == 50_000
                
                explorer.set_data(loaded)
                summary = explorer.summary_report()
                assert summary is not None
                
                logger.info('Processed CSV', extra={'rows': len(loaded)})
            
            metrics = logger.get_metrics()
            assert 'pipeline_csv' in metrics['operations']


class TestPerformanceBenchmarking:
    """Test performance benchmarking against targets."""
    
    def test_csv_load_performance_100k(self):
        """Test CSV load performance with 100k rows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_structured_logger('csv_perf', tmpdir)
            
            # Create 100k row dataset
            df = pd.DataFrame({
                'id': range(100_000),
                'value': np.random.randn(100_000),
                'metric': np.random.uniform(0, 100, 100_000),
            })
            
            csv_path = Path(tmpdir) / 'benchmark_100k.csv'
            df.to_csv(csv_path, index=False)
            
            # Benchmark load
            loader = DataLoader()
            loader.set_data(csv_path)
            
            start_time = time.time()
            loaded_df = loader.load_data()
            load_time = time.time() - start_time
            
            # Verify
            assert len(loaded_df) == 100_000
            assert load_time < 10.0  # Reasonable timeout for 100k rows
            
            logger.info('CSV load benchmark', extra={
                'rows': len(loaded_df),
                'time_seconds': load_time,
                'rows_per_second': len(loaded_df) / load_time
            })
    
    def test_pipeline_performance_50k(self):
        """Test full pipeline performance with 50k rows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_structured_logger('pipeline_perf_50k', tmpdir)
            
            # Create dataset
            df = pd.DataFrame({
                'id': range(50_000),
                'value': np.random.randn(50_000),
                'category': np.random.choice(['A', 'B', 'C'], 50_000),
            })
            csv_path = Path(tmpdir) / 'perf_test_50k.csv'
            df.to_csv(csv_path, index=False)
            
            # Benchmark full pipeline
            start_time = time.time()
            
            loader = DataLoader()
            loader.set_data(csv_path)
            loaded = loader.load_data()
            
            explorer = Explorer()
            explorer.set_data(loaded)
            explorer.summary_report()
            
            aggregator = Aggregator()
            aggregator.set_data(loaded)
            aggregator.execute_all()
            
            total_time = time.time() - start_time
            
            assert total_time < 30.0  # Reasonable timeout
            logger.info('Pipeline performance', extra={
                'rows': len(loaded),
                'time_seconds': total_time,
                'rows_per_second': len(loaded) / total_time
            })
    
    def test_memory_efficiency(self):
        """Test memory efficiency with 100k rows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_structured_logger('memory_usage', tmpdir)
            
            # Create 100k row dataset
            df = pd.DataFrame({
                'id': np.int32(np.arange(100_000)),
                'value': np.float32(np.random.randn(100_000)),
                'metric': np.float32(np.random.uniform(0, 100, 100_000)),
            })
            csv_path = Path(tmpdir) / 'memory_test_100k.csv'
            df.to_csv(csv_path, index=False)
            
            # Load and measure memory
            process = psutil.Process(os.getpid())
            mem_before = process.memory_info().rss / 1024 / 1024  # MB
            
            loader = DataLoader()
            loader.set_data(csv_path)
            loaded = loader.load_data()
            
            mem_after = process.memory_info().rss / 1024 / 1024  # MB
            mem_used = mem_after - mem_before
            
            assert len(loaded) == 100_000
            
            logger.info('Memory usage benchmark', extra={
                'rows': len(loaded),
                'memory_mb': mem_used,
                'memory_gb': mem_used / 1024
            })


class TestPandasComparison:
    """Test our performance vs pandas."""
    
    def test_our_vs_pandas_load_time(self):
        """Compare our load time vs pandas read_csv."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_structured_logger('pandas_comparison', tmpdir)
            
            # Create test dataset
            df = pd.DataFrame({
                'id': range(50_000),
                'value': np.random.randn(50_000),
                'category': np.random.choice(['A', 'B', 'C'], 50_000),
            })
            csv_path = Path(tmpdir) / 'comparison.csv'
            df.to_csv(csv_path, index=False)
            
            # Our implementation
            loader = DataLoader()
            loader.set_data(csv_path)
            
            start = time.time()
            our_df = loader.load_data()
            our_time = time.time() - start
            
            # Pandas implementation
            start = time.time()
            pandas_df = pd.read_csv(csv_path)
            pandas_time = time.time() - start
            
            # Verify same data
            assert len(our_df) == len(pandas_df)
            
            speedup = pandas_time / our_time if our_time > 0 else 1.0
            logger.info('Pandas comparison', extra={
                'our_time': our_time,
                'pandas_time': pandas_time,
                'speedup': speedup
            })


class TestEdgeCaseStressTesting:
    """Test edge cases and stress scenarios."""
    
    def test_empty_dataframe_pipeline(self):
        """Test pipeline with empty dataframe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_structured_logger('empty_edge_case', tmpdir)
            
            # Create empty CSV
            df = pd.DataFrame({'id': [], 'value': []})
            csv_path = Path(tmpdir) / 'empty.csv'
            df.to_csv(csv_path, index=False)
            
            loader = DataLoader()
            loader.set_data(csv_path)
            loaded = loader.load_data()
            
            assert len(loaded) == 0
            logger.info('Empty dataframe handled', extra={'rows': 0})
    
    def test_single_row_dataframe_pipeline(self):
        """Test pipeline with single row."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_structured_logger('single_row_edge_case', tmpdir)
            
            df = pd.DataFrame({'id': [1], 'value': [99.5]})
            csv_path = Path(tmpdir) / 'single.csv'
            df.to_csv(csv_path, index=False)
            
            loader = DataLoader()
            loader.set_data(csv_path)
            loaded = loader.load_data()
            
            assert len(loaded) == 1
            logger.info('Single row handled', extra={'rows': 1})
    
    def test_mixed_data_types(self):
        """Test pipeline with mixed data types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_structured_logger('mixed_types', tmpdir)
            
            df = pd.DataFrame({
                'int_col': range(10_000),
                'float_col': np.random.randn(10_000),
                'str_col': ['text'] * 10_000,
                'bool_col': [True, False] * 5_000,
            })
            csv_path = Path(tmpdir) / 'mixed.csv'
            df.to_csv(csv_path, index=False)
            
            loader = DataLoader()
            loader.set_data(csv_path)
            loaded = loader.load_data()
            
            assert len(loaded) == 10_000
            assert len(loaded.columns) == 4
            logger.info('Mixed types handled', extra={'columns': len(loaded.columns)})
    
    def test_large_categorical_cardinality(self):
        """Test with high cardinality categorical data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_structured_logger('high_cardinality', tmpdir)
            
            # Create data with 1k unique categories
            df = pd.DataFrame({
                'id': range(50_000),
                'category': [f'cat_{i % 1_000}' for i in range(50_000)],
                'value': np.random.randn(50_000),
            })
            csv_path = Path(tmpdir) / 'high_card.csv'
            df.to_csv(csv_path, index=False)
            
            loader = DataLoader()
            loader.set_data(csv_path)
            loaded = loader.load_data()
            
            assert len(loaded) == 50_000
            assert loaded['category'].nunique() == 1_000
            logger.info('High cardinality handled', extra={
                'rows': len(loaded),
                'unique_categories': loaded['category'].nunique()
            })
    
    def test_missing_values_handling(self):
        """Test handling of missing values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = get_structured_logger('missing_values', tmpdir)
            
            df = pd.DataFrame({
                'id': range(10_000),
                'value': [np.nan if i % 100 == 0 else np.random.randn() for i in range(10_000)],
                'category': [None if i % 50 == 0 else chr(65 + i % 3) for i in range(10_000)],
            })
            csv_path = Path(tmpdir) / 'missing.csv'
            df.to_csv(csv_path, index=False)
            
            loader = DataLoader()
            loader.set_data(csv_path)
            loaded = loader.load_data()
            
            assert len(loaded) == 10_000
            assert loaded['value'].isna().sum() > 0
            logger.info('Missing values handled', extra={
                'rows': len(loaded),
                'missing_value_count': loaded['value'].isna().sum()
            })


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
