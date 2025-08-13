import pandas as pd
import numpy as np

def rescale_weights_by_ratio_pattern(df1, df2):
    """
    Rescale weights in df1 based on ratio patterns in df2.
    
    Rules (processing in REVERSE time order - latest to earliest):
    1. Only process positive-to-negative patterns
    2. For positive first: find next negative ratio  
       - Rescale weights for dates [left_date, right_date) (left inclusive, right exclusive)
    3. After finding a positive-negative pair, continue to next first positive
       (skip any negatives in between)
    
    Args:
        df1 (DataFrame): Contains 'weight' and 'date' columns
        df2 (DataFrame): Contains 'ratio' and 'date' columns (subset of df1 dates)
    
    Returns:
        tuple: (DataFrame with rescaled_weight column, list of interval strings)
    """
    
    # Create a copy to avoid modifying original
    result_df = df1.copy()
    result_df['rescaled_weight'] = result_df['weight']  # Initialize with original weights
    
    # List to store interval strings
    rescale_intervals = []
    
    # Sort df2 by date in DESCENDING order (latest to earliest)
    df2_sorted = df2.sort_values('date', ascending=False).reset_index(drop=True)
    
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
        
        # Only process if current ratio is POSITIVE
        if current_ratio <= 0:
            i += 1
            continue
            
        # Find the next NEGATIVE ratio (going backwards in time)
        next_idx = None
        for j in range(i + 1, len(df2_sorted)):
            next_date = df2_sorted.loc[j, 'date']
            next_ratio = df2_sorted.loc[j, 'ratio']
            
            # Skip already used dates
            if next_date in used_dates:
                continue
                
            # Check if we found a negative ratio
            if next_ratio < 0:
                next_idx = j
                break
        
        # If we found a positive-negative pair, apply rescaling
        if next_idx is not None:
            # Note: In reverse order, current_date is later than next_date
            later_date = current_date  # positive ratio date (later in time)
            earlier_date = df2_sorted.loc[next_idx, 'date']  # negative ratio date (earlier in time)
            
            # Mark these dates as used
            used_dates.add(later_date)
            used_dates.add(earlier_date)
            
            # Apply positive-first rule: [left_date, right_date) (left inclusive, right exclusive)
            # Since we're going backwards, left_date is the earlier date, right_date is the later date
            mask = (result_df['date'] >= earlier_date) & (result_df['date'] < later_date)
            
            # Apply rescaling factor of 4/3
            result_df.loc[mask, 'rescaled_weight'] *= 4/3
            
            # Create interval string and add to list
            interval_str = f"[{earlier_date.strftime('%Y-%m-%d')}, {later_date.strftime('%Y-%m-%d')})"
            rescale_intervals.append(interval_str)
            
            print(f"Applied rescaling for positive-to-negative pattern:")
            print(f"  Positive ratio: {current_ratio:.3f} at {later_date}")
            print(f"  Negative ratio: {df2_sorted.loc[next_idx, 'ratio']:.3f} at {earlier_date}")
            print(f"  Interval: {interval_str} (left inclusive, right exclusive)")
            print(f"  Rows affected: {mask.sum()}")
            print()
        
        i += 1
    
    return result_df, rescale_intervals
