# Troubleshooting Guide - GOAT Data Analyst

## Common Issues and Solutions

### Issue: "Insufficient memory" Error

**Symptom:**
```
MemoryError: Insufficient memory for operation
```

**Causes:**
- DataFrame too large for operation
- Complex aggregation with many unique values
- Pivot table with too many categories

**Solutions:**
1. **Filter data before aggregation:**
   ```python
   # Bad: Aggregate entire dataset
   result = agg.aggregate(data=large_df, operations=[...])
   
   # Good: Filter first
   filtered = large_df[large_df['year'] == 2024]
   result = agg.aggregate(data=filtered, operations=[...])
   ```

2. **Use chunking for large operations:**
   ```python
   chunks = [df.iloc[i:i+10000] for i in range(0, len(df), 10000)]
   results = [agg.aggregate(data=chunk, operations=[...]) for chunk in chunks]
   ```

3. **Reduce categories in pivot operations:**
   ```python
   # Filter to top categories first
   top_cats = df['category'].value_counts().head(10).index
   df_filtered = df[df['category'].isin(top_cats)]
   ```

4. **Monitor quality score:**
   ```python
   if result.quality_score < 0.8:
       # Check for memory_error in metadata
       if 'advanced_errors_encountered' in result.data:
           print(f"Errors: {result.data['advanced_errors_encountered']}")
   ```

---

### Issue: "No numeric columns found"

**Symptom:**
```
Missing numeric columns for operation
```

**Causes:**
- Wrong DataFrame passed
- All columns are strings/objects
- Column selection doesn't include numeric columns

**Solutions:**
1. **Check DataFrame structure:**
   ```python
   print(df.dtypes)  # View all column types
   print(df.select_dtypes(include=['number']).columns)  # Numeric columns
   ```

2. **Convert columns to numeric:**
   ```python
   df['price'] = pd.to_numeric(df['price'], errors='coerce')
   ```

3. **Specify numeric columns explicitly:**
   ```python
   result = worker.safe_execute(
       df=df,
       columns=['price', 'quantity']  # Specify numeric columns
   )
   ```

---

### Issue: "Quality score too low"

**Symptom:**
```
Quality score: 0.45 (below acceptable threshold)
```

**Causes:**
- High percentage of null values
- Many advanced errors encountered
- Data type mismatches

**Solutions:**
1. **Check error details:**
   ```python
   result = agg.aggregate(data=df, operations=[...])
   
   if not result.success or result.quality_score < 0.7:
       print(f"Errors: {result.errors}")
       print(f"Error data: {result.data.get('advanced_error_types', [])}")
   ```

2. **Clean data before aggregation:**
   ```python
   # Remove null values
   df_clean = df.dropna(subset=['critical_columns'])
   
   # Remove duplicates
   df_clean = df_clean.drop_duplicates()
   
   # Convert types
   df_clean['price'] = pd.to_numeric(df_clean['price'])
   ```

3. **Check for infinity values:**
   ```python
   import numpy as np
   
   inf_cols = df.select_dtypes(include=['number']).columns
   for col in inf_cols:
       if np.isinf(df[col]).any():
           print(f"Infinity values in {col}")
           df[col] = df[col].replace([np.inf, -np.inf], np.nan)
   ```

---

### Issue: "Column not found" Error

**Symptom:**
```
Invalid parameter: Column 'sales' not found
```

**Causes:**
- Column name typo
- Wrong DataFrame passed
- Column was dropped

**Solutions:**
1. **Verify column names:**
   ```python
   print(df.columns.tolist())
   print('sales' in df.columns)  # Check specific column
   ```

2. **Case-sensitive check:**
   ```python
   # Column names are case-sensitive
   'Sales' != 'sales'  # These are different
   
   # Use lower case
   df.columns = df.columns.str.lower()
   ```

3. **Use correct parameter name:**
   ```python
   # Check API for correct parameter names
   result = worker.safe_execute(
       df=df,
       column='sales',  # Singular, not 'columns'
       functions=['mean']
   )
   ```

---

### Issue: "Empty result" Error

**Symptom:**
```
Computation error: Result is empty
```

**Causes:**
- All data filtered out
- Invalid aggregation combination
- No matching data for groupby

**Solutions:**
1. **Verify data exists:**
   ```python
   # Check before operation
   print(f"Rows: {len(df)}")
   print(f"Non-null in {col}: {df[col].notna().sum()}")
   ```

2. **Check groupby combinations:**
   ```python
   # Verify groups exist
   print(df.groupby('category').size())
   
   # Filter to categories with data
   top_cats = df['category'].value_counts().head(10).index
   df = df[df['category'].isin(top_cats)]
   ```

3. **Validate aggregation:**
   ```python
   # Test the aggregation manually
   test = df.groupby('category')['sales'].sum()
   print(test)
   ```

---

### Issue: "Infinity values detected"

**Symptom:**
```
Warning: Crosstab contains 5 infinity values
```

**Causes:**
- Division by zero in aggregation
- Very large number calculations
- Mathematical operations on invalid data

**Solutions:**
1. **Handle before operation:**
   ```python
   import numpy as np
   
   # Replace infinity with NaN
   df = df.replace([np.inf, -np.inf], np.nan)
   
   # Or drop rows with infinity
   numeric_cols = df.select_dtypes(include=['number']).columns
   df = df[~np.isinf(df[numeric_cols]).any(axis=1)]
   ```

2. **Check source calculation:**
   ```python
   # Identify which operation creates infinity
   print(df['value1'] / df['value2'])  # Check for division by zero
   ```

3. **Use safe division:**
   ```python
   # Avoid division by zero
   df['ratio'] = df['numerator'] / df['denominator'].replace(0, np.nan)
   ```

---

### Issue: "NaN values detected"

**Symptom:**
```
Warning: Unexpected NaN values found after processing
```

**Causes:**
- Null values in input data
- Operations creating NaN (e.g., log of negative)
- Mismatched data types

**Solutions:**
1. **Check source NaNs:**
   ```python
   print(df.isnull().sum())  # Count nulls per column
   print(df.isnull().sum().sum())  # Total nulls
   ```

2. **Fill NaN strategically:**
   ```python
   # Forward fill for time series
   df = df.fillna(method='ffill')
   
   # Fill with zero
   df = df.fillna(0)
   
   # Fill with mean
   df = df.fillna(df.mean())
   ```

3. **Drop NaN rows:**
   ```python
   # Drop any NaN
   df = df.dropna()
   
   # Drop NaN in specific columns
   df = df.dropna(subset=['critical_column'])
   ```

---

## Error Reference

### By Error Type

**InvalidParameterError:**
- Check parameter types
- Verify column names exist
- Ensure value ranges are valid

**MissingDataError:**
- Check for null values
- Verify data exists before operation
- Filter appropriately

**TypeError:**
- Check data types with `df.dtypes`
- Convert columns to correct type
- Use `pd.to_numeric()` for numbers

**ValueError:**
- Check aggregation function validity
- Verify column names for operations
- Ensure operation is compatible with data

**ComputationError:**
- Check for memory issues
- Verify data is valid (no infinity/NaN)
- Filter before complex operations

---

## Advanced Debugging

### Enable Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('aggregator')
```

### Inspect Metadata

```python
result = agg.aggregate(data=df, operations=[...])

print("Operation Data:")
for key, value in result.data.items():
    print(f"  {key}: {value}")

print("\nErrors:")
for error in result.errors:
    print(f"  Type: {error.error_type}")
    print(f"  Message: {error.message}")
    print(f"  Suggestion: {error.suggestion}")
```

### Profile Performance

```python
import time

start = time.time()
result = agg.aggregate(data=df, operations=[...])
end = time.time()

print(f"Execution time: {end - start:.2f}s")
print(f"Quality score: {result.quality_score:.2%}")
```

---

## Contact & Support

- **Issues:** GitHub Issues
- **Documentation:** See docs/ folder
- **Testing:** See tests/ folder

**Last Updated:** 2025-12-13
