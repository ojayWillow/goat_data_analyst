"""DataManager Worker - Manages data caching and inter-agent data flow.

Responsibilities:
- Cache data for sharing between agents
- Retrieve cached data by key
- Validate data types
- Provide data access priority (provided > cached > loaded)
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from core.logger import get_logger
from core.structured_logger import get_structured_logger
from core.exceptions import DataLoadError


class DataManager:
    """Manages data caching and flow between agents.
    
    Implements a caching layer to share data between agents
    and provides priority-based data access patterns.
    """

    def __init__(self) -> None:
        """Initialize the DataManager."""
        self.name = "DataManager"
        self.logger = get_logger("DataManager")
        self.structured_logger = get_structured_logger("DataManager")
        self.cache: Dict[str, Any] = {}
        self.logger.info("DataManager initialized")

    def set(self, key: str, data: Any) -> None:
        """Cache data with a key.
        
        Args:
            key: Cache key
            data: Data to cache
        """
        try:
            self.cache[key] = data
            self.logger.info(f"Data cached: {key}")
            self.structured_logger.info("Data cached", {
                'cache_key': key,
                'data_type': type(data).__name__,
                'total_cached': len(self.cache)
            })
        except Exception as e:
            self.logger.error(f"Error caching data: {e}")
            raise DataLoadError(f"Failed to cache data with key '{key}': {e}")

    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached data by key.
        
        Args:
            key: Cache key
        
        Returns:
            Cached data or None if not found
        """
        return self.cache.get(key)

    def get_or_default(self, key: str, default: Any = None) -> Any:
        """Retrieve cached data with default fallback.
        
        Args:
            key: Cache key
            default: Default value if not found
        
        Returns:
            Cached data or default
        """
        return self.cache.get(key, default)

    def get_dataframe(self, key: str) -> Optional[pd.DataFrame]:
        """Retrieve cached DataFrame.
        
        Args:
            key: Cache key
        
        Returns:
            DataFrame or None
        
        Raises:
            DataLoadError: If cached data is not a DataFrame
        """
        data = self.get(key)
        if data is None:
            return None
        
        if not isinstance(data, pd.DataFrame):
            raise DataLoadError(f"Cached data at '{key}' is not a DataFrame")
        
        return data

    def exists(self, key: str) -> bool:
        """Check if data is cached.
        
        Args:
            key: Cache key
        
        Returns:
            True if cached, False otherwise
        """
        return key in self.cache

    def delete(self, key: str) -> bool:
        """Delete cached data.
        
        Args:
            key: Cache key
        
        Returns:
            True if deleted, False if not found
        """
        if key in self.cache:
            del self.cache[key]
            self.logger.info(f"Cache deleted: {key}")
            return True
        return False

    def clear(self) -> None:
        """Clear all cached data."""
        self.cache.clear()
        self.logger.info("Cache cleared")

    def list_keys(self) -> List[str]:
        """List all cache keys.
        
        Returns:
            List of cache keys
        """
        return list(self.cache.keys())

    def get_count(self) -> int:
        """Get number of cached items.
        
        Returns:
            Number of items in cache
        """
        return len(self.cache)

    def get_summary(self) -> Dict[str, Any]:
        """Get cache summary.
        
        Returns:
            Summary dict with cache stats
        """
        return {
            'total_items': len(self.cache),
            'keys': list(self.cache.keys()),
            'data_types': {
                key: type(data).__name__ 
                for key, data in self.cache.items()
            }
        }

    def get_data_for_task(
        self, 
        params: Dict[str, Any], 
        loader_agent: Optional[Any] = None
    ) -> pd.DataFrame:
        """Get data for task execution with priority:
        1. Provided data in params
        2. Cached data (by key)
        3. Default cached data ('loaded_data')
        4. Load from file
        
        Args:
            params: Task parameters
            loader_agent: DataLoader agent (optional, for loading from file)
        
        Returns:
            DataFrame
        
        Raises:
            DataLoadError: If no data available
        """
        # Priority 1: Data provided directly
        if 'data' in params and isinstance(params['data'], pd.DataFrame):
            self.logger.info("Using provided data")
            return params['data']
        
        # Priority 2: Cached data by key
        if 'data_key' in params:
            cached = self.get_dataframe(params['data_key'])
            if cached is not None:
                self.logger.info(f"Using cached data: {params['data_key']}")
                return cached
        
        # Priority 3: Default cached data
        cached = self.get_dataframe('loaded_data')
        if cached is not None:
            self.logger.info("Using default cached data")
            return cached
        
        # Priority 4: Load from file
        if 'file_path' in params and loader_agent is not None:
            try:
                result = loader_agent.load(params['file_path'])
                if result.get('status') == 'success':
                    data = result['data']
                    self.set('loaded_data', data)
                    self.logger.info(f"Loaded and cached data from: {params['file_path']}")
                    return data
            except Exception as e:
                self.logger.error(f"Error loading data from file: {e}")
        
        raise DataLoadError("No data available for task execution")
