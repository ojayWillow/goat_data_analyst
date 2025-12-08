#!/usr/bin/env python3
"""Generate and display data analysis reports.

Generates reports and opens them in the default viewer.

Usage:
    python scripts/generate_and_show_report.py
"""

import sys
import json
from pathlib import Path
import subprocess
import os

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.data_loader import DataLoader
from agents.reporter import Reporter
from core.logger import get_logger

logger = get_logger(__name__)


def main():
    logger.info("\n" + "="*80)
    logger.info("GENERATE AND DISPLAY REPORTS")
    logger.info("="*80)
    
    # Find data file
    data_dir = project_root / "data"
    csv_files = sorted([f for f in data_dir.glob("*.csv") if f.name != 'sample_data.csv'])
    
    if not csv_files:
        logger.error("No data files found")
        return
    
    data_file = str(csv_files[0])
    logger.info(f"\nLoading: {Path(data_file).name}")
    
    # Load data
    loader = DataLoader()
    result = loader.load(data_file)
    
    if result["status"] != "success":
        logger.error("Failed to load data")
        return
    
    df = result["data"]
    logger.info(f"Loaded: {df.shape[0]:,} rows x {df.shape[1]} columns")
    
    # Initialize Reporter
    reporter = Reporter()
    reporter.set_data(df)
    
    # Generate reports
    logger.info("\n" + "-"*80)
    logger.info("Generating reports...")
    logger.info("-"*80)
    
    # 1. Executive Summary
    logger.info("\n[1/4] Executive Summary")
    try:
        summary = reporter.generate_executive_summary()
        logger.info("✓ Generated")
        
        logger.info("\n" + "="*80)
        logger.info("EXECUTIVE SUMMARY")
        logger.info("="*80)
        logger.info(f"\nDataset Information:")
        logger.info(f"  Rows: {summary['dataset_info']['rows']:,}")
        logger.info(f"  Columns: {summary['dataset_info']['columns']}")
        logger.info(f"  Numeric columns: {summary['dataset_info']['numeric_columns']}")
        logger.info(f"  Categorical columns: {summary['dataset_info']['categorical_columns']}")
        
        logger.info(f"\nData Quality:")
        logger.info(f"  Rating: {summary['data_quality']['quality_rating']}")
        logger.info(f"  Null values: {summary['data_quality']['null_percentage']}%")
        logger.info(f"  Duplicates: {summary['data_quality']['duplicate_count']} rows ({summary['data_quality']['duplicate_percentage']}%)")
        
        logger.info(f"\nSummary:")
        logger.info(f"  {summary['summary_statement']}")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    # 2. Data Profile
    logger.info("\n[2/4] Data Profile")
    try:
        profile = reporter.generate_data_profile()
        logger.info("✓ Generated")
        
        logger.info("\n" + "="*80)
        logger.info("DATA PROFILE")
        logger.info("="*80)
        
        logger.info(f"\nColumn Analysis:")
        for i, (col, info) in enumerate(list(profile['columns'].items())[:5], 1):
            logger.info(f"\n  {i}. {col}")
            logger.info(f"     Type: {info['data_type']}")
            logger.info(f"     Missing: {info['missing_percentage']}%")
            logger.info(f"     Unique values: {info['unique_values']}")
            logger.info(f"     Completeness: {info['completeness']}%")
            
            if 'statistics' in info:
                stats = info['statistics']
                logger.info(f"     Stats: mean={stats.get('mean', 'N/A')}, median={stats.get('median', 'N/A')}, std={stats.get('std', 'N/A')}")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    # 3. Statistical Analysis
    logger.info("\n[3/4] Statistical Analysis")
    try:
        stats_report = reporter.generate_statistical_report()
        logger.info("✓ Generated")
        
        logger.info("\n" + "="*80)
        logger.info("STATISTICAL ANALYSIS")
        logger.info("="*80)
        
        if stats_report['correlation_analysis']:
            strong_corrs = stats_report['correlation_analysis'].get('strong_correlations', [])
            logger.info(f"\nStrong Correlations (|r| > 0.7): {len(strong_corrs)}")
            for corr in strong_corrs[:5]:
                logger.info(f"  {corr['col1']} <-> {corr['col2']}: {corr['correlation']:.3f}")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    # 4. Comprehensive Report
    logger.info("\n[4/4] Comprehensive Report")
    try:
        comp_report = reporter.generate_comprehensive_report()
        logger.info("✓ Generated")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    # Export to JSON
    logger.info("\n" + "-"*80)
    logger.info("Exporting Reports...")
    logger.info("-"*80)
    
    try:
        json_export = reporter.export_to_json("comprehensive")
        logger.info(f"\n✓ JSON Export: {json_export['file_path']}")
        logger.info(f"  Size: {json_export['file_size']} bytes")
    except Exception as e:
        logger.error(f"JSON Export Error: {e}")
    
    # Export to HTML
    try:
        html_export = reporter.export_to_html("comprehensive")
        logger.info(f"\n✓ HTML Export: {html_export['file_path']}")
        logger.info(f"  Size: {html_export['file_size']} bytes")
        
        # Try to open HTML in default browser
        html_file = html_export['file_path']
        logger.info(f"\n" + "="*80)
        logger.info("Opening HTML report...")
        logger.info("="*80)
        
        if os.name == 'nt':  # Windows
            try:
                os.startfile(html_file)
                logger.info(f"\n✓ Opened: {html_file}")
            except Exception as e:
                logger.info(f"\nTo view the report, open: {html_file}")
        else:  # Mac/Linux
            try:
                subprocess.Popen(['open', html_file])
                logger.info(f"\n✓ Opened: {html_file}")
            except Exception as e:
                logger.info(f"\nTo view the report, open: {html_file}")
    except Exception as e:
        logger.error(f"HTML Export Error: {e}")
    
    # Summary of generated files
    logger.info("\n" + "="*80)
    logger.info("REPORT GENERATION COMPLETE")
    logger.info("="*80)
    logger.info("\nGenerated Files:")
    logger.info(f"  1. JSON Report: report_comprehensive_*.json")
    logger.info(f"  2. HTML Report: report_comprehensive_*.html (opened in browser)")
    logger.info(f"\nFiles are saved in: {project_root}")
    logger.info("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
