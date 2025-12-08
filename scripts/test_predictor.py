#!/usr/bin/env python3
"""Test Predictor agent with real datasets.

Usage:
    python scripts/test_predictor.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.data_loader import DataLoader
from agents.predictor import Predictor
from core.logger import get_logger

logger = get_logger(__name__)


def test_predictions(file_path):
    """Test Predictor with a dataset."""
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
    
    # Initialize Predictor
    pred = Predictor()
    pred.set_data(df)
    
    # Test 1: Trend Analysis
    logger.info("\n[TREND ANALYSIS]")
    try:
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        if num_cols:
            col = num_cols[0]
            trend = pred.trend_analysis(col)
            logger.info(f"Trend for '{col}':")
            logger.info(f"  Direction: {trend['trend_direction']}")
            logger.info(f"  Change: {trend['percent_change']}%")
            logger.info(f"  Mean: {trend['statistics']['overall_mean']}")
            logger.info(f"  Std: {trend['statistics']['overall_std']}")
    except Exception as e:
        logger.debug(f"Trend: {e}")
    
    # Test 2: Moving Average
    logger.info("\n[MOVING AVERAGE]")
    try:
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        if num_cols:
            col = num_cols[0]
            ma = pred.moving_average(col, window=5)
            logger.info(f"Moving average for '{col}':")
            logger.info(f"  Window: {ma['window']}")
            logger.info(f"  Total values: {ma['values']}")
            logger.info(f"  MA available: {ma['ma_available']}")
    except Exception as e:
        logger.debug(f"MA: {e}")
    
    # Test 3: Exponential Smoothing
    logger.info("\n[EXPONENTIAL SMOOTHING]")
    try:
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        if num_cols:
            col = num_cols[0]
            smooth = pred.exponential_smoothing(col, alpha=0.3)
            logger.info(f"Exponential smoothing for '{col}':")
            logger.info(f"  Alpha: {smooth['alpha']}")
            logger.info(f"  Values: {smooth['values']}")
    except Exception as e:
        logger.debug(f"Smoothing: {e}")
    
    # Test 4: Linear Regression Forecast
    logger.info("\n[LINEAR REGRESSION FORECAST]")
    try:
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        if len(num_cols) >= 1:
            col = num_cols[0]
            forecast = pred.linear_regression_forecast('index', col, periods=5)
            if forecast['status'] == 'success':
                logger.info(f"Forecast for '{col}':")
                logger.info(f"  Training samples: {forecast['training_samples']}")
                logger.info(f"  R² Score: {forecast['metrics']['r2_score']:.4f}")
                logger.info(f"  RMSE: {forecast['metrics']['rmse']:.2f}")
                logger.info(f"  Slope: {forecast['slope']:.4f}")
    except Exception as e:
        logger.debug(f"Forecast: {e}")
    
    # Test 5: Random Forest
    logger.info("\n[RANDOM FOREST PREDICTION]")
    try:
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        if len(num_cols) >= 2:
            feature_cols = num_cols[:-1]
            target_col = num_cols[-1]
            rf = pred.random_forest_prediction(feature_cols, target_col, test_size=0.2)
            if rf['status'] == 'success':
                logger.info(f"Random Forest prediction:")
                logger.info(f"  Train size: {rf['train_size']} | Test size: {rf['test_size']}")
                logger.info(f"  Train R²: {rf['metrics']['train_r2']:.4f}")
                logger.info(f"  Test R²: {rf['metrics']['test_r2']:.4f}")
                logger.info(f"  Test RMSE: {rf['metrics']['test_rmse']:.2f}")
                logger.info(f"  Top features: {list(rf['feature_importance'].items())[:3]}")
    except Exception as e:
        logger.debug(f"RF: {e}")
    
    # Test 6: List Models
    logger.info("\n[MODELS TRAINED]")
    try:
        models = pred.list_models()
        logger.info(f"Total models: {models['count']}")
        if models['models']:
            logger.info(f"Models: {models['models']}")
    except Exception as e:
        logger.debug(f"List: {e}")


def main():
    logger.info("="*80)
    logger.info("PREDICTOR - FORECASTING AND PREDICTIONS TEST")
    logger.info("="*80)
    
    data_dir = project_root / "data"
    files = sorted([f for f in data_dir.glob("*.csv") if f.name != 'sample_data.csv'])[:2]
    
    logger.info(f"Testing {len(files)} datasets...\n")
    
    for f in files:
        try:
            test_predictions(f)
        except Exception as e:
            logger.error(f"Error: {e}")
    
    logger.info("\n" + "="*80)
    logger.info("[OK] Predictor tests complete!")
    logger.info("="*80)


if __name__ == "__main__":
    main()
