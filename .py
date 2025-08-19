
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
    result_df['rescaled_weight'] = result_df[weight_col] # Initialize with original weights
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
            # ***BUG FIX: Add all df2 dates within the interval to used_dates***
            if current_ratio < 0: # Rule 1: negative first
                # Left exclusive, right inclusive: (left_date, right_date]
                mask = (result_df[date_col] > left_date) & (result_df[date_col] <= right_date)
                # Add all df2 dates in the interval (left_date, right_date] to used_dates
                df2_interval_mask = (df2_sorted[date_col] > left_date) & (df2_sorted[date_col] <= right_date)
            else: # Rule 2; positive first
                # Left inclusive, right exclusive: [left_date, right_date)
                mask = (result_df[date_col] >= left_date) & (result_df[date_col] < right_date)
                # Add all df2 dates in the interval [left_date, right_date) to used_dates
                df2_interval_mask = (df2_sorted[date_col] >= left_date) & (df2_sorted[date_col] < right_date)
            # Add all df2 dates within the interval to used_dates
            dates_in_interval = df2_sorted.loc[df2_interval_mask, date_col].tolist()
            used_dates.update(dates_in_interval)
            
            # Print message if the time period contains more than 2 elements (left, right + others)
            if len(dates_in_interval) > 0:  # More than just left and right points
                print(f"Time period contains {len(dates_in_interval) + 2} dates (including endpoints):")
                print(f"  Left endpoint: {left_date} (ratio: {current_ratio:.3f})")
                for date in dates_in_interval:
                    ratio_value = df2_sorted.loc[df2_sorted[date_col] == date, ratio_col].iloc[0]
                    print(f"  Internal date: {date} (ratio: {ratio_value:.3f})")
                print(f"  Right endpoint: {right_date} (ratio: {df2_sorted.loc[next_idx, ratio_col]:.3f})")
                print()
            
            # Apply rescaling factor of 4/3
            result_df.loc[mask, 'rescaled_weight'] *= 4/3
            
            # Create interval string based on the actual mask logic
            if current_ratio < 0:  # negative first: (left_date, right_date]
                interval_str = f"({left_date.strftime('%Y-%m-%d')}, {right_date.strftime('%Y-%m-%d')}]"
            else:  # positive first: [left_date, right_date)
                interval_str = f"[{left_date.strftime('%Y-%m-%d')}, {right_date.strftime('%Y-%m-%d')})"
            rescale_intervals.append(interval_str)
        
            print(f"Applied rescaling for dates between {left_date} and {right_date}")
            print(f" Current ratio: {current_ratio:.3f} ({'negative' if current_ratio < 0 else 'positive'})")
            print(f" Next ratio: {df2_sorted.loc[next_idx, 'ratio']:.3f}")
            print(f" Interval: {'(' if current_ratio < 0 else '['}{left_date}, {right_date}{']' if current_ratio < 0 else ')'}")
            print(f" Rows affected in df1: {mask.sum()}")
            print(f" df2 dates marked as used in interval: {len(dates_in_interval)}")
            
            # Debug: Show which dates in df1 are being rescaled
            if mask.sum() > 0:
                rescaled_dates = result_df.loc[mask, date_col].unique()
                print(f" First few rescaled dates in df1: {sorted(rescaled_dates)[:5]}")
                if len(rescaled_dates) > 5:
                    print(f" Last few rescaled dates in df1: {sorted(rescaled_dates)[-5:]}")
            print()
        
        i += 1
        
    return result_df, rescale_intervals
        
