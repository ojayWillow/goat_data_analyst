#!/usr/bin/env python3
"""
Test Data Generation Script

Purpose: Generate realistic test data for Phase 2 production testing
Date: December 10, 2025
Status: Ready for execution
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timedelta

# Configuration
OUTPUT_DIR = Path(__file__).parent / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("🧪 Generating test data for Phase 2...\n")

# ============================================================================
# SMALL CSV - Clean data for happy path testing
# ============================================================================

def generate_small_csv():
    """
    Small CSV: 2,000 rows, 10 columns, clean data
    Purpose: Happy path testing (Scenario 1)
    """
    print("1. Generating small_dataset.csv (2K rows, clean)...")
    
    np.random.seed(42)
    n = 2000
    
    data = {
        'id': range(1, n + 1),
        'numeric_1': np.random.randn(n),  # Normal distribution
        'numeric_2': np.random.randint(0, 1000, n),  # Integers 0-1000
        'numeric_3': np.random.uniform(0, 100, n),  # Floats 0-100
        'category_1': np.random.choice(['A', 'B', 'C', 'D'], n),  # Categorical
        'category_2': np.random.choice(['X', 'Y', 'Z'], n),  # Categorical
        'value_1': np.random.exponential(2, n),  # Exponential distribution
        'date': pd.date_range('2024-01-01', periods=n),  # Date column
        'flag': np.random.choice([True, False], n),  # Boolean
        'nullable': [None if np.random.random() < 0.05 else str(i) for i in range(n)]  # 5% missing
    }
    
    df = pd.DataFrame(data)
    output_path = OUTPUT_DIR / 'small_dataset.csv'
    df.to_csv(output_path, index=False)
    
    print(f"   ✅ Created: {output_path}")
    print(f"      Shape: {df.shape}")
    print(f"      Columns: {', '.join(df.columns)}")
    print(f"      Missing values: {df.isnull().sum().sum()}\n")

# ============================================================================
# MEDIUM CSV - Data with quality issues for edge case testing
# ============================================================================

def generate_medium_csv():
    """
    Medium CSV: 100,000 rows, 15 columns, with data quality issues
    Purpose: Edge case testing (Scenario 2) + stress testing (Scenario 3)
    Issues: missing values, duplicates, outliers
    """
    print("2. Generating medium_dataset.csv (100K rows, with issues)...")
    
    np.random.seed(42)
    n = 100000
    
    data = {
        'id': range(1, n + 1),
        'value_1': np.random.randn(n),  # Normal distribution
        'value_2': np.random.randint(0, 1000, n),  # Integers
        'value_3': np.random.uniform(0, 100, n),  # Floats
        'value_4': np.random.exponential(2, n),  # Exponential
        'value_5': np.random.poisson(3, n),  # Poisson distribution
        'cat_1': np.random.choice(['A', 'B', 'C', 'D', 'E'], n),  # Categorical
        'cat_2': np.random.choice(['X', 'Y', 'Z'], n),  # Categorical
        'cat_3': np.random.choice(['P', 'Q', 'R', 'S'], n),  # Categorical
        'date_1': pd.date_range('2024-01-01', periods=n),  # Date sequence
        'date_2': [pd.Timestamp('2024-01-01') + timedelta(days=int(x)) 
                   for x in np.random.randint(0, 365, n)],  # Random dates
        'flag': np.random.choice([True, False], n),  # Boolean
        'nullable_1': [None if np.random.random() < 0.15 else f'val_{i}' 
                       for i in range(n)],  # 15% missing strings
        'nullable_2': [None if np.random.random() < 0.20 else np.random.randint(0, 100) 
                       for _ in range(n)],  # 20% missing integers
        'outlier_col': [1000 if np.random.random() < 0.01 else np.random.uniform(0, 100) 
                        for _ in range(n)]  # 1% outliers
    }
    
    df = pd.DataFrame(data)
    
    # Add duplicates (1% of rows)
    dup_indices = np.random.choice(df.index, size=int(0.01 * n), replace=False)
    df_dups = df.loc[dup_indices].copy()
    df = pd.concat([df, df_dups], ignore_index=True)
    
    output_path = OUTPUT_DIR / 'medium_dataset.csv'
    df.to_csv(output_path, index=False)
    
    print(f"   ✅ Created: {output_path}")
    print(f"      Shape: {df.shape}")
    print(f"      Columns: {', '.join(df.columns)}")
    print(f"      Missing values: {df.isnull().sum().sum()}")
    print(f"      Duplicates: ~{int(0.01 * n)}\n")

# ============================================================================
# JSON FILE - Nested structure
# ============================================================================

def generate_json():
    """
    JSON File: 5,000 records with nested structure
    Purpose: Test DataLoader JSON parsing
    """
    print("3. Generating test_data.json (5K records)...")
    
    np.random.seed(42)
    records = []
    
    for i in range(5000):
        record = {
            'id': i + 1,
            'name': f'record_{i}',
            'value': float(np.random.randn()),
            'category': np.random.choice(['A', 'B', 'C']),
            'timestamp': (pd.Timestamp('2024-01-01') + timedelta(days=i % 365)).isoformat(),
            'metrics': {
                'count': int(np.random.randint(1, 100)),
                'sum': float(np.random.uniform(0, 1000)),
                'average': float(np.random.uniform(0, 100))
            }
        }
        records.append(record)
    
    output_path = OUTPUT_DIR / 'test_data.json'
    with open(output_path, 'w') as f:
        json.dump(records, f, indent=2)
    
    print(f"   ✅ Created: {output_path}")
    print(f"      Records: {len(records)}")
    print(f"      File size: {output_path.stat().st_size / 1024:.1f} KB\n")

# ============================================================================
# EXCEL FILE - Multiple sheets
# ============================================================================

def generate_excel():
    """
    Excel File: 5,000 rows in single sheet
    Purpose: Test DataLoader Excel parsing
    """
    print("4. Generating test_data.xlsx (5K rows)...")
    
    np.random.seed(42)
    n = 5000
    
    data = {
        'id': range(1, n + 1),
        'value_1': np.random.randn(n),
        'value_2': np.random.randint(0, 100, n),
        'category': np.random.choice(['A', 'B', 'C'], n),
        'date': pd.date_range('2024-01-01', periods=n),
        'flag': np.random.choice([True, False], n)
    }
    
    df = pd.DataFrame(data)
    
    output_path = OUTPUT_DIR / 'test_data.xlsx'
    df.to_excel(output_path, index=False, sheet_name='Data')
    
    print(f"   ✅ Created: {output_path}")
    print(f"      Shape: {df.shape}")
    print(f"      Columns: {', '.join(df.columns)}\n")

# ============================================================================
# PARQUET FILE (Optional) - Columnar format
# ============================================================================

def generate_parquet():
    """
    Parquet File: 5,000 rows
    Purpose: Test DataLoader Parquet parsing
    """
    try:
        print("5. Generating test_data.parquet (5K rows)...")
        
        np.random.seed(42)
        n = 5000
        
        data = {
            'id': range(1, n + 1),
            'value_1': np.random.randn(n),
            'value_2': np.random.randint(0, 100, n),
            'category': np.random.choice(['A', 'B', 'C'], n),
            'date': pd.date_range('2024-01-01', periods=n),
        }
        
        df = pd.DataFrame(data)
        
        output_path = OUTPUT_DIR / 'test_data.parquet'
        df.to_parquet(output_path, index=False)
        
        print(f"   ✅ Created: {output_path}")
        print(f"      Shape: {df.shape}\n")
    
    except ImportError:
        print("   ⚠️  Skipped (pyarrow not installed)\n")

# ============================================================================
# METADATA FILE - Test information
# ============================================================================

def generate_metadata():
    """
    Generate metadata about test datasets
    """
    print("6. Generating test_metadata.json...")
    
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "test_datasets": {
            "small_dataset.csv": {
                "purpose": "Happy path testing (Scenario 1)",
                "rows": 2000,
                "columns": 10,
                "data_quality": "Clean",
                "missing_values": "~100 (5%)",
                "duplicates": 0,
                "outliers": 0
            },
            "medium_dataset.csv": {
                "purpose": "Edge case + stress testing (Scenarios 2 & 3)",
                "rows": 101000,  # Includes duplicates
                "columns": 15,
                "data_quality": "With issues",
                "missing_values": "~25000 (15-20%)",
                "duplicates": "~1000 (1%)",
                "outliers": "~1000 (1%)"
            },
            "test_data.json": {
                "purpose": "JSON parsing test",
                "records": 5000,
                "structure": "List of nested objects",
                "fields": 5
            },
            "test_data.xlsx": {
                "purpose": "Excel parsing test",
                "rows": 5000,
                "columns": 6,
                "sheets": 1
            },
            "test_data.parquet": {
                "purpose": "Parquet parsing test (optional)",
                "rows": 5000,
                "columns": 5
            }
        },
        "test_scenarios": {
            "scenario_1_happy_path": {
                "data": "small_dataset.csv",
                "focus": "Normal operation, clean data",
                "expected": "All agents pass without errors"
            },
            "scenario_2_edge_cases": {
                "data": "medium_dataset.csv",
                "focus": "Data quality issues",
                "expected": "Agents handle missing values, duplicates, outliers"
            },
            "scenario_3_stress": {
                "data": "medium_dataset.csv",
                "focus": "Performance under load",
                "expected": "Agents complete within performance targets"
            }
        }
    }
    
    output_path = OUTPUT_DIR / 'test_metadata.json'
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"   ✅ Created: {output_path}\n")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("🧪 TEST DATA GENERATION")
    print("="*80)
    print()
    
    try:
        generate_small_csv()
        generate_medium_csv()
        generate_json()
        generate_excel()
        generate_parquet()
        generate_metadata()
        
        print("="*80)
        print("✅ TEST DATA GENERATION COMPLETE")
        print("="*80)
        print(f"\nOutput directory: {OUTPUT_DIR}")
        print(f"Files created:")
        for file in sorted(OUTPUT_DIR.glob('*')):
            size_mb = file.stat().st_size / 1024 / 1024
            print(f"  ✅ {file.name:30} ({size_mb:.2f} MB)")
        print()
        print("🚀 Ready for Phase 2 testing!\n")
    
    except Exception as e:
        print(f"\n❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()
