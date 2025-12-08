#!/usr/bin/env python3
"""Test Anomaly Detector agent with real datasets.

Usage:
    python scripts/test_anomaly_detector.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.data_loader import DataLoader
from agents.anomaly_detector import AnomalyDetector
from core.logger import get_logger

logger = get_logger(__name__)


def test_anomaly_detection(file_path):
    """Test Anomaly Detector with a dataset."""
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
    
    # Initialize Anomaly Detector
    detector = AnomalyDetector()
    detector.set_data(df)
    
    # Test 1: IQR Detection
    logger.info("\n[IQR DETECTION]")
    try:
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        if num_cols:
            col = num_cols[0]
            result = detector.iqr_detection(col, multiplier=1.5)
            logger.info(f"IQR detection for '{col}':")
            logger.info(f"  Lower bound: {result['bounds']['lower']:.2f}")
            logger.info(f"  Upper bound: {result['bounds']['upper']:.2f}")
            logger.info(f"  Outliers: {result['outliers_count']} ({result['outliers_percentage']}%)")
            logger.info(f"  Lower outliers: {result['lower_outliers_count']}")
            logger.info(f"  Upper outliers: {result['upper_outliers_count']}")
    except Exception as e:
        logger.debug(f"IQR: {e}")
    
    # Test 2: Z-Score Detection
    logger.info("\n[Z-SCORE DETECTION]")
    try:
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        if num_cols:
            col = num_cols[0]
            result = detector.zscore_detection(col, threshold=3.0)
            if result['status'] == 'success':
                logger.info(f"Z-score detection for '{col}':")
                logger.info(f"  Mean: {result['statistics']['mean']:.2f}")
                logger.info(f"  Std: {result['statistics']['std']:.2f}")
                logger.info(f"  Outliers: {result['outliers_count']} ({result['outliers_percentage']}%)")
                logger.info(f"  Z-score range: {result['z_score_range']}")
    except Exception as e:
        logger.debug(f"Z-score: {e}")
    
    # Test 3: Modified Z-Score Detection
    logger.info("\n[MODIFIED Z-SCORE DETECTION]")
    try:
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        if num_cols:
            col = num_cols[0]
            result = detector.modified_zscore_detection(col, threshold=3.5)
            if result['status'] == 'success':
                logger.info(f"Modified Z-score detection for '{col}':")
                logger.info(f"  Median: {result['statistics']['median']:.2f}")
                logger.info(f"  MAD: {result['statistics']['mad']:.2f}")
                logger.info(f"  Outliers: {result['outliers_count']} ({result['outliers_percentage']}%)")
    except Exception as e:
        logger.debug(f"Modified Z-score: {e}")
    
    # Test 4: Isolation Forest Detection
    logger.info("\n[ISOLATION FOREST DETECTION]")
    try:
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        if len(num_cols) >= 2:
            result = detector.isolation_forest_detection(num_cols, contamination=0.1)
            if result['status'] == 'success':
                logger.info(f"Isolation Forest detection:")
                logger.info(f"  Samples: {result['total_samples']}")
                logger.info(f"  Anomalies: {result['anomalies_count']} ({result['anomalies_percentage']}%)")
                logger.info(f"  Score range: {result['anomaly_score_range']}")
    except Exception as e:
        logger.debug(f"Isolation Forest: {e}")
    
    # Test 5: Multivariate Analysis
    logger.info("\n[MULTIVARIATE ANALYSIS (Mahalanobis)]")
    try:
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        if len(num_cols) >= 2:
            result = detector.multivariate_analysis(num_cols)
            if result['status'] == 'success':
                logger.info(f"Mahalanobis distance analysis:")
                logger.info(f"  Samples: {result['samples']}")
                logger.info(f"  Threshold: {result['distance_threshold']:.2f}")
                logger.info(f"  Outliers: {result['outliers_count']} ({result['outliers_percentage']}%)")
                logger.info(f"  Distance mean: {result['distance_statistics']['mean']:.2f}")
                logger.info(f"  Distance std: {result['distance_statistics']['std']:.2f}")
    except Exception as e:
        logger.debug(f"Multivariate: {e}")
    
    # Test 6: Summary Report
    logger.info("\n[ANOMALY SUMMARY]")
    try:
        report = detector.summary_report()
        logger.info(f"Total analyses: {report['total_analyses']}")
        logger.info(f"Methods used: {report['methods_used']}")
    except Exception as e:
        logger.debug(f"Summary: {e}")


def main():
    logger.info("="*80)
    logger.info("ANOMALY DETECTOR - OUTLIER DETECTION TEST")
    logger.info("="*80)
    
    data_dir = project_root / "data"
    files = sorted([f for f in data_dir.glob("*.csv") if f.name != 'sample_data.csv'])[:2]
    
    logger.info(f"Testing {len(files)} datasets...\n")
    
    for f in files:
        try:
            test_anomaly_detection(f)
        except Exception as e:
            logger.error(f"Error: {e}")
    
    logger.info("\n" + "="*80)
    logger.info("[OK] Anomaly Detector tests complete!")
    logger.info("="*80)


if __name__ == "__main__":
    main()
