import pandas as pd

def rescale_weights_by_ratio_pattern(df1, df2,
        date_col='date',
        weight_col='sum_weight_excl_USD_CASH',
        ratio_col='ratio',
        verbose=True):
    """
    Rescale weights in df1 based on ratio patterns in df2.
    Rules (processing in CHRONOLOGICAL order - earliest to latest):
    1. Process both positive-to-negative and negative-to-positive patterns
    2. For each sign change: rescale weights for the time period between them
    3. After finding a pair, continue to next available date
    
    Args:
        df1 (DataFrame): Contains 'weight' and 'date' columns
        df2 (DataFrame): Contains 'ratio' and 'date' columns (subset of df1 dates)
        verbose (bool): Whether to print detailed output
        
    Returns:
        tuple: (
            DataFrame with rescaled_weight column,
            list of interval strings,
            DataFrame with detailed interval information,
            DataFrame with intervals containing intermediate dates
        )
    """
    # Create a copy to avoid modifying original
    result_df = df1.copy()
    result_df['rescaled_weight'] = result_df[weight_col]  # Initialize with original weights
    
    # Lists to store interval information
    rescale_intervals = []
    interval_details = []  # Store detailed info for each interval
    
    # Sort df2 by date to ensure proper sequence (chronological order)
    df2_sorted = df2.sort_values(date_col).reset_index(drop=True)
    
    # Track which dates have been used
    used_dates = set()
    
    i = 0
    while i < len(df2_sorted):
        current_date = df2_sorted.loc[i, date_col]
        current_ratio = df2_sorted.loc[i, ratio_col]
        
        # Skip if this date was already used
        if current_date in used_dates:
            i += 1
            continue
        
        # Find the next date with opposite sign ratio
        next_idx = None
        for j in range(i + 1, len(df2_sorted)):
            next_date = df2_sorted.loc[j, date_col]
            next_ratio = df2_sorted.loc[j, ratio_col]
            
            # Skip already used dates
            if next_date in used_dates:
                continue
            
            # Check if we found opposite sign
            if (current_ratio < 0 and next_ratio > 0) or (current_ratio > 0 and next_ratio < 0):
                next_idx = j
                break
        
        # If we found a pair, apply rescaling
        if next_idx is not None:
            left_date = current_date
            right_date = df2_sorted.loc[next_idx, date_col]
            right_ratio = df2_sorted.loc[next_idx, ratio_col]
            
            # Mark these dates as used
            used_dates.add(left_date)
            used_dates.add(right_date)
            
            # Define masks for rescaling and for finding intermediate df2 dates
            if current_ratio < 0:  # Rule 1: negative first
                # Left exclusive, right inclusive: (left_date, right_date]
                rescale_mask = (result_df[date_col] > left_date) & (result_df[date_col] <= right_date)
                df2_interval_mask = (df2_sorted[date_col] > left_date) & (df2_sorted[date_col] < right_date)
                interval_notation = f"({left_date.strftime('%Y-%m-%d')}, {right_date.strftime('%Y-%m-%d')}]"
                interval_type = "negative_to_positive"
            else:  # Rule 2: positive first
                # Left inclusive, right exclusive: [left_date, right_date)
                rescale_mask = (result_df[date_col] >= left_date) & (result_df[date_col] < right_date)
                df2_interval_mask = (df2_sorted[date_col] > left_date) & (df2_sorted[date_col] < right_date)
                interval_notation = f"[{left_date.strftime('%Y-%m-%d')}, {right_date.strftime('%Y-%m-%d')})"
                interval_type = "positive_to_negative"
            
            # Get intermediate dates and their ratios
            intermediate_df = df2_sorted[df2_interval_mask].copy()
            dates_in_interval = intermediate_df[date_col].tolist()
            used_dates.update(dates_in_interval)
            
            # Apply rescaling factor of 4/3
            result_df.loc[rescale_mask, 'rescaled_weight'] *= 4/3
            
            # Add interval to list
            rescale_intervals.append(interval_notation)
            
            # Collect all dates in this interval with their ratios
            interval_dates_info = []
            
            # Add left endpoint
            interval_dates_info.append({
                'date': left_date,
                'ratio': current_ratio,
                'role': 'left_endpoint',
                'included_in_rescale': current_ratio > 0  # included if positive (rule 2)
            })
            
            # Add intermediate dates
            for _, row in intermediate_df.iterrows():
                interval_dates_info.append({
                    'date': row[date_col],
                    'ratio': row[ratio_col],
                    'role': 'intermediate',
                    'included_in_rescale': True  # always included
                })
            
            # Add right endpoint
            interval_dates_info.append({
                'date': right_date,
                'ratio': right_ratio,
                'role': 'right_endpoint',
                'included_in_rescale': current_ratio < 0  # included if negative (rule 1)
            })
            
            # Store detailed interval information
            interval_detail = {
                'interval_index': len(interval_details),
                'interval_notation': interval_notation,
                'interval_type': interval_type,
                'left_date': left_date,
                'left_ratio': current_ratio,
                'right_date': right_date,
                'right_ratio': right_ratio,
                'num_intermediate_dates': len(dates_in_interval),
                'intermediate_dates': dates_in_interval,
                'all_dates_with_ratios': interval_dates_info,
                'rows_rescaled_in_df1': rescale_mask.sum()
            }
            interval_details.append(interval_detail)
            
            # Print detailed information if verbose
            if verbose:
                print(f"Interval {len(interval_details)}: {interval_notation}")
                print(f"  Type: {interval_type}")
                print(f"  Rows rescaled in df1: {rescale_mask.sum()}")
                if len(dates_in_interval) > 0:
                    print(f"  Contains {len(dates_in_interval)} intermediate df2 dates")
                print()
        
        i += 1
    
    # Create summary DataFrames
    
    # 1. Overall interval summary
    interval_summary_df = pd.DataFrame([
        {
            'interval_index': d['interval_index'],
            'interval': d['interval_notation'],
            'type': d['interval_type'],
            'num_intermediate': d['num_intermediate_dates'],
            'rows_rescaled': d['rows_rescaled_in_df1']
        }
        for d in interval_details
    ])
    
    # 2. Detailed view of intervals with intermediate dates
    intervals_with_intermediates = []
    for detail in interval_details:
        if detail['num_intermediate_dates'] > 0:
            # Create a DataFrame for this interval's dates
            dates_df = pd.DataFrame(detail['all_dates_with_ratios'])
            dates_df['interval_index'] = detail['interval_index']
            dates_df['interval_notation'] = detail['interval_notation']
            intervals_with_intermediates.append(dates_df)
    
    # Combine all intervals with intermediate dates into one DataFrame
    if intervals_with_intermediates:
        intervals_with_intermediates_df = pd.concat(intervals_with_intermediates, ignore_index=True)
        # Reorder columns for better readability
        intervals_with_intermediates_df = intervals_with_intermediates_df[[
            'interval_index', 'interval_notation', 'date', 'ratio', 'role', 'included_in_rescale'
        ]]
    else:
        intervals_with_intermediates_df = pd.DataFrame()
    
    # Print summary if verbose
    if verbose:
        print("=" * 60)
        print("RESCALING SUMMARY")
        print("=" * 60)
        print(f"Total intervals processed: {len(rescale_intervals)}")
        print(f"Intervals with intermediate dates: {sum(1 for d in interval_details if d['num_intermediate_dates'] > 0)}")
        print(f"Total df2 dates used: {len(used_dates)} out of {len(df2_sorted)}")
        
        if not interval_summary_df.empty:
            print("\nInterval Summary:")
            print(interval_summary_df.to_string())
        
        if not intervals_with_intermediates_df.empty:
            print("\n" + "=" * 60)
            print("INTERVALS WITH INTERMEDIATE DATES (DETAILED VIEW)")
            print("=" * 60)
            for idx in intervals_with_intermediates_df['interval_index'].unique():
                interval_data = intervals_with_intermediates_df[
                    intervals_with_intermediates_df['interval_index'] == idx
                ]
                print(f"\nInterval {idx}: {interval_data['interval_notation'].iloc[0]}")
                print(interval_data[['date', 'ratio', 'role', 'included_in_rescale']].to_string(index=False))
    
    return result_df, rescale_intervals, interval_summary_df, intervals_with_intermediates_df


def view_intervals_with_intermediates(intervals_df, interval_index=None):
    """
    Helper function to nicely view intervals that contain intermediate dates
    
    Args:
        intervals_df: The intervals_with_intermediates_df returned from rescale_weights_by_ratio_pattern
        interval_index: Optional specific interval index to view. If None, shows all.
    
    Returns:
        None (prints formatted output)
    """
    if intervals_df.empty:
        print("No intervals with intermediate dates found.")
        return
    
    if interval_index is not None:
        # View specific interval
        interval_data = intervals_df[intervals_df['interval_index'] == interval_index]
        if interval_data.empty:
            print(f"No interval found with index {interval_index}")
            return
        
        print(f"Interval {interval_index}: {interval_data['interval_notation'].iloc[0]}")
        print("-" * 60)
        for _, row in interval_data.iterrows():
            marker = "✓" if row['included_in_rescale'] else "✗"
            role_str = f"[{row['role'].upper()}]".ljust(20)
            print(f"  {marker} {row['date']} {role_str} ratio: {row['ratio']:8.3f}")
    else:
        # View all intervals
        for idx in intervals_df['interval_index'].unique():
            interval_data = intervals_df[intervals_df['interval_index'] == idx]
            print(f"\nInterval {idx}: {interval_data['interval_notation'].iloc[0]}")
            print("-" * 60)
            for _, row in interval_data.iterrows():
                marker = "✓" if row['included_in_rescale'] else "✗"
                role_str = f"[{row['role'].upper()}]".ljust(20)
                print(f"  {marker} {row['date']} {role_str} ratio: {row['ratio']:8.3f}")
        
        print("\n" + "=" * 60)
        print("Legend: ✓ = included in rescaling, ✗ = excluded from rescaling")


# Example usage:
"""
# Run the function
result_df, intervals, summary_df, intermediates_df = rescale_weights_by_ratio_pattern(
    df1, df2, verbose=True
)

# View all intervals with intermediate dates
view_intervals_with_intermediates(intermediates_df)

# View a specific interval
view_intervals_with_intermediates(intermediates_df, interval_index=0)

# Or directly explore the DataFrames
print(summary_df)  # Quick overview of all intervals
print(intermediates_df)  # Detailed view of intervals with intermediate dates

# Filter to see only intervals with many intermediate dates
many_intermediates = summary_df[summary_df['num_intermediate'] > 2]
print(many_intermediates)

# Export to CSV for external viewing
intermediates_df.to_csv('intervals_with_intermediates.csv', index=False)
summary_df.to_csv('interval_summary.csv', index=False)
"""
