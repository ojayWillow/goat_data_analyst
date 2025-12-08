#!/usr/bin/env python3
"""GOAT Data Analyst - Main Entry Point."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.logger import get_logger
from core.config import Config

logger = get_logger(__name__)


def main():
    """Main application entry point."""
    try:
        logger.info("Starting GOAT Data Analyst...")
        config = Config()
        logger.info(f"Config loaded: {config.app_name} v{config.app_version}")
        
        # TODO: Initialize database
        # TODO: Start API server
        # TODO: Launch UI
        
        logger.info("Application ready!")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
