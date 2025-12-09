"""Aggregator Agent - Data aggregation, grouping, and summarization.

This agent performs grouping, aggregation, pivot tables, and statistical
summaries on loaded datasets.

Capabilities:
- GroupBy operations (single and multiple columns)
- Pivot table creation
- Cross-tabulation
- Rolling aggregations
- Summary statistics
- Value counting

Returns:
    Dictionary with the following structure:
    {
        'status': 'success' or 'error',
        'message': 'human-readable message',
        'data': aggregated_result,
        'metadata': {
            'rows': int,
            'columns': int,
            'groups': int
        },
        'errors': list of error messages
    }

Example:
    agg = Aggregator()
    agg.set_data(df)
    result = agg.groupby_single('region', 'sales', 'sum')
    if result['status'] == 'success':
        print(f"Grouped into {result['metadata']['groups']} groups")
"""

from typing import Any, Dict, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime

from core.logger import get_logger
from core.exceptions import AgentError


class Aggregator:
    """Aggregator: Groups, aggregates, and summarizes data."""

    def __init__(self):
        """Initialize Aggregator agent."""
        self.name = "Aggregator"
        self.logger = get_logger("Aggregator")
        self.data = None
        self.aggregation_cache = {}
        self.logger.info("Aggregator initialized")

    # ===== SECTION 1: Data Management =====
    # What: Set and retrieve data
    # Input: DataFrame
    # Output: confirmation or current data

    def set_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Set data to aggregate.
        
        Args:
            df: DataFrame to aggregate
            
        Returns:
            {
                'status': 'success' or 'error',
                'message': str,
                'data': None,
                'metadata': {'rows': int, 'columns': int},
                'errors': list
            }
        """
        try:
            if df is None or df.empty:
                return {
                    'status': 'error',
                    'message': 'Data is empty',
                    'data': None,
                    'metadata': {},
                    'errors': ['DataFrame is empty']
                }
            
            self.data = df.copy()
            self.aggregation_cache = {}
            
            self.logger.info(f"Data set: {df.shape[0]} rows, {df.shape[1]} columns")
            
            return {
                'status': 'success',
                'message': f"Data loaded: {df.shape[0]} rows, {df.shape[1]} columns",
                'data': None,
                'metadata': {
                    'rows': df.shape[0],
                    'columns': df.shape[1],
                    'column_names': df.columns.tolist()
                },
                'errors': []
            }
        except Exception as e:
            self.logger.error(f"Failed to set data: {e}")
            return {
                'status': 'error',
                'message': f"Failed to set data: {e}",
                'data': None,
                'metadata': {},
                'errors': [str(e)]
            }

    def get_data(self) -> Optional[pd.DataFrame]:
        """Get currently loaded data.
        
        Returns:
            Loaded DataFrame or None if no data loaded
        """
        return self.data

    # ===== SECTION 2: Single-Level GroupBy =====
    # What: Group by one column and aggregate
    # Input: group column, agg column, function
    # Output: grouped result

    def groupby_single(self, group_col: str, agg_col: str, agg_func: str = "sum") -> Dict[str, Any]:
        """Group by single column and aggregate.
        
        Args:
            group_col: Column to group by
            agg_col: Column to aggregate
            agg_func: Aggregation function ('sum', 'mean', 'count', 'min', 'max', 'std', 'var')
            
        Returns:
            {
                'status': 'success' or 'error',
                'message': str,
                'data': list of dicts,
                'metadata': {'groups': int, 'function': str},
                'errors': list
            }
        """
        try:
            # Validate data
            if self.data is None:
                return {
                    'status': 'error',
                    'message': 'No data loaded',
                    'data': None,
                    'metadata': {},
                    'errors': ['No data set. Use set_data() first.']
                }
            
            # Validate columns
            if group_col not in self.data.columns:
                return {
                    'status': 'error',
                    'message': f"Column '{group_col}' not found",
                    'data': None,
                    'metadata': {},
                    'errors': [f"Group column '{group_col}' not found"]
                }
            
            if agg_col not in self.data.columns:
                return {
                    'status': 'error',
                    'message': f"Column '{agg_col}' not found",
                    'data': None,
                    'metadata': {},
                    'errors': [f"Aggregation column '{agg_col}' not found"]
                }
            
            # Perform groupby
            self.logger.info(f"GroupBy '{group_col}' aggregating '{agg_col}' with {agg_func}")
            
            result = self.data.groupby(group_col)[agg_col].agg(agg_func).reset_index()
            result.columns = [group_col, f"{agg_col}_{agg_func}"]
            
            return {
                'status': 'success',
                'message': f"Grouped by '{group_col}' into {len(result)} groups",
                'data': result.to_dict(orient='records'),
                'metadata': {
                    'groups': len(result),
                    'group_column': group_col,
                    'aggregated_column': agg_col,
                    'function': agg_func
                },
                'errors': []
            }
        
        except Exception as e:
            self.logger.error(f"GroupBy failed: {e}")
            return {
                'status': 'error',
                'message': f"GroupBy operation failed: {e}",
                'data': None,
                'metadata': {},
                'errors': [str(e)]
            }

    # ===== SECTION 3: Multi-Level GroupBy =====
    # What: Group by multiple columns with multiple aggregations
    # Input: group columns, aggregation specs
    # Output: multi-level grouped result

    def groupby_multiple(self, group_cols: List[str], agg_specs: Dict[str, str]) -> Dict[str, Any]:
        """Group by multiple columns with multiple aggregations.
        
        Args:
            group_cols: Columns to group by
            agg_specs: Dictionary mapping columns to aggregation functions
                      e.g., {'sales': 'sum', 'quantity': 'mean'}
            
        Returns:
            {
                'status': 'success' or 'error',
                'message': str,
                'data': list of dicts,
                'metadata': {'groups': int, 'group_columns': list, 'agg_specs': dict},
                'errors': list
            }
        """
        try:
            # Validate data
            if self.data is None:
                return {
                    'status': 'error',
                    'message': 'No data loaded',
                    'data': None,
                    'metadata': {},
                    'errors': ['No data set. Use set_data() first.']
                }
            
            # Validate group columns
            for col in group_cols:
                if col not in self.data.columns:
                    return {
                        'status': 'error',
                        'message': f"Column '{col}' not found",
                        'data': None,
                        'metadata': {},
                        'errors': [f"Group column '{col}' not found"]
                    }
            
            # Validate aggregation columns
            for col in agg_specs.keys():
                if col not in self.data.columns:
                    return {
                        'status': 'error',
                        'message': f"Column '{col}' not found",
                        'data': None,
                        'metadata': {},
                        'errors': [f"Aggregation column '{col}' not found"]
                    }
            
            # Perform multi-level groupby
            self.logger.info(f"Multi-level GroupBy by {group_cols} with specs {agg_specs}")
            
            result = self.data.groupby(group_cols).agg(agg_specs).reset_index()
            
            return {
                'status': 'success',
                'message': f"Grouped into {len(result)} groups",
                'data': result.to_dict(orient='records'),
                'metadata': {
                    'groups': len(result),
                    'group_columns': group_cols,
                    'aggregation_specs': agg_specs
                },
                'errors': []
            }
        
        except Exception as e:
            self.logger.error(f"Multi-level GroupBy failed: {e}")
            return {
                'status': 'error',
                'message': f"Multi-level GroupBy failed: {e}",
                'data': None,
                'metadata': {},
                'errors': [str(e)]
            }

    # ===== SECTION 4: Pivot & CrossTab =====
    # What: Reshape data into pivot tables
    # Input: index, columns, values
    # Output: pivot table result

    def pivot_table(self, index: str, columns: str, values: str, aggfunc: str = "sum") -> Dict[str, Any]:
        """Create pivot table.
        
        Args:
            index: Column for rows
            columns: Column for columns
            values: Column to aggregate
            aggfunc: Aggregation function
            
        Returns:
            {
                'status': 'success' or 'error',
                'message': str,
                'data': list of dicts,
                'metadata': {'shape': tuple, 'index': str, 'columns': str, 'values': str},
                'errors': list
            }
        """
        try:
            # Validate data
            if self.data is None:
                return {
                    'status': 'error',
                    'message': 'No data loaded',
                    'data': None,
                    'metadata': {},
                    'errors': ['No data set. Use set_data() first.']
                }
            
            # Validate columns
            for col in [index, columns, values]:
                if col not in self.data.columns:
                    return {
                        'status': 'error',
                        'message': f"Column '{col}' not found",
                        'data': None,
                        'metadata': {},
                        'errors': [f"Column '{col}' not found"]
                    }
            
            # Create pivot table
            self.logger.info(f"Creating pivot table: index={index}, columns={columns}, values={values}")
            
            pivot = pd.pivot_table(
                self.data,
                index=index,
                columns=columns,
                values=values,
                aggfunc=aggfunc
            ).reset_index()
            
            return {
                'status': 'success',
                'message': f"Pivot table created: {pivot.shape[0]} rows x {pivot.shape[1]} columns",
                'data': pivot.to_dict(orient='records'),
                'metadata': {
                    'shape': pivot.shape,
                    'index': index,
                    'columns': columns,
                    'values': values,
                    'aggfunc': aggfunc
                },
                'errors': []
            }
        
        except Exception as e:
            self.logger.error(f"Pivot table creation failed: {e}")
            return {
                'status': 'error',
                'message': f"Pivot table creation failed: {e}",
                'data': None,
                'metadata': {},
                'errors': [str(e)]
            }

    def crosstab(self, row_col: str, col_col: str, values: Optional[str] = None, aggfunc: str = "count") -> Dict[str, Any]:
        """Create cross-tabulation.
        
        Args:
            row_col: Column for rows
            col_col: Column for columns
            values: Column to aggregate (optional)
            aggfunc: Aggregation function
            
        Returns:
            {
                'status': 'success' or 'error',
                'message': str,
                'data': list of dicts,
                'metadata': {'shape': tuple, 'rows': str, 'columns': str},
                'errors': list
            }
        """
        try:
            # Validate data
            if self.data is None:
                return {
                    'status': 'error',
                    'message': 'No data loaded',
                    'data': None,
                    'metadata': {},
                    'errors': ['No data set. Use set_data() first.']
                }
            
            # Validate columns
            for col in [row_col, col_col]:
                if col not in self.data.columns:
                    return {
                        'status': 'error',
                        'message': f"Column '{col}' not found",
                        'data': None,
                        'metadata': {},
                        'errors': [f"Column '{col}' not found"]
                    }
            
            if values and values not in self.data.columns:
                return {
                    'status': 'error',
                    'message': f"Column '{values}' not found",
                    'data': None,
                    'metadata': {},
                    'errors': [f"Values column '{values}' not found"]
                }
            
            # Create crosstab
            self.logger.info(f"Creating crosstab: rows={row_col}, cols={col_col}")
            
            if values:
                ct = pd.crosstab(
                    self.data[row_col],
                    self.data[col_col],
                    values=self.data[values],
                    aggfunc=aggfunc
                )
            else:
                ct = pd.crosstab(
                    self.data[row_col],
                    self.data[col_col]
                )
            
            ct = ct.reset_index()
            
            return {
                'status': 'success',
                'message': f"Crosstab created: {ct.shape[0]} rows x {ct.shape[1]} columns",
                'data': ct.to_dict(orient='records'),
                'metadata': {
                    'shape': ct.shape,
                    'row_column': row_col,
                    'column_column': col_col,
                    'values_column': values,
                    'aggfunc': aggfunc
                },
                'errors': []
            }
        
        except Exception as e:
            self.logger.error(f"Crosstab creation failed: {e}")
            return {
                'status': 'error',
                'message': f"Crosstab creation failed: {e}",
                'data': None,
                'metadata': {},
                'errors': [str(e)]
            }

    # ===== SECTION 5: Time Series Aggregation =====
    # What: Rolling and time-based aggregations
    # Input: column, window, function
    # Output: time series result

    def rolling_aggregation(self, col: str, window: int, aggfunc: str = "mean") -> Dict[str, Any]:
        """Apply rolling aggregation (for time series).
        
        Args:
            col: Column to aggregate
            window: Rolling window size
            aggfunc: Aggregation function ('mean', 'sum', 'min', 'max')
            
        Returns:
            {
                'status': 'success' or 'error',
                'message': str,
                'data': list of dicts,
                'metadata': {'window': int, 'function': str, 'non_null': int},
                'errors': list
            }
        """
        try:
            # Validate data
            if self.data is None:
                return {
                    'status': 'error',
                    'message': 'No data loaded',
                    'data': None,
                    'metadata': {},
                    'errors': ['No data set. Use set_data() first.']
                }
            
            # Validate column
            if col not in self.data.columns:
                return {
                    'status': 'error',
                    'message': f"Column '{col}' not found",
                    'data': None,
                    'metadata': {},
                    'errors': [f"Column '{col}' not found"]
                }
            
            # Apply rolling aggregation
            self.logger.info(f"Rolling {aggfunc} on '{col}' with window={window}")
            
            rolling_result = self.data[col].rolling(window=window).agg(aggfunc)
            
            result_df = pd.DataFrame({
                col: self.data[col],
                f"{col}_rolling_{aggfunc}": rolling_result
            })
            
            return {
                'status': 'success',
                'message': f"Rolling aggregation applied",
                'data': result_df.to_dict(orient='records'),
                'metadata': {
                    'column': col,
                    'window': window,
                    'function': aggfunc,
                    'non_null_values': int(rolling_result.notna().sum())
                },
                'errors': []
            }
        
        except Exception as e:
            self.logger.error(f"Rolling aggregation failed: {e}")
            return {
                'status': 'error',
                'message': f"Rolling aggregation failed: {e}",
                'data': None,
                'metadata': {},
                'errors': [str(e)]
            }

    # ===== SECTION 6: Statistical Summary =====
    # What: Summary statistics and value counts
    # Input: column(s)
    # Output: summary statistics

    def summary_statistics(self, group_col: str) -> Dict[str, Any]:
        """Get comprehensive summary statistics for groups.
        
        Args:
            group_col: Column to group by
            
        Returns:
            {
                'status': 'success' or 'error',
                'message': str,
                'data': dict of statistics,
                'metadata': {'groups': int, 'numeric_columns': int},
                'errors': list
            }
        """
        try:
            # Validate data
            if self.data is None:
                return {
                    'status': 'error',
                    'message': 'No data loaded',
                    'data': None,
                    'metadata': {},
                    'errors': ['No data set. Use set_data() first.']
                }
            
            # Validate column
            if group_col not in self.data.columns:
                return {
                    'status': 'error',
                    'message': f"Column '{group_col}' not found",
                    'data': None,
                    'metadata': {},
                    'errors': [f"Column '{group_col}' not found"]
                }
            
            # Get numeric columns
            numeric_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()
            
            if not numeric_cols:
                return {
                    'status': 'error',
                    'message': 'No numeric columns found',
                    'data': None,
                    'metadata': {},
                    'errors': ['No numeric columns to aggregate']
                }
            
            # Compute statistics for each group
            self.logger.info(f"Computing summary statistics grouped by '{group_col}'")
            
            grouped = self.data.groupby(group_col)
            stats = {}
            
            for group_name, group_df in grouped:
                group_stats = {}
                for col in numeric_cols:
                    group_stats[col] = {
                        "count": int(group_df[col].count()),
                        "mean": float(group_df[col].mean()),
                        "std": float(group_df[col].std()),
                        "min": float(group_df[col].min()),
                        "max": float(group_df[col].max()),
                        "median": float(group_df[col].median()),
                    }
                stats[str(group_name)] = group_stats
            
            return {
                'status': 'success',
                'message': f"Summary statistics for {len(stats)} groups",
                'data': stats,
                'metadata': {
                    'groups': len(stats),
                    'group_column': group_col,
                    'numeric_columns': len(numeric_cols)
                },
                'errors': []
            }
        
        except Exception as e:
            self.logger.error(f"Summary statistics failed: {e}")
            return {
                'status': 'error',
                'message': f"Summary statistics failed: {e}",
                'data': None,
                'metadata': {},
                'errors': [str(e)]
            }

    def value_counts(self, col: str, top_n: int = 10) -> Dict[str, Any]:
        """Get value counts for a column.
        
        Args:
            col: Column to analyze
            top_n: Number of top values to return
            
        Returns:
            {
                'status': 'success' or 'error',
                'message': str,
                'data': list of dicts,
                'metadata': {'total_unique': int, 'top_n': int},
                'errors': list
            }
        """
        try:
            # Validate data
            if self.data is None:
                return {
                    'status': 'error',
                    'message': 'No data loaded',
                    'data': None,
                    'metadata': {},
                    'errors': ['No data set. Use set_data() first.']
                }
            
            # Validate column
            if col not in self.data.columns:
                return {
                    'status': 'error',
                    'message': f"Column '{col}' not found",
                    'data': None,
                    'metadata': {},
                    'errors': [f"Column '{col}' not found"]
                }
            
            # Compute value counts
            self.logger.info(f"Computing value counts for '{col}'")
            
            vc = self.data[col].value_counts().head(top_n)
            
            result_list = []
            for value, count in vc.items():
                pct = (count / len(self.data)) * 100
                result_list.append({
                    "value": value,
                    "count": int(count),
                    "percentage": round(pct, 2),
                })
            
            return {
                'status': 'success',
                'message': f"Value counts for {len(result_list)} unique values",
                'data': result_list,
                'metadata': {
                    'column': col,
                    'total_unique': self.data[col].nunique(),
                    'top_n': top_n,
                    'results_returned': len(result_list)
                },
                'errors': []
            }
        
        except Exception as e:
            self.logger.error(f"Value counts failed: {e}")
            return {
                'status': 'error',
                'message': f"Value counts failed: {e}",
                'data': None,
                'metadata': {},
                'errors': [str(e)]
            }

    # ===== SECTION 7: Utilities =====
    # What: Helper functions
    # Output: summary or info

    def get_summary(self) -> str:
        """Get human-readable summary of aggregator.
        
        Returns:
            Formatted summary string
        """
        if self.data is None:
            return "Aggregator: No data loaded"
        
        return (
            f"Aggregator Summary:\n"
            f"  Data: {self.data.shape[0]} rows x {self.data.shape[1]} columns\n"
            f"  Columns: {', '.join(self.data.columns[:5])}{'...' if len(self.data.columns) > 5 else ''}\n"
            f"  Numeric: {len(self.data.select_dtypes(include=[np.number]).columns)}\n"
            f"  Categorical: {len(self.data.select_dtypes(include=['object']).columns)}"
        )
