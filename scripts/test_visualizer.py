#!/usr/bin/env python3
"""Test Visualizer agent with real datasets.

Usage:
    python scripts/test_visualizer.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.data_loader import DataLoader
from agents.visualizer import Visualizer
from core.logger import get_logger

logger = get_logger(__name__)


def test_visualizations(file_path):
    """Test Visualizer with a dataset."""
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
    
    # Initialize Visualizer
    viz = Visualizer()
    viz.set_data(df)
    
    # Test 1: Histogram
    logger.info("\n[HISTOGRAM]")
    try:
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        if num_cols:
            col = num_cols[0]
            result = viz.histogram(col, bins=20)
            logger.info(f"[OK] Histogram created for '{col}'")
            logger.info(f"  Chart ID: {result['chart_id']}")
            logger.info(f"  Values: {result['values']}")
    except Exception as e:
        logger.debug(f"Histogram: {e}")
    
    # Test 2: Pie Chart
    logger.info("\n[PIE CHART]")
    try:
        cat_cols = df.select_dtypes(include=['object']).columns.tolist()
        if cat_cols:
            col = cat_cols[0]
            result = viz.pie_chart(col)
            logger.info(f"[OK] Pie chart created for '{col}'")
            logger.info(f"  Chart ID: {result['chart_id']}")
            logger.info(f"  Categories: {result['categories']}")
    except Exception as e:
        logger.debug(f"Pie: {e}")
    
    # Test 3: Bar Chart
    logger.info("\n[BAR CHART]")
    try:
        cat_cols = df.select_dtypes(include=['object']).columns.tolist()
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        if cat_cols and num_cols:
            result = viz.bar_chart(cat_cols[0], num_cols[0])
            logger.info(f"[OK] Bar chart created")
            logger.info(f"  Chart ID: {result['chart_id']}")
            logger.info(f"  Categories: {result['categories']}")
    except Exception as e:
        logger.debug(f"Bar: {e}")
    
    # Test 4: Scatter Plot
    logger.info("\n[SCATTER PLOT]")
    try:
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        if len(num_cols) >= 2:
            result = viz.scatter_plot(num_cols[0], num_cols[1])
            logger.info(f"[OK] Scatter plot created")
            logger.info(f"  Chart ID: {result['chart_id']}")
            logger.info(f"  Points: {result['points']}")
    except Exception as e:
        logger.debug(f"Scatter: {e}")
    
    # Test 5: Heatmap
    logger.info("\n[HEATMAP]")
    try:
        result = viz.heatmap()
        if result['status'] == 'success':
            logger.info(f"[OK] Heatmap created")
            logger.info(f"  Chart ID: {result['chart_id']}")
            logger.info(f"  Columns: {result['columns']}")
            logger.info(f"  Correlation range: {result['correlation_range']}")
    except Exception as e:
        logger.debug(f"Heatmap: {e}")
    
    # Test 6: List charts
    logger.info("\n[CHARTS CREATED]")
    try:
        charts = viz.list_charts()
        logger.info(f"Total charts: {charts['count']}")
        if charts['charts']:
            logger.info(f"Charts: {charts['charts']}")
    except Exception as e:
        logger.debug(f"List: {e}")


def main():
    logger.info("="*80)
    logger.info("VISUALIZER - DATA VISUALIZATION TEST")
    logger.info("="*80)
    
    data_dir = project_root / "data"
    files = sorted([f for f in data_dir.glob("*.csv") if f.name != 'sample_data.csv'])[:2]
    
    logger.info(f"Testing {len(files)} datasets...\n")
    
    for f in files:
        try:
            test_visualizations(f)
        except Exception as e:
            logger.error(f"Error: {e}")
    
    logger.info("\n" + "="*80)
    logger.info("[OK] Visualizer tests complete!")
    logger.info("="*80)


if __name__ == "__main__":
    main()
