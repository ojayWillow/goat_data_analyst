#!/usr/bin/env python3
"""Comprehensive data analysis script for all datasets in data/ folder.

Analyzes all CSV files and displays:
- File size and row/column counts
- Data types and null values
- Sample data preview
- Memory usage

Usage:
    python scripts/analyze_all_data.py
"""

import sys
from pathlib import Path
import pandas as pd
from tabulate import tabulate

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.data_loader import DataLoader
from core.logger import get_logger

logger = get_logger(__name__)


def format_size(bytes_size):
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} TB"


def main():
    """Analyze all data files."""
    logger.info("="*80)
    logger.info("COMPREHENSIVE DATA ANALYSIS")
    logger.info("="*80)
    
    data_dir = project_root / "data"
    csv_files = sorted(data_dir.glob("*.csv"))
    
    if not csv_files:
        logger.error("No CSV files found in data/ directory")
        return
    
    logger.info(f"Found {len(csv_files)} CSV files\n")
    
    # Summary table
    summary_data = []
    loader = DataLoader()
    
    for i, file_path in enumerate(csv_files, 1):
        logger.info(f"[{i}/{len(csv_files)}] Processing: {file_path.name}")
        
        try:
            # Load data
            result = loader.load(str(file_path))
            
            if result["status"] != "success":
                logger.error(f"  Failed to load: {result.get('message', 'Unknown error')}")
                continue
            
            # Get metadata
            meta = loader.get_metadata()
            df = loader.get_data()
            
            # Get null statistics
            null_count = df.isnull().sum().sum()
            null_pct = (null_count / (df.shape[0] * df.shape[1]) * 100) if (df.shape[0] * df.shape[1]) > 0 else 0
            
            # Add to summary
            summary_data.append([
                file_path.name,
                meta['rows'],
                meta['columns'],
                format_size(file_path.stat().st_size),
                f"{meta['memory_usage_mb']:.2f} MB",
                null_count,
                f"{null_pct:.2f}%",
                meta['duplicates'],
            ])
            
            logger.info(f"  [OK] Rows: {meta['rows']:,} | Columns: {meta['columns']} | Size: {format_size(file_path.stat().st_size)}")
            logger.info(f"  [OK] Memory: {meta['memory_usage_mb']:.2f} MB | Nulls: {null_count:,} ({null_pct:.2f}%) | Duplicates: {meta['duplicates']}")
            logger.info()
            
        except Exception as e:
            logger.error(f"  [ERROR] {str(e)}")
            logger.info()
            continue
    
    # Display summary table
    logger.info("="*80)
    logger.info("SUMMARY TABLE")
    logger.info("="*80)
    
    headers = [
        "Filename",
        "Rows",
        "Columns",
        "File Size",
        "Memory",
        "Null Count",
        "Null %",
        "Duplicates",
    ]
    
    table_output = tabulate(summary_data, headers=headers, tablefmt="grid")
    logger.info(table_output)
    logger.info()
    
    # Detailed analysis for each file
    logger.info("="*80)
    logger.info("DETAILED ANALYSIS")
    logger.info("="*80)
    
    for file_path in csv_files[:5]:  # Detailed analysis for first 5 files
        logger.info(f"\n[FILE] {file_path.name}")
        logger.info("-" * 80)
        
        try:
            result = loader.load(str(file_path))
            if result["status"] != "success":
                continue
            
            meta = loader.get_metadata()
            df = loader.get_data()
            
            # Column information
            logger.info("Columns:")
            col_info = []
            for col in df.columns[:10]:  # Show first 10 columns
                dtype = meta['dtypes'][col]
                null_pct = meta['columns_info'][col]['null_percentage']
                non_null = meta['columns_info'][col]['non_null_count']
                col_info.append([col, dtype, non_null, f"{null_pct:.1f}%"])
            
            col_table = tabulate(col_info, headers=["Column", "Type", "Non-Null", "Null %"], tablefmt="simple")
            logger.info(col_table)
            
            # Sample data
            logger.info("\nSample Data (first 3 rows):")
            sample = loader.get_sample(n_rows=3)
            for j, row in enumerate(sample['sample'], 1):
                logger.info(f"  Row {j}: {row}")
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path.name}: {e}")
    
    logger.info("\n" + "="*80)
    logger.info("[OK] Analysis complete!")
    logger.info("="*80)


if __name__ == "__main__":
    main()
