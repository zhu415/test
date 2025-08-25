import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple

def aggregate_and_compare_weights(
df1: pd.DataFrame,
wesByIndex: Dict[str, Dict[str, pd.DataFrame]],
mapping_csv_path: str,
mapped_index: str,
datetime_col: str,
bm_key: str = ‘continuous bm’,
debug: bool = False
) -> pd.DataFrame:
“””
Aggregate weights by asset class and RF, then compare with wesByIndex data.

```
Parameters:
-----------
df1 : pd.DataFrame
    DataFrame with columns: 'mapped_index', 'component sub index', 'source_weight',
    'borrow shift 6m', 'borrow shift 1y', 'borrow shift 2y', datetime column
wesByIndex : Dict
    Nested dictionary with structure {bm_key: {index_name: DataFrame}}
mapping_csv_path : str
    Path to CSV file containing asset class mappings
mapped_index : str
    The index name to process
datetime_col : str
    The specific datetime to compare
bm_key : str
    Key for benchmark data (default: 'continuous bm')
debug : bool
    Print debug information

Returns:
--------
pd.DataFrame with comparison results
"""

# Load mapping CSV
mapping_df = pd.read_csv(mapping_csv_path)

# Filter df1 for the specific index and datetime
df1_filtered = df1[(df1['mapped_index'] == mapped_index) & 
                   (df1[datetime_col] == datetime_col)].copy()

if df1_filtered.empty:
    print(f"No data found for index {mapped_index} on date {datetime_col}")
    return pd.DataFrame()

# Get df2 from wesByIndex
if mapped_index not in wesByIndex[bm_key]:
    print(f"Index {mapped_index} not found in wesByIndex")
    return pd.DataFrame()

df2 = wesByIndex[bm_key][mapped_index]

if datetime_col not in df2.columns:
    print(f"Date {datetime_col} not found in wesByIndex for {mapped_index}")
    return pd.DataFrame()

# Aggregate weights from df1
df1_aggregated = aggregate_weights_by_category(
    df1_filtered, mapping_df, mapped_index, debug
)

# Extract weights from df2
df2_weights = extract_weights_from_wesByIndex(
    df2, datetime_col, mapping_df, mapped_index, debug
)

# Compare the two sets of weights
comparison_results = compare_weights(df1_aggregated, df2_weights)

return comparison_results
```

def aggregate_weights_by_category(
df: pd.DataFrame,
mapping_df: pd.DataFrame,
mapped_index: str,
debug: bool = False
) -> Dict:
“””
Aggregate weights by asset class and rolling futures.
“””
results = {
‘sub_index_weights’: {},
‘asset_class_weights’: {},
‘rolling_futures_weight’: 0.0,
‘borrow_shift’: {}
}

```
# Get mapping for this index
index_mapping = mapping_df[mapping_df['index'] == mapped_index]

# Process each sub-index
for _, row in df.iterrows():
    sub_index = row['component sub index']
    weight = row['source_weight']
    
    # Store individual sub-index weight
    results['sub_index_weights'][sub_index] = weight
    
    # Find asset class and RF status from mapping
    asset_class = 'Unknown'
    is_rf = False
    
    if not index_mapping.empty:
        # Match sub_index with underlier in mapping
        underlier_match = index_mapping[index_mapping['underlier'] == sub_index]
        
        # Try with stripped whitespace if no exact match
        if underlier_match.empty:
            underlier_match = index_mapping[index_mapping['underlier'].str.strip() == sub_index.strip()]
        
        if not underlier_match.empty:
            # Get asset class
            if 'asset class' in underlier_match.columns:
                asset_class = underlier_match.iloc[0]['asset class']
            elif 'asset_class' in underlier_match.columns:
                asset_class = underlier_match.iloc[0]['asset_class']
            
            # Check if it's RF
            if 'RF' in underlier_match.columns:
                rf_value = underlier_match.iloc[0]['RF']
                is_rf = (rf_value == 'Y' or rf_value == 'Yes' or rf_value == True or rf_value == 1)
    
    # Aggregate by asset class
    if asset_class != 'Unknown':
        if asset_class not in results['asset_class_weights']:
            results['asset_class_weights'][asset_class] = 0.0
        results['asset_class_weights'][asset_class] += weight
    
    # Aggregate rolling futures
    if is_rf:
        results['rolling_futures_weight'] += weight

# Get borrow shift values (should be same for all rows of same index/date)
if not df.empty:
    first_row = df.iloc[0]
    for tenor in ['6m', '1y', '2y']:
        col_name = f'borrow shift {tenor}'
        if col_name in df.columns:
            results['borrow_shift'][tenor] = first_row[col_name]

if debug:
    print(f"\nDF1 Aggregated Results:")
    print(f"Asset Class Weights: {results['asset_class_weights']}")
    print(f"Rolling Futures Weight: {results['rolling_futures_weight']}")
    print(f"Borrow Shifts: {results['borrow_shift']}")

return results
```

def extract_weights_from_wesByIndex(
df: pd.DataFrame,
date_col: str,
mapping_df: pd.DataFrame,
mapped_index: str,
debug: bool = False
) -> Dict:
“””
Extract weights from wesByIndex DataFrame for comparison.
“””
results = {
‘sub_index_weights’: {},
‘asset_class_weights’: {},
‘rolling_futures_weight’: 0.0,
‘borrow_shift’: {}
}

```
# Get mapping for this index
index_mapping = mapping_df[mapping_df['index'] == mapped_index]

# Extract constituent weights
for idx in df.index:
    if isinstance(idx, tuple):
        if idx[0] == 'constituentId':
            sub_index = idx[1]
            weight = df.loc[idx, date_col]
            results['sub_index_weights'][sub_index] = weight
            
            # Find asset class from mapping
            asset_class = 'Unknown'
            is_rf = False
            
            if not index_mapping.empty:
                underlier_match = index_mapping[index_mapping['underlier'] == sub_index]
                
                if underlier_match.empty:
                    underlier_match = index_mapping[index_mapping['underlier'].str.strip() == sub_index.strip()]
                
                if not underlier_match.empty:
                    if 'asset class' in underlier_match.columns:
                        asset_class = underlier_match.iloc[0]['asset class']
                    elif 'asset_class' in underlier_match.columns:
                        asset_class = underlier_match.iloc[0]['asset_class']
                    
                    if 'RF' in underlier_match.columns:
                        rf_value = underlier_match.iloc[0]['RF']
                        is_rf = (rf_value == 'Y' or rf_value == 'Yes' or rf_value == True or rf_value == 1)
            
            # Aggregate by asset class
            if asset_class != 'Unknown':
                if asset_class not in results['asset_class_weights']:
                    results['asset_class_weights'][asset_class] = 0.0
                results['asset_class_weights'][asset_class] += weight
            
            # Aggregate rolling futures
            if is_rf:
                results['rolling_futures_weight'] += weight
        
        # Extract asset class weights directly (as a check)
        elif idx[0] == 'assetClass':
            # These are already aggregated in df2, can use for validation
            pass
        
        # Extract rolling futures weight
        elif idx[0] == 'isRollingFutures' and idx[1] == 'RF':
            # This is already aggregated in df2
            # Can override our calculation if you trust this more
            # results['rolling_futures_weight'] = df.loc[idx, date_col]
            pass
        
        # Extract borrow shift
        elif idx[0] == 'Borrow Shift':
            tenor = idx[1]
            results['borrow_shift'][tenor] = df.loc[idx, date_col]

if debug:
    print(f"\nDF2 (wesByIndex) Results:")
    print(f"Asset Class Weights: {results['asset_class_weights']}")
    print(f"Rolling Futures Weight: {results['rolling_futures_weight']}")
    print(f"Borrow Shifts: {results['borrow_shift']}")

return results
```

def compare_weights(df1_weights: Dict, df2_weights: Dict) -> pd.DataFrame:
“””
Compare weights between two sources and calculate absolute differences.
“””
comparison_data = []

```
# Compare sub-index weights
all_sub_indices = set(df1_weights['sub_index_weights'].keys()) | set(df2_weights['sub_index_weights'].keys())

for sub_index in all_sub_indices:
    weight1 = df1_weights['sub_index_weights'].get(sub_index, 0.0)
    weight2 = df2_weights['sub_index_weights'].get(sub_index, 0.0)
    comparison_data.append({
        'Category': 'Sub-Index',
        'Name': sub_index,
        'DF1_Weight': weight1,
        'DF2_Weight': weight2,
        'Absolute_Difference': abs(weight1 - weight2)
    })

# Compare asset class weights
all_asset_classes = set(df1_weights['asset_class_weights'].keys()) | set(df2_weights['asset_class_weights'].keys())

for asset_class in all_asset_classes:
    weight1 = df1_weights['asset_class_weights'].get(asset_class, 0.0)
    weight2 = df2_weights['asset_class_weights'].get(asset_class, 0.0)
    comparison_data.append({
        'Category': 'Asset Class',
        'Name': asset_class,
        'DF1_Weight': weight1,
        'DF2_Weight': weight2,
        'Absolute_Difference': abs(weight1 - weight2)
    })

# Compare rolling futures weight
comparison_data.append({
    'Category': 'Rolling Futures',
    'Name': 'Total RF',
    'DF1_Weight': df1_weights['rolling_futures_weight'],
    'DF2_Weight': df2_weights['rolling_futures_weight'],
    'Absolute_Difference': abs(df1_weights['rolling_futures_weight'] - 
                              df2_weights['rolling_futures_weight'])
})

# Compare borrow shift for each tenor
for tenor in ['6m', '1y', '2y']:
    weight1 = df1_weights['borrow_shift'].get(tenor, 0.0)
    weight2 = df2_weights['borrow_shift'].get(tenor, 0.0)
    comparison_data.append({
        'Category': 'Borrow Shift',
        'Name': f'Tenor {tenor}',
        'DF1_Weight': weight1,
        'DF2_Weight': weight2,
        'Absolute_Difference': abs(weight1 - weight2)
    })

# Create DataFrame
comparison_df = pd.DataFrame(comparison_data)

# Sort by category and then by absolute difference (largest first)
comparison_df = comparison_df.sort_values(['Category', 'Absolute_Difference'], 
                                          ascending=[True, False])

return comparison_df
```

def print_comparison_summary(comparison_df: pd.DataFrame):
“””
Print a formatted summary of the comparison results.
“””
print(”\n” + “=”*80)
print(“WEIGHT COMPARISON SUMMARY”)
print(”=”*80)

```
categories = comparison_df['Category'].unique()

for category in categories:
    cat_df = comparison_df[comparison_df['Category'] == category]
    print(f"\n{category}:")
    print("-" * 40)
    
    for _, row in cat_df.iterrows():
        print(f"  {row['Name']:30s}: DF1={row['DF1_Weight']:8.4f}, "
              f"DF2={row['DF2_Weight']:8.4f}, Diff={row['Absolute_Difference']:8.4f}")

print("\n" + "="*80)

# Highlight largest differences
top_diffs = comparison_df.nlargest(5, 'Absolute_Difference')
if not top_diffs.empty:
    print("\nTop 5 Largest Differences:")
    print("-" * 40)
    for _, row in top_diffs.iterrows():
        print(f"  {row['Category']} - {row['Name']}: {row['Absolute_Difference']:.4f}")
```

# Example usage

if **name** == “**main**”:
# Example call
# comparison_results = aggregate_and_compare_weights(
#     df1=your_dataframe,
#     wesByIndex=your_wesByIndex,
#     mapping_csv_path=“mapping.csv”,
#     mapped_index=“INDEX1”,
#     datetime_col=“2024-01-15”,
#     debug=True
# )
#
# print_comparison_summary(comparison_results)
