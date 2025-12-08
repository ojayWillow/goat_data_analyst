#!/usr/bin/env python3
"""Quick test script for DataLoader agent.

Usage:
    python scripts/test_data_loader.py
"""

import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.data_loader import DataLoader
from core.logger import get_logger

logger = get_logger(__name__)


def main():
    """Test DataLoader with sample data."""
    logger.info("="*60)
    logger.info("Testing DataLoader Agent")
    logger.info("="*60)
    
    # Create DataLoader instance
    loader = DataLoader()
    logger.info(f"[OK] {loader.name} initialized\n")
    
    # Test 1: Load sample CSV
    logger.info("Test 1: Loading sample CSV file...")
    sample_csv = project_root / "data" / "sample_data.csv"
    
    if not sample_csv.exists():
        logger.error(f"[ERROR] Sample CSV not found: {sample_csv}")
        return
    
    try:
        result = loader.load(str(sample_csv))
        logger.info(f"[OK] {result['message']}")
        logger.info(f"[OK] Status: {result['status']}\n")
    except Exception as e:
        logger.error(f"[ERROR] Error loading CSV: {e}")
        return
    
    # Test 2: Get metadata
    logger.info("Test 2: Extracting metadata...")
    try:
        metadata = loader.get_metadata()
        logger.info(f"[OK] File: {metadata['file_name']}")
        logger.info(f"[OK] Rows: {metadata['rows']}")
        logger.info(f"[OK] Columns: {metadata['columns']}")
        logger.info(f"[OK] Column Names: {metadata['column_names']}")
        logger.info(f"[OK] File Size: {metadata['file_size_mb']} MB")
        logger.info(f"[OK] Duplicates: {metadata['duplicates']}\n")
    except Exception as e:
        logger.error(f"[ERROR] Error getting metadata: {e}")
        return
    
    # Test 3: Get sample data
    logger.info("Test 3: Retrieving sample data...")
    try:
        sample = loader.get_sample(n_rows=3)
        logger.info(f"[OK] Retrieved {len(sample['sample'])} sample rows")
        logger.info(f"[OK] Total rows in dataset: {sample['total_rows']}")
        logger.info("Sample data:")
        for row in sample['sample']:
            logger.info(f"  {row}")
        logger.info("" )
    except Exception as e:
        logger.error(f"[ERROR] Error getting sample: {e}")
        return
    
    # Test 4: Get data info
    logger.info("Test 4: Getting data information...")
    try:
        info = loader.get_info()
        logger.info(f"[OK] Data types:")
        for col, dtype in info['data_types'].items():
            logger.info(f"    {col}: {dtype}")
        logger.info("")
    except Exception as e:
        logger.error(f"[ERROR] Error getting info: {e}")
        return
    
    # Test 5: Validate columns
    logger.info("Test 5: Validating required columns...")
    try:
        required_cols = ['date', 'product', 'sales']
        result = loader.validate_columns(required_cols)
        logger.info(f"[OK] Required columns: {result['required_columns']}")
        logger.info(f"[OK] Valid: {result['valid']}")
        if result['missing_columns']:
            logger.warning(f"[WARN] Missing columns: {result['missing_columns']}")
        else:
            logger.info(f"[OK] All required columns present\n")
    except Exception as e:
        logger.error(f"[ERROR] Error validating columns: {e}")
        return
    
    # Test 6: Try to validate non-existent columns
    logger.info("Test 6: Validating non-existent columns...")
    try:
        required_cols = ['date', 'product', 'revenue', 'cost']
        result = loader.validate_columns(required_cols)
        logger.info(f"[OK] Required columns: {result['required_columns']}")
        logger.info(f"[OK] Valid: {result['valid']}")
        logger.warning(f"[WARN] Missing columns: {result['missing_columns']}\n")
    except Exception as e:
        logger.error(f"[ERROR] Error validating columns: {e}")
        return
    
    logger.info("="*60)
    logger.info("[OK] All tests completed successfully!")
    logger.info("="*60)


if __name__ == "__main__":
    main()
