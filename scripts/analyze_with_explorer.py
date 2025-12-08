#!/usr/bin/env python3
"""Analyze real datasets using Explorer agent.

Usage:
    python scripts/analyze_with_explorer.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.data_loader import DataLoader
from agents.explorer import Explorer
from core.logger import get_logger

logger = get_logger(__name__)


def analyze_file(file_path):
    """Analyze a dataset with Explorer."""
    logger.info(f"\n[FILE] {file_path.name}")
    logger.info("-" * 80)
    
    loader = DataLoader()
    result = loader.load(str(file_path))
    
    if result["status"] != "success":
        logger.error(f"Failed to load")
        return
    
    logger.info(f"Rows: {result['data'].shape[0]:,} | Columns: {result['data'].shape[1]}")
    
    explorer = Explorer()
    explorer.set_data(result["data"])
    
    # Numeric stats
    try:
        stats = explorer.describe_numeric()
        if stats['status'] == 'success':
            logger.info(f"\nNumeric columns: {len(stats['statistics'])}")
            for col in list(stats['statistics'].keys())[:3]:
                s = stats['statistics'][col]
                logger.info(f"  {col}: mean={s['mean']:.1f}, median={s['median']:.1f}, std={s['std']:.1f}")
    except: pass
    
    # Categorical stats
    try:
        stats = explorer.describe_categorical()
        if stats['status'] == 'success':
            logger.info(f"\nCategorical columns: {len(stats['statistics'])}")
            for col in list(stats['statistics'].keys())[:2]:
                s = stats['statistics'][col]
                logger.info(f"  {col}: unique={s['unique_values']}, top={s['most_common']}")
    except: pass
    
    # Quality
    try:
        quality = explorer.data_quality_assessment()
        logger.info(f"\nQuality: {quality['overall_quality_score']:.0f}/100 ({quality['quality_rating']})")
        logger.info(f"Nulls: {quality['null_percentage']:.1f}% | Duplicates: {quality['duplicate_percentage']:.1f}%")
    except: pass


def main():
    logger.info("="*80)
    logger.info("EXPLORER - REAL DATA ANALYSIS")
    logger.info("="*80)
    
    data_dir = project_root / "data"
    files = sorted([f for f in data_dir.glob("*.csv") if f.name != 'sample_data.csv'])[:5]
    
    logger.info(f"Analyzing {len(files)} datasets...")
    
    for f in files:
        try:
            analyze_file(f)
        except Exception as e:
            logger.error(f"Error: {e}")
    
    logger.info("\n" + "="*80)
    logger.info("[OK] Analysis complete!")
    logger.info("="*80)


if __name__ == "__main__":
    main()
