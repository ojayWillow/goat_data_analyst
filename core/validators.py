"""Validation Framework for GOAT Data Analyst - Hardening Phase 1

Provides comprehensive validation with:
- Input validation decorators
- Output validation
- Type checking
- Schema validation
- Data quality checks

Usage:
    from core.validators import validate_input, validate_output, DataValidator
    
    @validate_input({
        'data': 'dataframe',
        'columns': 'list',
    })
    def process_data(data, columns):
        return data[columns]
    
    @validate_output('dataframe')
    def load_data(filepath):
        return pd.read_csv(filepath)
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Callable, Optional, Union, Type
from functools import wraps
from core.logger import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Exception raised when validation fails."""
    pass


class DataValidator:
    """Validator for data types and schemas."""
    
    @staticmethod
    def is_dataframe(obj: Any) -> bool:
        """Check if object is a pandas DataFrame."""
        return isinstance(obj, pd.DataFrame)
    
    @staticmethod
    def is_series(obj: Any) -> bool:
        """Check if object is a pandas Series."""
        return isinstance(obj, pd.Series)
    
    @staticmethod
    def is_list(obj: Any) -> bool:
        """Check if object is a list."""
        return isinstance(obj, list)
    
    @staticmethod
    def is_dict(obj: Any) -> bool:
        """Check if object is a dictionary."""
        return isinstance(obj, dict)
    
    @staticmethod
    def is_array(obj: Any) -> bool:
        """Check if object is a numpy array."""
        return isinstance(obj, np.ndarray)
    
    @staticmethod
    def is_numeric(obj: Any) -> bool:
        """Check if object is numeric."""
        return isinstance(obj, (int, float, np.number))
    
    @staticmethod
    def is_string(obj: Any) -> bool:
        """Check if object is a string."""
        return isinstance(obj, str)
    
    @staticmethod
    def is_bool(obj: Any) -> bool:
        """Check if object is a boolean."""
        return isinstance(obj, bool)
    
    @staticmethod
    def dataframe_not_empty(df: pd.DataFrame) -> bool:
        """Check if DataFrame is not empty."""
        return not df.empty and len(df) > 0
    
    @staticmethod
    def dataframe_has_columns(df: pd.DataFrame, columns: List[str]) -> bool:
        """Check if DataFrame has required columns."""
        return all(col in df.columns for col in columns)
    
    @staticmethod
    def dataframe_no_nans(df: pd.DataFrame) -> bool:
        """Check if DataFrame has no NaN values."""
        return not df.isnull().any().any()
    
    @staticmethod
    def dataframe_no_duplicates(df: pd.DataFrame) -> bool:
        """Check if DataFrame has no duplicate rows."""
        return not df.duplicated().any()
    
    @staticmethod
    def list_not_empty(lst: List) -> bool:
        """Check if list is not empty."""
        return isinstance(lst, list) and len(lst) > 0
    
    @staticmethod
    def list_of_type(lst: List, element_type: Type) -> bool:
        """Check if list contains only elements of specific type."""
        return isinstance(lst, list) and all(isinstance(x, element_type) for x in lst)
    
    @staticmethod
    def dict_has_keys(d: Dict, keys: List[str]) -> bool:
        """Check if dict has required keys."""
        return isinstance(d, dict) and all(key in d for key in keys)
    
    @classmethod
    def validate(cls, value: Any, value_type: str) -> bool:
        """Validate value against type.
        
        Args:
            value: Value to validate
            value_type: Type name ('dataframe', 'list', 'dict', 'array', etc.)
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        validators = {
            'dataframe': cls.is_dataframe,
            'series': cls.is_series,
            'list': cls.is_list,
            'dict': cls.is_dict,
            'array': cls.is_array,
            'numeric': cls.is_numeric,
            'string': cls.is_string,
            'bool': cls.is_bool,
        }
        
        if value_type not in validators:
            raise ValueError(f"Unknown type: {value_type}")
        
        if not validators[value_type](value):
            raise ValidationError(
                f"Expected {value_type}, got {type(value).__name__}"
            )
        
        return True


def validate_input(schema: Dict[str, str]):
    """Decorator for input validation.
    
    Args:
        schema: Dictionary mapping parameter names to expected types
        
    Example:
        @validate_input({
            'data': 'dataframe',
            'columns': 'list',
        })
        def process_data(data, columns):
            return data[columns]
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate each parameter in schema
            for param_name, expected_type in schema.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    try:
                        DataValidator.validate(value, expected_type)
                    except ValidationError as e:
                        logger.error(
                            f"Input validation failed for {func.__name__}: {param_name}. {e}"
                        )
                        raise
                else:
                    raise ValidationError(
                        f"Parameter {param_name} not found in function signature"
                    )
            
            logger.debug(f"Input validation passed for {func.__name__}")
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_output(expected_type: str):
    """Decorator for output validation.
    
    Args:
        expected_type: Expected return type
        
    Example:
        @validate_output('dataframe')
        def load_data(filepath):
            return pd.read_csv(filepath)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            try:
                DataValidator.validate(result, expected_type)
            except ValidationError as e:
                logger.error(
                    f"Output validation failed for {func.__name__}. {e}"
                )
                raise
            
            logger.debug(f"Output validation passed for {func.__name__}")
            return result
        
        return wrapper
    return decorator


def validate_dataframe_quality(require_no_nans: bool = False,
                              require_no_duplicates: bool = False,
                              require_columns: Optional[List[str]] = None):
    """Decorator for DataFrame quality validation.
    
    Args:
        require_no_nans: Check for NaN values
        require_no_duplicates: Check for duplicate rows
        require_columns: Required columns
        
    Example:
        @validate_dataframe_quality(
            require_no_nans=True,
            require_columns=['id', 'name']
        )
        def process_data(data):
            return data
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            if not isinstance(result, pd.DataFrame):
                raise ValidationError(f"Expected DataFrame, got {type(result).__name__}")
            
            # Check for NaNs
            if require_no_nans and result.isnull().any().any():
                nan_count = result.isnull().sum().sum()
                raise ValidationError(f"DataFrame contains {nan_count} NaN values")
            
            # Check for duplicates
            if require_no_duplicates and result.duplicated().any():
                dup_count = result.duplicated().sum()
                raise ValidationError(f"DataFrame contains {dup_count} duplicate rows")
            
            # Check for required columns
            if require_columns:
                missing = set(require_columns) - set(result.columns)
                if missing:
                    raise ValidationError(f"Missing columns: {missing}")
            
            logger.debug(f"DataFrame quality validation passed for {func.__name__}")
            return result
        
        return wrapper
    return decorator


def validate_not_none():
    """Decorator to ensure return value is not None.
    
    Example:
        @validate_not_none()
        def get_data():
            return load_data()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            if result is None:
                raise ValidationError(f"{func.__name__} returned None")
            
            logger.debug(f"Non-None validation passed for {func.__name__}")
            return result
        
        return wrapper
    return decorator


def validate_positive_numbers():
    """Decorator to ensure return value contains only positive numbers.
    
    Example:
        @validate_positive_numbers()
        def compute_scores(data):
            return np.array([1, 2, 3, 4])
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            if isinstance(result, (list, np.ndarray, pd.Series)):
                if np.any(np.array(result) <= 0):
                    raise ValidationError(
                        f"{func.__name__} returned non-positive values"
                    )
            elif isinstance(result, (int, float)):
                if result <= 0:
                    raise ValidationError(
                        f"{func.__name__} returned non-positive value: {result}"
                    )
            
            logger.debug(f"Positive numbers validation passed for {func.__name__}")
            return result
        
        return wrapper
    return decorator


def validate_size_limit(max_size: int):
    """Decorator to ensure result size doesn't exceed limit.
    
    Args:
        max_size: Maximum allowed size
        
    Example:
        @validate_size_limit(max_size=10000)
        def load_data(filepath):
            return pd.read_csv(filepath)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            size = None
            if isinstance(result, pd.DataFrame):
                size = len(result)
            elif isinstance(result, (list, np.ndarray)):
                size = len(result)
            elif isinstance(result, dict):
                size = len(result)
            
            if size is not None and size > max_size:
                raise ValidationError(
                    f"{func.__name__} returned {size} items, max is {max_size}"
                )
            
            logger.debug(f"Size limit validation passed for {func.__name__}")
            return result
        
        return wrapper
    return decorator
