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
    logger.info(f"✓ {loader.name} initialized\n")
    
    # Test 1: Load sample CSV
    logger.info("Test 1: Loading sample CSV file...")
    sample_csv = project_root / "data" / "sample_data.csv"
    
    if not sample_csv.exists():
        logger.error(f"❌ Sample CSV not found: {sample_csv}")
        return
    
    try:
        result = loader.load(str(sample_csv))
        logger.info(f"✓ {result['message']}")
        logger.info(f"✓ Status: {result['status']}\n")
    except Exception as e:
        logger.error(f"❌ Error loading CSV: {e}")
        return
    
    # Test 2: Get metadata
    logger.info("Test 2: Extracting metadata...")
    try:
        metadata = loader.get_metadata()
        logger.info(f"✓ File: {metadata['file_name']}")
        logger.info(f"✓ Rows: {metadata['rows']}")
        logger.info(f"✓ Columns: {metadata['columns']}")
        logger.info(f"✓ Column Names: {metadata['column_names']}")
        logger.info(f"✓ File Size: {metadata['file_size_mb']} MB")
        logger.info(f"✓ Duplicates: {metadata['duplicates']}\n")
    except Exception as e:
        logger.error(f"❌ Error getting metadata: {e}")
        return
    
    # Test 3: Get sample data
    logger.info("Test 3: Retrieving sample data...")
    try:
        sample = loader.get_sample(n_rows=3)
        logger.info(f"✓ Retrieved {len(sample['sample'])} sample rows")
        logger.info(f"✓ Total rows in dataset: {sample['total_rows']}\n")
        logger.info("Sample data:")
        for row in sample['sample']:
            logger.info(f"  {row}")
        logger.info()
    except Exception as e:
        logger.error(f"❌ Error getting sample: {e}")
        return
    
    # Test 4: Get data info
    logger.info("Test 4: Getting data information...")
    try:
        info = loader.get_info()
        logger.info(f"✓ Data types:")
        for col, dtype in info['data_types'].items():
            logger.info(f"    {col}: {dtype}")
        logger.info()
    except Exception as e:
        logger.error(f"❌ Error getting info: {e}")
        return
    
    # Test 5: Validate columns
    logger.info("Test 5: Validating required columns...")
    try:
        required_cols = ['date', 'product', 'sales']
        result = loader.validate_columns(required_cols)
        logger.info(f"✓ Required columns: {result['required_columns']}")
        logger.info(f"✓ Valid: {result['valid']}")
        if result['missing_columns']:
            logger.warning(f"⚠ Missing columns: {result['missing_columns']}")
        else:
            logger.info(f"✓ All required columns present\n")
    except Exception as e:
        logger.error(f"❌ Error validating columns: {e}")
        return
    
    # Test 6: Try to validate non-existent columns
    logger.info("Test 6: Validating non-existent columns...")
    try:
        required_cols = ['date', 'product', 'revenue', 'cost']
        result = loader.validate_columns(required_cols)
        logger.info(f"✓ Required columns: {result['required_columns']}")
        logger.info(f"✓ Valid: {result['valid']}")
        logger.warning(f"⚠ Missing columns: {result['missing_columns']}\n")
    except Exception as e:
        logger.error(f"❌ Error validating columns: {e}")
        return
    
    logger.info("="*60)
    logger.info("✓ All tests completed successfully!")
    logger.info("="*60)


if __name__ == "__main__":
    main()
