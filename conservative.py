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
        DataFrame: df1 with new 'rescaled_weight' column
    """
    
    # Create a copy to avoid modifying original
    result_df = df1.copy()
    result_df['rescaled_weight'] = result_df['weight']  # Initialize with original weights
    
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
            
            print(f"Applied rescaling for positive-to-negative pattern:")
            print(f"  Positive ratio: {current_ratio:.3f} at {later_date}")
            print(f"  Negative ratio: {df2_sorted.loc[next_idx, 'ratio']:.3f} at {earlier_date}")
            print(f"  Interval: [{earlier_date}, {later_date}) (left inclusive, right exclusive)")
            print(f"  Rows affected: {mask.sum()}")
            print()
        
        i += 1
    
    return result_df


# Example usage and test
def create_test_data():
    """Create sample test data to demonstrate the function"""
    
    # Create df1 with daily dates and weights
    dates1 = pd.date_range('2024-01-01', '2024-01-20', freq='D')
    df1 = pd.DataFrame({
        'date': dates1,
        'weight': np.random.uniform(10, 50, len(dates1))
    })
    
    # Create df2 with subset of dates and ratios
    # Design to show positive-to-negative patterns when processed in reverse
    dates2 = ['2024-01-03', '2024-01-07', '2024-01-12', '2024-01-16', '2024-01-18']
    ratios = [-0.5, 0.3, -0.2, 0.7, -0.1]  # Will process: 0.7→-0.2, then 0.3→-0.5
    
    df2 = pd.DataFrame({
        'date': pd.to_datetime(dates2),
        'ratio': ratios
    })
    
    return df1, df2


# Test the function
if __name__ == "__main__":
    # Create test data
    df1, df2 = create_test_data()
    
    print("Original df1 (first 10 rows):")
    print(df1.head(10))
    print(f"\ndf1 shape: {df1.shape}")
    
    print("\ndf2 (all rows):")
    print(df2)
    print(f"df2 shape: {df2.shape}")
    
    print("\n" + "="*60)
    print("PROCESSING RATIO PATTERNS (REVERSE TIME ORDER)")
    print("Only positive-to-negative patterns will be processed")
    print("="*60)
    
    # Apply the rescaling function
    result = rescale_weights_by_ratio_pattern(df1, df2)
    
    print("\nFinal result (showing changes):")
    # Show only rows where rescaling occurred
    changed_mask = result['weight'] != result['rescaled_weight']
    if changed_mask.any():
        comparison = result[changed_mask][['date', 'weight', 'rescaled_weight']].copy()
        comparison['change_factor'] = comparison['rescaled_weight'] / comparison['weight']
        print(comparison)
    else:
        print("No weights were rescaled.")
    
    print(f"\nTotal rows rescaled: {changed_mask.sum()} out of {len(result)}")
