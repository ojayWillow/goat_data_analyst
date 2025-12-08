#!/usr/bin/env python3
"""Test Recommender agent with real datasets.

Usage:
    python scripts/test_recommender.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.data_loader import DataLoader
from agents.recommender import Recommender
from core.logger import get_logger

logger = get_logger(__name__)


def test_recommendations(file_path):
    """Test Recommender with a dataset."""
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
    
    # Initialize Recommender
    rec = Recommender()
    rec.set_data(df)
    
    # Test 1: Summary Insights
    logger.info("\n[SUMMARY INSIGHTS]")
    try:
        summary = rec.get_summary_insights()
        logger.info("Dataset Summary:")
        for insight in summary['insights']:
            msg = f"  {insight['metric']}: {insight['value']}"
            if 'percentage' in insight:
                msg += f" ({insight['percentage']})"
            logger.info(msg)
    except Exception as e:
        logger.debug(f"Summary: {e}")
    
    # Test 2: Missing Data Analysis
    logger.info("\n[MISSING DATA ANALYSIS]")
    try:
        missing = rec.analyze_missing_data()
        logger.info(f"Status: {missing['status']}")
        logger.info(f"Null percentage: {missing['null_percentage']}%")
        logger.info(f"Insights: {len(missing['insights'])}")
        for insight in missing['insights'][:2]:
            logger.info(f"  - {insight['message']} [{insight['severity']}]")
        if missing['recommendations']:
            logger.info(f"Recommendations: {len(missing['recommendations'])}")
    except Exception as e:
        logger.debug(f"Missing: {e}")
    
    # Test 3: Duplicate Analysis
    logger.info("\n[DUPLICATE ANALYSIS]")
    try:
        dupes = rec.analyze_duplicates()
        logger.info(f"Status: {dupes['status']}")
        logger.info(f"Duplicates: {dupes['duplicate_count']} ({dupes['duplicate_percentage']}%)")
        logger.info(f"Insights: {len(dupes['insights'])}")
        for insight in dupes['insights']:
            logger.info(f"  - {insight['message']}")
    except Exception as e:
        logger.debug(f"Dupes: {e}")
    
    # Test 4: Distribution Analysis
    logger.info("\n[DISTRIBUTION ANALYSIS]")
    try:
        dist = rec.analyze_distributions()
        logger.info(f"Status: {dist['status']}")
        logger.info(f"Columns analyzed: {dist['columns_analyzed']}")
        logger.info(f"Insights: {len(dist['insights'])}")
        for insight in dist['insights'][:3]:
            logger.info(f"  - {insight['message']}")
    except Exception as e:
        logger.debug(f"Distribution: {e}")
    
    # Test 5: Correlation Analysis
    logger.info("\n[CORRELATION ANALYSIS]")
    try:
        corr = rec.analyze_correlations()
        if corr['status'] == 'success':
            logger.info(f"Status: {corr['status']}")
            logger.info(f"Strong correlations: {corr['strong_correlations']}")
            logger.info(f"Insights: {len(corr['insights'])}")
            for insight in corr['insights'][:2]:
                logger.info(f"  - {insight['message']}")
    except Exception as e:
        logger.debug(f"Correlation: {e}")
    
    # Test 6: Action Plan
    logger.info("\n[ACTION PLAN]")
    try:
        plan = rec.generate_action_plan()
        logger.info(f"Status: {plan['status']}")
        logger.info(f"Total actions: {plan['total_actions']}")
        logger.info(f"Data shape: {plan['data_shape']}")
        if plan['actions']:
            logger.info("Top 3 Priority Actions:")
            for i, action in enumerate(plan['actions'][:3], 1):
                logger.info(f"  {i}. [{action['action'].upper()}] {action['suggestion']}")
    except Exception as e:
        logger.debug(f"Plan: {e}")


def main():
    logger.info("="*80)
    logger.info("RECOMMENDER - INSIGHTS AND RECOMMENDATIONS TEST")
    logger.info("="*80)
    
    data_dir = project_root / "data"
    files = sorted([f for f in data_dir.glob("*.csv") if f.name != 'sample_data.csv'])[:2]
    
    logger.info(f"Testing {len(files)} datasets...\n")
    
    for f in files:
        try:
            test_recommendations(f)
        except Exception as e:
            logger.error(f"Error: {e}")
    
    logger.info("\n" + "="*80)
    logger.info("[OK] Recommender tests complete!")
    logger.info("="*80)


if __name__ == "__main__":
    main()
