#!/usr/bin/env python3
"""Generate comprehensive data report and save to file.

Creates a detailed report of all datasets including:
- Summary statistics
- Column analysis
- Data quality metrics
- Sample data preview

Output: reports/data_analysis_report.txt

Usage:
    python scripts/generate_data_report.py
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

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
    """Generate data analysis report."""
    # Create reports directory
    reports_dir = project_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    report_file = reports_dir / "data_analysis_report.txt"
    
    logger.info(f"Generating report: {report_file}")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("="*100 + "\n")
        f.write("DATA ANALYSIS REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*100 + "\n\n")
        
        # Get all CSV files
        data_dir = project_root / "data"
        csv_files = sorted(data_dir.glob("*.csv"))
        
        f.write(f"Total Files Found: {len(csv_files)}\n\n")
        
        loader = DataLoader()
        file_count = 0
        total_rows = 0
        total_columns = 0
        
        # Process each file
        for i, file_path in enumerate(csv_files, 1):
            logger.info(f"Processing [{i}/{len(csv_files)}]: {file_path.name}")
            
            try:
                # Load data
                result = loader.load(str(file_path))
                
                if result["status"] != "success":
                    f.write(f"[ERROR] {file_path.name}: {result.get('message', 'Unknown error')}\n\n")
                    continue
                
                file_count += 1
                meta = loader.get_metadata()
                df = loader.get_data()
                
                total_rows += meta['rows']
                total_columns += meta['columns']
                
                # File summary
                f.write("="*100 + "\n")
                f.write(f"FILE: {file_path.name}\n")
                f.write("="*100 + "\n")
                f.write(f"File Size: {format_size(file_path.stat().st_size)}\n")
                f.write(f"Rows: {meta['rows']:,}\n")
                f.write(f"Columns: {meta['columns']}\n")
                f.write(f"Memory Usage: {meta['memory_usage_mb']:.2f} MB\n")
                
                # Data quality
                null_count = df.isnull().sum().sum()
                null_pct = (null_count / (df.shape[0] * df.shape[1]) * 100) if (df.shape[0] * df.shape[1]) > 0 else 0
                f.write(f"\nData Quality:\n")
                f.write(f"  Null Values: {null_count:,} ({null_pct:.2f}%)\n")
                f.write(f"  Duplicates: {meta['duplicates']}\n")
                f.write(f"  Duplicate Percentage: {meta['duplicate_percentage']:.2f}%\n")
                
                # Column information
                f.write(f"\nColumn Details:\n")
                f.write("-" * 100 + "\n")
                f.write(f"{'Column Name':<30} {'Type':<15} {'Non-Null':<15} {'Null %':<10}\n")
                f.write("-" * 100 + "\n")
                
                for col in df.columns:
                    col_info = meta['columns_info'][col]
                    col_type = meta['dtypes'][col]
                    null_pct_col = col_info['null_percentage']
                    non_null = col_info['non_null_count']
                    f.write(f"{col:<30} {col_type:<15} {non_null:<15} {null_pct_col:<10.2f}\n")
                
                # Sample data
                f.write(f"\nSample Data (First 3 Rows):\n")
                f.write("-" * 100 + "\n")
                sample = loader.get_sample(n_rows=3)
                for j, row in enumerate(sample['sample'], 1):
                    f.write(f"Row {j}:\n")
                    for key, value in row.items():
                        f.write(f"  {key}: {value}\n")
                    f.write("\n")
                
                f.write("\n" + "="*100 + "\n\n")
                
            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")
                f.write(f"[ERROR] {file_path.name}: {str(e)}\n\n")
        
        # Summary statistics
        f.write("="*100 + "\n")
        f.write("SUMMARY STATISTICS\n")
        f.write("="*100 + "\n")
        f.write(f"Files Successfully Processed: {file_count}\n")
        f.write(f"Total Rows Analyzed: {total_rows:,}\n")
        f.write(f"Total Columns Analyzed: {total_columns}\n")
        if file_count > 0:
            f.write(f"Average Rows per File: {total_rows // file_count:,}\n")
            f.write(f"Average Columns per File: {total_columns // file_count}\n")
        f.write(f"\nReport Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    logger.info(f"[OK] Report saved to: {report_file}")
    logger.info(f"[OK] Open with: notepad {report_file}")
    
    # Also print to console
    print(f"\n[OK] Report generated successfully!")
    print(f"Location: {report_file}")
    print(f"\nTo view the report:")
    print(f"  notepad {report_file}")
    print(f"  or")
    print(f"  code {report_file}")


if __name__ == "__main__":
    main()
