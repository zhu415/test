def find_closest_column(
    df: pd.DataFrame,
    columns: List[str],
    tolerance: float,
    start_idx: Optional[int] = None,
    end_idx: Optional[int] = None
) -> Tuple[pd.DataFrame, List, Dict]:
    """
    Compare column values against a reference column and find the closest match for each date.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with 'date' column
    columns: list of str
        List of column names, first column is the reference (e.g., 'normalized_weight')
    tolerance : float
        Tolerance level for comparison
    start_idx : int, optional
        Starting row index (inclusive)
    end_idx : int, optional
        Ending row index (exclusive)
        
    Returns:
    --------
    Tuple of:
        - pd.DataFrame: DataFrame with 'date', 'closest_column', and 'actual_closest' columns
        - List: List of error dates
        - Dict: Dictionary mapping error dates to their closest column and distance
    """
    # Validate inputs
    if 'date' not in df.columns:
        raise ValueError("DataFrame must have 'date' column")
    if len(columns) < 2:
        raise ValueError("Must provide at least 2 columns (reference + comparison)")
    for col in columns:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame")
    
    # Handle row range
    start_idx = start_idx if start_idx is not None else 0
    end_idx = end_idx if end_idx is not None else len(df)
    df_subset = df.iloc[start_idx:end_idx].copy()
    
    reference_col = columns[0]
    comparison_cols = columns[1:]
    
    results = []
    error_dates = []
    error_details = {}  # Store details about errors
    
    for _, row in df_subset.iterrows():
        try:
            date = row['date']
            ref_value = row[reference_col]
            
            # Skip comparison if reference value is zero
            if ref_value == 0:
                results.append({
                    'date': date, 
                    'closest_column': 'zero_value',
                    'actual_closest': 'zero_value',
                    'distance': 0
                })
                continue
            
            # Calculate distances for all columns
            distances = {}
            for col in comparison_cols:
                distances[col] = abs(row[col] - ref_value)
            
            # Find the column with minimum distance
            min_col = min(distances, key=distances.get)
            min_distance = distances[min_col]
            
            # Check which columns are within tolerance
            close_columns = [col for col, dist in distances.items() if dist <= tolerance]
            
            # Determine the result
            if len(close_columns) == 0:
                # No column within tolerance - mark as error but record the closest
                error_msg = f"No column found within tolerance for date {date.strftime('%Y-%m-%d')}. Closest was '{min_col}' with distance {min_distance:.6f}"
                print(error_msg)
                error_dates.append(date)
                error_details[date] = {
                    'closest': min_col,
                    'distance': min_distance,
                    'all_distances': distances.copy()
                }
                results.append({
                    'date': date, 
                    'closest_column': 'error',
                    'actual_closest': min_col,  # Store which was actually closest
                    'distance': min_distance
                })
            elif len(close_columns) > 1:
                # Multiple columns within tolerance - still an error but record the closest
                error_msg = f"Multiple columns found within tolerance for date {date.strftime('%Y-%m-%d')}: {close_columns}. Using closest: '{min_col}'"
                print(error_msg)
                error_dates.append(date)
                error_details[date] = {
                    'closest': min_col,
                    'distance': min_distance,
                    'multiple_matches': close_columns,
                    'all_distances': distances.copy()
                }
                results.append({
                    'date': date, 
                    'closest_column': 'error',
                    'actual_closest': min_col,
                    'distance': min_distance
                })
            else:
                # Exactly one match - success
                results.append({
                    'date': date, 
                    'closest_column': close_columns[0],
                    'actual_closest': close_columns[0],
                    'distance': distances[close_columns[0]]
                })
                
        except Exception as e:
            date_str = str(row.get('date', 'unknown'))[:10]
            print(f"Error processing row with date {date_str}: {e}")
            error_dates.append(row.get('date', pd.NaT))
            results.append({
                'date': row.get('date', pd.NaT), 
                'closest_column': 'error',
                'actual_closest': 'unknown',
                'distance': float('inf')
            })
            continue
    
    # Create result DataFrame
    result_df = pd.DataFrame(results)
    
    # Print summary of errors if any
    if error_details:
        print(f"\n=== Error Summary: {len(error_details)} dates with issues ===")
        for date, details in error_details.items():
            print(f"\nDate: {date.strftime('%Y-%m-%d')}")
            print(f"  Closest column: {details['closest']} (distance: {details['distance']:.6f})")
            if 'multiple_matches' in details:
                print(f"  Multiple matches within tolerance: {details['multiple_matches']}")
            print(f"  All distances: {', '.join([f'{k}:{v:.6f}' for k, v in details['all_distances'].items()])}")
    
    return result_df, error_dates, error_details



# Create error check DataFrame
error_check_df = pd.DataFrame({'date': rate_error_dates})

# Merge equity weights
error_check_df = error_check_df.merge(
    equity_df[['date', 'weight', 'normalized_weight']], 
    on='date', 
    how='left'
)

# Add closest column info from error details dictionary
error_check_df['closest_column'] = error_check_df['date'].map(
    lambda d: equity_error_details.get(d, {}).get('closest')
)
error_check_df['distance'] = error_check_df['date'].map(
    lambda d: equity_error_details.get(d, {}).get('distance')
)

# Get the value from the closest column
error_check_df['closest_column_value'] = error_check_df.apply(
    lambda row: equity_df.loc[equity_df['date'] == row['date'], row['closest_column']].values[0] 
    if pd.notna(row['closest_column']) else None, 
    axis=1
)
