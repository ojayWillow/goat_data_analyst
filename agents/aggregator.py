"""Aggregator Agent - Data aggregation, grouping, and summarization.

Handles groupBy operations, multi-level aggregations, pivot tables,
and custom aggregation functions.
"""

from typing import Any, Dict, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime

from core.logger import get_logger
from core.exceptions import AgentError

logger = get_logger(__name__)


class Aggregator:
    """Agent for data aggregation and grouping.
    
    Capabilities:
    - GroupBy operations (single and multiple columns)
    - Multi-level aggregations
    - Pivot table creation
    - Custom aggregation functions
    - Time-based aggregation
    - Rolling aggregations
    - Cross-tabulation
    """
    
    def __init__(self):
        """Initialize Aggregator agent."""
        self.name = "Aggregator"
        self.data = None
        self.aggregation_cache = {}
        logger.info(f"{self.name} initialized")
    
    def set_data(self, df: pd.DataFrame) -> None:
        """Set data to aggregate.
        
        Args:
            df: DataFrame to aggregate
        """
        self.data = df.copy()
        self.aggregation_cache = {}  # Clear cache
        logger.info(f"Data set: {df.shape[0]} rows, {df.shape[1]} columns")
    
    def get_data(self) -> Optional[pd.DataFrame]:
        """Get current data.
        
        Returns:
            DataFrame or None
        """
        return self.data
    
    def groupby_single(self, group_col: str, agg_col: str, agg_func: str = "sum") -> Dict[str, Any]:
        """Group by single column and aggregate.
        
        Args:
            group_col: Column to group by
            agg_col: Column to aggregate
            agg_func: Aggregation function ('sum', 'mean', 'count', 'min', 'max', 'std', 'var')
            
        Returns:
            Dictionary with groupby results
            
        Raises:
            AgentError: If columns don't exist or aggregation fails
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if group_col not in self.data.columns:
            raise AgentError(f"Column '{group_col}' not found")
        
        if agg_col not in self.data.columns:
            raise AgentError(f"Column '{agg_col}' not found")
        
        try:
            logger.info(f"GroupBy '{group_col}' aggregating '{agg_col}' with {agg_func}")
            
            result = self.data.groupby(group_col)[agg_col].agg(agg_func).reset_index()
            result.columns = [group_col, f"{agg_col}_{agg_func}"]
            
            return {
                "status": "success",
                "group_by": group_col,
                "aggregated_column": agg_col,
                "function": agg_func,
                "groups": len(result),
                "results": result.to_dict(orient="records"),
                "dataframe": result,
            }
        
        except Exception as e:
            logger.error(f"GroupBy failed: {e}")
            raise AgentError(f"GroupBy operation failed: {e}")
    
    def groupby_multiple(self, group_cols: List[str], agg_specs: Dict[str, str]) -> Dict[str, Any]:
        """Group by multiple columns with multiple aggregations.
        
        Args:
            group_cols: Columns to group by
            agg_specs: Dictionary mapping columns to aggregation functions
                      e.g., {'sales': 'sum', 'quantity': 'mean', 'price': 'max'}
            
        Returns:
            Dictionary with multi-level groupby results
            
        Raises:
            AgentError: If columns don't exist or aggregation fails
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        # Validate columns
        for col in group_cols:
            if col not in self.data.columns:
                raise AgentError(f"Group column '{col}' not found")
        
        for col in agg_specs.keys():
            if col not in self.data.columns:
                raise AgentError(f"Aggregation column '{col}' not found")
        
        try:
            logger.info(f"Multi-level GroupBy by {group_cols} with specs {agg_specs}")
            
            result = self.data.groupby(group_cols).agg(agg_specs).reset_index()
            
            return {
                "status": "success",
                "group_by_columns": group_cols,
                "aggregation_specs": agg_specs,
                "groups": len(result),
                "results": result.to_dict(orient="records"),
                "dataframe": result,
            }
        
        except Exception as e:
            logger.error(f"Multi-level GroupBy failed: {e}")
            raise AgentError(f"Multi-level GroupBy failed: {e}")
    
    def pivot_table(self, index: str, columns: str, values: str, aggfunc: str = "sum") -> Dict[str, Any]:
        """Create pivot table.
        
        Args:
            index: Column for rows
            columns: Column for columns
            values: Column to aggregate
            aggfunc: Aggregation function
            
        Returns:
            Dictionary with pivot table
            
        Raises:
            AgentError: If columns don't exist or pivot fails
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        # Validate columns
        for col in [index, columns, values]:
            if col not in self.data.columns:
                raise AgentError(f"Column '{col}' not found")
        
        try:
            logger.info(f"Creating pivot table: index={index}, columns={columns}, values={values}")
            
            pivot = pd.pivot_table(
                self.data,
                index=index,
                columns=columns,
                values=values,
                aggfunc=aggfunc
            ).reset_index()
            
            return {
                "status": "success",
                "index": index,
                "columns": columns,
                "values": values,
                "aggfunc": aggfunc,
                "shape": pivot.shape,
                "results": pivot.to_dict(orient="records"),
                "dataframe": pivot,
            }
        
        except Exception as e:
            logger.error(f"Pivot table creation failed: {e}")
            raise AgentError(f"Pivot table creation failed: {e}")
    
    def crosstab(self, row_col: str, col_col: str, values: Optional[str] = None, aggfunc: str = "count") -> Dict[str, Any]:
        """Create cross-tabulation.
        
        Args:
            row_col: Column for rows
            col_col: Column for columns
            values: Column to aggregate (optional)
            aggfunc: Aggregation function
            
        Returns:
            Dictionary with cross-tabulation
            
        Raises:
            AgentError: If columns don't exist or crosstab fails
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        # Validate columns
        for col in [row_col, col_col]:
            if col not in self.data.columns:
                raise AgentError(f"Column '{col}' not found")
        
        if values and values not in self.data.columns:
            raise AgentError(f"Values column '{values}' not found")
        
        try:
            logger.info(f"Creating crosstab: rows={row_col}, cols={col_col}")
            
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
                "status": "success",
                "row_column": row_col,
                "column_column": col_col,
                "values_column": values,
                "aggfunc": aggfunc,
                "shape": ct.shape,
                "results": ct.to_dict(orient="records"),
                "dataframe": ct,
            }
        
        except Exception as e:
            logger.error(f"Crosstab creation failed: {e}")
            raise AgentError(f"Crosstab creation failed: {e}")
    
    def rolling_aggregation(self, col: str, window: int, aggfunc: str = "mean") -> Dict[str, Any]:
        """Apply rolling aggregation (for time series).
        
        Args:
            col: Column to aggregate
            window: Rolling window size
            aggfunc: Aggregation function ('mean', 'sum', 'min', 'max')
            
        Returns:
            Dictionary with rolling aggregation results
            
        Raises:
            AgentError: If column doesn't exist or aggregation fails
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if col not in self.data.columns:
            raise AgentError(f"Column '{col}' not found")
        
        try:
            logger.info(f"Rolling {aggfunc} on '{col}' with window={window}")
            
            rolling_result = self.data[col].rolling(window=window).agg(aggfunc)
            
            result_df = pd.DataFrame({
                col: self.data[col],
                f"{col}_rolling_{aggfunc}": rolling_result
            })
            
            return {
                "status": "success",
                "column": col,
                "window": window,
                "function": aggfunc,
                "non_null_values": int(rolling_result.notna().sum()),
                "results": result_df.to_dict(orient="records"),
                "dataframe": result_df,
            }
        
        except Exception as e:
            logger.error(f"Rolling aggregation failed: {e}")
            raise AgentError(f"Rolling aggregation failed: {e}")
    
    def summary_statistics(self, group_col: str) -> Dict[str, Any]:
        """Get comprehensive summary statistics for groups.
        
        Args:
            group_col: Column to group by
            
        Returns:
            Dictionary with comprehensive statistics per group
            
        Raises:
            AgentError: If column doesn't exist
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if group_col not in self.data.columns:
            raise AgentError(f"Column '{group_col}' not found")
        
        try:
            logger.info(f"Computing summary statistics grouped by '{group_col}'")
            
            numeric_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()
            
            if not numeric_cols:
                return {"status": "no_numeric_columns", "message": "No numeric columns found"}
            
            # Compute statistics for each group
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
                "status": "success",
                "group_by": group_col,
                "groups": len(stats),
                "statistics": stats,
            }
        
        except Exception as e:
            logger.error(f"Summary statistics failed: {e}")
            raise AgentError(f"Summary statistics failed: {e}")
    
    def value_counts(self, col: str, top_n: int = 10) -> Dict[str, Any]:
        """Get value counts for a column.
        
        Args:
            col: Column to analyze
            top_n: Number of top values to return
            
        Returns:
            Dictionary with value counts
            
        Raises:
            AgentError: If column doesn't exist
        """
        if self.data is None:
            raise AgentError("No data set. Use set_data() first.")
        
        if col not in self.data.columns:
            raise AgentError(f"Column '{col}' not found")
        
        try:
            logger.info(f"Computing value counts for '{col}'")
            
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
                "status": "success",
                "column": col,
                "total_unique": self.data[col].nunique(),
                "top_n": top_n,
                "results": result_list,
            }
        
        except Exception as e:
            logger.error(f"Value counts failed: {e}")
            raise AgentError(f"Value counts failed: {e}")
