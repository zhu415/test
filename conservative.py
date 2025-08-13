def rescale_weights_by_ratio_pattern(df1, df2):
    """
    Rescale weights in df1 based on ratio patterns in df2.
    
    Rules:
    1. If first ratio is negative: find next positive ratio
       - Rescale weights for dates (left_date, right_date] (left exclusive, right inclusive)
    2. If first ratio is positive: find next negative ratio  
       - Rescale weights for dates [left_date, right_date) (left inclusive, right exclusive)
    3. Move to next unused dates after each pair is processed
    
    Args:
        df1 (DataFrame): Contains 'weight' and 'date' columns
        df2 (DataFrame): Contains 'ratio' and 'date' columns (subset of df1 dates)
    
    Returns:
        DataFrame: df1 with new 'rescaled_weight' column
    """
    
    # Create a copy to avoid modifying original
    result_df = df1.copy()
    result_df['rescaled_weight'] = result_df['weight']  # Initialize with original weights
    
    # Sort df2 by date to ensure proper sequence
    df2_sorted = df2.sort_values('date').reset_index(drop=True)
    
    # Track which dates have been used
    used_dates = set()
    
    i = 0
    while i < len(df2_sorted):
        current_date = df2_sorted.loc[i, 'date']
        current_ratio = df2_sorted.loc[i, 'ratio']
        
        # Skip if this date was already used
        if current_date in used_dates:
            i += 1
            continue
            
        # Find the next date with opposite sign ratio
        next_idx = None
        target_sign = current_ratio > 0  # True if current is positive, False if negative
        
        for j in range(i + 1, len(df2_sorted)):
            next_date = df2_sorted.loc[j, 'date']
            next_ratio = df2_sorted.loc[j, 'ratio']
            
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
            right_date = df2_sorted.loc[next_idx, 'date']
            
            # Mark these dates as used
            used_dates.add(left_date)
            used_dates.add(right_date)
            
            if current_ratio < 0:  # Rule 1: negative first
                # Left exclusive, right inclusive: (left_date, right_date]
                mask = (result_df['date'] > left_date) & (result_df['date'] <= right_date)
            else:  # Rule 2: positive first  
                # Left inclusive, right exclusive: [left_date, right_date)
                mask = (result_df['date'] >= left_date) & (result_df['date'] < right_date)
            
            # Apply rescaling factor of 4/3
            result_df.loc[mask, 'rescaled_weight'] *= 4/3
            
            print(f"Applied rescaling for dates between {left_date} and {right_date}")
            print(f"  Current ratio: {current_ratio:.3f} ({'negative' if current_ratio < 0 else 'positive'})")
            print(f"  Next ratio: {df2_sorted.loc[next_idx, 'ratio']:.3f}")
            print(f"  Interval: {'(' if current_ratio < 0 else '['}{left_date}, {right_date}{']' if current_ratio < 0 else ')'}")
            print(f"  Rows affected: {mask.sum()}")
            print()
        
        i += 1
    
    return result_df
