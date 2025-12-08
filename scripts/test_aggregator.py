#!/usr/bin/env python3
"""Test Aggregator agent with real datasets.

Usage:
    python scripts/test_aggregator.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.data_loader import DataLoader
from agents.aggregator import Aggregator
from core.logger import get_logger

logger = get_logger(__name__)


def test_aggregations(file_path):
    """Test Aggregator with a dataset."""
    logger.info(f"\n[FILE] {file_path.name}")
    logger.info("-" * 80)
    
    # Load data
    loader = DataLoader()
    result = loader.load(str(file_path))
    
    if result["status"] != "success":
        logger.error("Failed to load")
        return
    
    df = result["data"]
    logger.info(f"Rows: {df.shape[0]:,} | Columns: {df.shape[1]}")
    
    # Initialize Aggregator
    agg = Aggregator()
    agg.set_data(df)
    
    # Test 1: Value counts on categorical columns
    logger.info("\n[VALUE COUNTS]")
    try:
        cat_cols = df.select_dtypes(include=['object']).columns.tolist()
        if cat_cols:
            col = cat_cols[0]
            vc = agg.value_counts(col, top_n=5)
            logger.info(f"Top 5 values in '{col}' (unique: {vc['total_unique']}):")
            for item in vc['results']:
                logger.info(f"  {item['value']}: {item['count']} ({item['percentage']}%)")
    except Exception as e:
        logger.debug(f"Value counts: {e}")
    
    # Test 2: GroupBy on categorical columns
    logger.info("\n[GROUP BY]")
    try:
        cat_cols = df.select_dtypes(include=['object']).columns.tolist()
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if cat_cols and num_cols:
            group_col = cat_cols[0]
            agg_col = num_cols[0]
            result = agg.groupby_single(group_col, agg_col, "sum")
            logger.info(f"GroupBy '{group_col}' sum '{agg_col}':")
            for item in result['results'][:5]:
                logger.info(f"  {item}")
    except Exception as e:
        logger.debug(f"GroupBy: {e}")
    
    # Test 3: Summary statistics
    logger.info("\n[SUMMARY STATS]")
    try:
        cat_cols = df.select_dtypes(include=['object']).columns.tolist()
        if cat_cols:
            col = cat_cols[0]
            stats = agg.summary_statistics(col)
            if stats['status'] == 'success':
                logger.info(f"Summary stats grouped by '{col}' ({stats['groups']} groups):")
                for group_name in list(stats['statistics'].keys())[:2]:
                    logger.info(f"  {group_name}: stats computed")
    except Exception as e:
        logger.debug(f"Summary stats: {e}")
    
    # Test 4: Pivot table
    logger.info("\n[PIVOT TABLE]")
    try:
        cat_cols = df.select_dtypes(include=['object']).columns.tolist()
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if len(cat_cols) >= 2 and num_cols:
            result = agg.pivot_table(cat_cols[0], cat_cols[1], num_cols[0], "sum")
            logger.info(f"Pivot table shape: {result['shape']}")
    except Exception as e:
        logger.debug(f"Pivot: {e}")


def main():
    logger.info("="*80)
    logger.info("AGGREGATOR - DATA AGGREGATION TEST")
    logger.info("="*80)
    
    data_dir = project_root / "data"
    files = sorted([f for f in data_dir.glob("*.csv") if f.name != 'sample_data.csv'])[:3]
    
    logger.info(f"Testing {len(files)} datasets...")
    
    for f in files:
        try:
            test_aggregations(f)
        except Exception as e:
            logger.error(f"Error: {e}")
    
    logger.info("\n" + "="*80)
    logger.info("[OK] Aggregator tests complete!")
    logger.info("="*80)


if __name__ == "__main__":
    main()
