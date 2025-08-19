def rescale_weights_by_ratio_pattern(df1, df2,
        date_col='date',
        weight_col='sum_weight_excl_USD_CASH',
        ratio_col='ratio'):
    """
    Rescale weights in df1 based on ratio patterns in df2.
    Rules (processing in CHRONOLOGICAL order - earliest to latest):
    1. Process both positive-to-negative and negative-to-positive patterns
    2. For each sign change: rescale weights for the time period between them
    3. After finding a pair, continue to next available date
    Args:
        df1 (DataFrame): Contains 'weight' and 'date' columns
        df2 (DataFrame): Contains 'ratio' and 'date' columns (subset of df1 dates)
    Returns:
        tuple: (DataFrame with rescaled_weight column, list of interval strings)
    """
    # Create a copy to avoid modifying original
    result_df = df1.copy()
    result_df['rescaled_weight'] = result_df[weight_col]  # Initialize with original weights
    
    # List to store interval strings
    rescale_intervals = []
    
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
            
            # Mark these dates as used
            used_dates.add(left_date)
            used_dates.add(right_date)
            
            # Define masks for rescaling and for finding intermediate df2 dates
            if current_ratio < 0:  # Rule 1: negative first
                # Left exclusive, right inclusive: (left_date, right_date]
                rescale_mask = (result_df[date_col] > left_date) & (result_df[date_col] <= right_date)
                # For df2 dates to mark as used: same interval (left_date, right_date]
                # But we exclude right_date since it's already added to used_dates
                df2_interval_mask = (df2_sorted[date_col] > left_date) & (df2_sorted[date_col] < right_date)
                interval_notation = f"({left_date.strftime('%Y-%m-%d')}, {right_date.strftime('%Y-%m-%d')}]"
            else:  # Rule 2: positive first
                # Left inclusive, right exclusive: [left_date, right_date)
                rescale_mask = (result_df[date_col] >= left_date) & (result_df[date_col] < right_date)
                # For df2 dates to mark as used: same interval [left_date, right_date)
                # But we exclude left_date since it's already added to used_dates
                df2_interval_mask = (df2_sorted[date_col] > left_date) & (df2_sorted[date_col] < right_date)
                interval_notation = f"[{left_date.strftime('%Y-%m-%d')}, {right_date.strftime('%Y-%m-%d')})"
            
            # Add all df2 dates within the interval to used_dates
            dates_in_interval = df2_sorted.loc[df2_interval_mask, date_col].tolist()
            used_dates.update(dates_in_interval)
            
            # Apply rescaling factor of 4/3
            result_df.loc[rescale_mask, 'rescaled_weight'] *= 4/3
            
            # Add interval to list
            rescale_intervals.append(interval_notation)
            
            # Print detailed information
            print(f"Applied rescaling for interval: {interval_notation}")
            print(f"  Left endpoint: {left_date} (ratio: {current_ratio:.3f}, {'negative' if current_ratio < 0 else 'positive'})")
            print(f"  Right endpoint: {right_date} (ratio: {df2_sorted.loc[next_idx, ratio_col]:.3f})")
            
            # Show intermediate df2 dates if any
            if len(dates_in_interval) > 0:
                print(f"  Intermediate df2 dates marked as used ({len(dates_in_interval)} dates):")
                for date in dates_in_interval:
                    ratio_value = df2_sorted.loc[df2_sorted[date_col] == date, ratio_col].iloc[0]
                    print(f"    - {date} (ratio: {ratio_value:.3f})")
            else:
                print(f"  No intermediate df2 dates in this interval")
            
            # Show rescaling statistics
            num_rescaled = rescale_mask.sum()
            print(f"  Rows rescaled in df1: {num_rescaled}")
            
            if num_rescaled > 0:
                # Get the actual dates being rescaled in df1
                rescaled_dates = result_df.loc[rescale_mask, date_col].unique()
                rescaled_dates_sorted = sorted(rescaled_dates)
                
                # Check if the included endpoint is actually in df1
                if current_ratio < 0:  # right endpoint should be included
                    endpoint_in_df1 = right_date in rescaled_dates
                    print(f"  Right endpoint ({right_date}) in df1: {endpoint_in_df1}")
                else:  # left endpoint should be included
                    endpoint_in_df1 = left_date in rescaled_dates
                    print(f"  Left endpoint ({left_date}) in df1: {endpoint_in_df1}")
                
                # Show sample of rescaled dates
                if len(rescaled_dates_sorted) <= 10:
                    print(f"  All rescaled dates in df1: {[d.strftime('%Y-%m-%d') for d in rescaled_dates_sorted]}")
                else:
                    print(f"  First 5 rescaled dates in df1: {[d.strftime('%Y-%m-%d') for d in rescaled_dates_sorted[:5]]}")
                    print(f"  Last 5 rescaled dates in df1: {[d.strftime('%Y-%m-%d') for d in rescaled_dates_sorted[-5:]]}")
            
            print()  # Empty line for readability
        
        i += 1
    
    # Summary statistics
    print("=" * 60)
    print("RESCALING SUMMARY")
    print("=" * 60)
    print(f"Total intervals processed: {len(rescale_intervals)}")
    print(f"Total df2 dates used: {len(used_dates)} out of {len(df2_sorted)}")
    print(f"Unused df2 dates: {len(df2_sorted) - len(used_dates)}")
    
    if len(df2_sorted) > len(used_dates):
        unused_dates = set(df2_sorted[date_col]) - used_dates
        print(f"Unused df2 dates: {sorted(unused_dates)}")
    
    print(f"\nIntervals processed:")
    for interval in rescale_intervals:
        print(f"  - {interval}")
    
    return result_df, rescale_intervals
