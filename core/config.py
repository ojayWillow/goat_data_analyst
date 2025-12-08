"""Configuration management for GOAT Data Analyst."""

import os
from pathlib import Path
from typing import Optional
import yaml
from dotenv import load_dotenv


class Config:
    """Application configuration manager."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_file: Path to YAML config file. Defaults to config/config.yml
        """
        # Load environment variables
        load_dotenv()
        
        # Set default config file
        if config_file is None:
            config_file = Path(__file__).parent.parent / "config" / "config.yml"
        
        self.config_file = Path(config_file)
        self.config = self._load_config()
        
    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    @property
    def app_name(self) -> str:
        """Application name."""
        return os.getenv('APP_NAME', self.config.get('app', {}).get('name', 'GOAT Data Analyst'))
    
    @property
    def app_version(self) -> str:
        """Application version."""
        return self.config.get('app', {}).get('version', '1.0.0')
    
    @property
    def debug(self) -> bool:
        """Debug mode."""
        return os.getenv('APP_DEBUG', 'false').lower() == 'true'
    
    @property
    def log_level(self) -> str:
        """Logging level."""
        return os.getenv('APP_LOG_LEVEL', self.config.get('app', {}).get('log_level', 'INFO'))
    
    @property
    def database_url(self) -> str:
        """Database connection URL."""
        return os.getenv('DATABASE_URL', self.config.get('database', {}).get('url', 'sqlite:///data/analyst.db'))
    
    @property
    def api_host(self) -> str:
        """API host."""
        return os.getenv('API_HOST', self.config.get('api', {}).get('host', '0.0.0.0'))
    
    @property
    def api_port(self) -> int:
        """API port."""
        return int(os.getenv('API_PORT', self.config.get('api', {}).get('port', 8000)))
    
    @property
    def ui_theme(self) -> str:
        """UI theme."""
        return os.getenv('UI_THEME', self.config.get('ui', {}).get('theme', 'light'))
    
    def get(self, key: str, default: any = None) -> any:
        """Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
