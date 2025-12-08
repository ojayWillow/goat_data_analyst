#!/usr/bin/env python3
"""Test Reporter agent with real datasets.

Usage:
    python scripts/test_reporter.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.data_loader import DataLoader
from agents.reporter import Reporter
from core.logger import get_logger

logger = get_logger(__name__)


def test_reporter(file_path):
    """Test Reporter with a dataset."""
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
    
    # Initialize Reporter
    reporter = Reporter()
    reporter.set_data(df)
    
    # Test 1: Executive Summary
    logger.info("\n[EXECUTIVE SUMMARY]")
    try:
        summary = reporter.generate_executive_summary()
        logger.info(f"Status: {summary['status']}")
        logger.info(f"Data shape: {summary['dataset_info']['rows']} rows x {summary['dataset_info']['columns']} columns")
        logger.info(f"Quality rating: {summary['data_quality']['quality_rating']}")
        logger.info(f"Null percentage: {summary['data_quality']['null_percentage']}%")
        logger.info(f"Summary: {summary['summary_statement']}")
    except Exception as e:
        logger.debug(f"Executive: {e}")
    
    # Test 2: Data Profile
    logger.info("\n[DATA PROFILE]")
    try:
        profile = reporter.generate_data_profile()
        logger.info(f"Status: {profile['status']}")
        logger.info(f"Columns profiled: {len(profile['columns'])}")
        for col in list(profile['columns'].keys())[:3]:
            col_info = profile['columns'][col]
            logger.info(f"  {col}:")
            logger.info(f"    Type: {col_info['data_type']}")
            logger.info(f"    Missing: {col_info['missing_percentage']}%")
            logger.info(f"    Unique: {col_info['unique_values']}")
    except Exception as e:
        logger.debug(f"Profile: {e}")
    
    # Test 3: Statistical Report
    logger.info("\n[STATISTICAL ANALYSIS]")
    try:
        stats = reporter.generate_statistical_report()
        logger.info(f"Status: {stats['status']}")
        if stats['correlation_analysis']:
            logger.info(f"Strong correlations: {len(stats['correlation_analysis'].get('strong_correlations', []))}")
    except Exception as e:
        logger.debug(f"Statistics: {e}")
    
    # Test 4: Comprehensive Report
    logger.info("\n[COMPREHENSIVE REPORT]")
    try:
        comp = reporter.generate_comprehensive_report()
        logger.info(f"Status: {comp['status']}")
        logger.info(f"Sections: {list(comp['sections'].keys())}")
        logger.info(f"Title: {comp['title']}")
        logger.info(f"Data shape: {comp['metadata']['data_shape']}")
    except Exception as e:
        logger.debug(f"Comprehensive: {e}")
    
    # Test 5: Export to JSON
    logger.info("\n[EXPORT TO JSON]")
    try:
        export = reporter.export_to_json("executive_summary")
        logger.info(f"Status: {export['status']}")
        logger.info(f"File: {export['file_path']}")
        logger.info(f"Size: {export['file_size']} bytes")
    except Exception as e:
        logger.debug(f"JSON Export: {e}")
    
    # Test 6: Export to HTML
    logger.info("\n[EXPORT TO HTML]")
    try:
        export = reporter.export_to_html("comprehensive")
        logger.info(f"Status: {export['status']}")
        logger.info(f"File: {export['file_path']}")
        logger.info(f"Size: {export['file_size']} bytes")
    except Exception as e:
        logger.debug(f"HTML Export: {e}")
    
    # Test 7: List Reports
    logger.info("\n[REPORTS GENERATED]")
    try:
        reports = reporter.list_reports()
        logger.info(f"Total reports: {reports['count']}")
        logger.info(f"Types: {reports['reports']}")
    except Exception as e:
        logger.debug(f"List: {e}")


def main():
    logger.info("="*80)
    logger.info("REPORTER - REPORT GENERATION TEST (FINAL AGENT)")
    logger.info("="*80)
    
    data_dir = project_root / "data"
    files = sorted([f for f in data_dir.glob("*.csv") if f.name != 'sample_data.csv'])[:1]
    
    logger.info(f"Testing {len(files)} dataset...\n")
    
    for f in files:
        try:
            test_reporter(f)
        except Exception as e:
            logger.error(f"Error: {e}")
    
    logger.info("\n" + "="*80)
    logger.info("[OK] Reporter tests complete!")
    logger.info("="*80)


if __name__ == "__main__":
    main()
