#!/usr/bin/env python3
"""Test script for Explorer agent.

Usage:
    python scripts/test_explorer.py
"""

import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.data_loader import DataLoader
from agents.explorer import Explorer
from core.logger import get_logger

logger = get_logger(__name__)


def main():
    """Test Explorer agent with sample data."""
    logger.info("="*80)
    logger.info("Testing Explorer Agent")
    logger.info("="*80)
    
    # Load sample data
    logger.info("\nStep 1: Loading sample data...")
    loader = DataLoader()
    sample_file = project_root / "data" / "sample_data.csv"
    
    result = loader.load(str(sample_file))
    if result["status"] != "success":
        logger.error(f"Failed to load data: {result.get('message')}")
        return
    
    logger.info(f"[OK] Loaded {result['data'].shape[0]} rows, {result['data'].shape[1]} columns")
    
    # Initialize Explorer
    logger.info("\nStep 2: Initializing Explorer...")
    explorer = Explorer()
    explorer.set_data(result["data"])
    logger.info("[OK] Explorer initialized with data")
    
    # Test 1: Numeric statistics
    logger.info("\nStep 3: Computing numeric statistics...")
    try:
        numeric_stats = explorer.describe_numeric()
        logger.info(f"[OK] Status: {numeric_stats['status']}")
        logger.info(f"[OK] Numeric columns: {numeric_stats['numeric_columns']}")
        logger.info("Numeric statistics:")
        for col, stats in numeric_stats['statistics'].items():
            logger.info(f"  {col}:")
            logger.info(f"    Mean: {stats['mean']:.2f}")
            logger.info(f"    Median: {stats['median']:.2f}")
            logger.info(f"    Std Dev: {stats['std']:.2f}")
            logger.info(f"    Min: {stats['min']:.2f}")
            logger.info(f"    Max: {stats['max']:.2f}")
    except Exception as e:
        logger.error(f"[ERROR] Failed to compute numeric statistics: {e}")
    
    # Test 2: Categorical statistics
    logger.info("\nStep 4: Computing categorical statistics...")
    try:
        cat_stats = explorer.describe_categorical()
        logger.info(f"[OK] Status: {cat_stats['status']}")
        logger.info(f"[OK] Categorical columns: {cat_stats['categorical_columns']}")
        logger.info("Categorical statistics:")
        for col, stats in cat_stats['statistics'].items():
            logger.info(f"  {col}:")
            logger.info(f"    Unique values: {stats['unique_values']}")
            logger.info(f"    Most common: {stats['most_common']} ({stats['most_common_count']} times)")
    except Exception as e:
        logger.error(f"[ERROR] Failed to compute categorical statistics: {e}")
    
    # Test 3: Correlation analysis
    logger.info("\nStep 5: Analyzing correlations...")
    try:
        correlations = explorer.correlation_analysis()
        logger.info(f"[OK] Status: {correlations['status']}")
        if 'strong_correlations' in correlations:
            logger.info(f"[OK] Found {len(correlations['strong_correlations'])} strong correlations")
            for corr in correlations['strong_correlations']:
                logger.info(f"  {corr['col1']} <-> {corr['col2']}: {corr['correlation']}")
    except Exception as e:
        logger.error(f"[ERROR] Failed to analyze correlations: {e}")
    
    # Test 4: Data quality assessment
    logger.info("\nStep 6: Assessing data quality...")
    try:
        quality = explorer.data_quality_assessment()
        logger.info(f"[OK] Status: {quality['status']}")
        logger.info(f"[OK] Quality Score: {quality['overall_quality_score']}/100")
        logger.info(f"[OK] Quality Rating: {quality['quality_rating']}")
        logger.info(f"[OK] Null cells: {quality['null_cells']} ({quality['null_percentage']}%)")
        logger.info(f"[OK] Duplicates: {quality['duplicates']} ({quality['duplicate_percentage']}%)")
    except Exception as e:
        logger.error(f"[ERROR] Failed to assess data quality: {e}")
    
    # Test 5: Outlier detection
    logger.info("\nStep 7: Detecting outliers...")
    try:
        outliers = explorer.detect_outliers(method="iqr")
        logger.info(f"[OK] Status: {outliers['status']}")
        logger.info(f"[OK] Total outliers found: {outliers['total_outliers']}")
        logger.info(f"[OK] Columns with outliers: {outliers['columns_with_outliers']}")
        for col, data in outliers['outliers'].items():
            logger.info(f"  {col}: {data['count']} outliers ({data['percentage']}%)")
    except Exception as e:
        logger.error(f"[ERROR] Failed to detect outliers: {e}")
    
    # Test 6: Full summary report
    logger.info("\nStep 8: Generating summary report...")
    try:
        report = explorer.get_summary_report()
        logger.info(f"[OK] Report generated at {report['timestamp']}")
        logger.info(f"[OK] Data shape: {report['shape']['rows']} rows x {report['shape']['columns']} columns")
        logger.info(f"[OK] Numeric columns analyzed: {len(report['numeric_stats'].get('statistics', {}))}")
        logger.info(f"[OK] Categorical columns analyzed: {len(report['categorical_stats'].get('statistics', {}))}")
    except Exception as e:
        logger.error(f"[ERROR] Failed to generate report: {e}")
    
    logger.info("\n" + "="*80)
    logger.info("[OK] All Explorer tests completed successfully!")
    logger.info("="*80)


if __name__ == "__main__":
    main()
