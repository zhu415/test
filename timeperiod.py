import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

def verify_date_columns(dataframes: Dict[str, pd.DataFrame]) -> bool:
    """
    Verify that all dataframes have the same date column values.
    
    Parameters:
    dataframes: Dictionary with dataframe names as keys and dataframes as values
    
    Returns:
    Boolean indicating if all date columns are identical
    """
    df_names = list(dataframes.keys())
    if len(df_names) < 2:
        return True
    
    # Get the first dataframe's dates as reference
    reference_dates = dataframes[df_names[0]]['date'].reset_index(drop=True)
    
    print("=" * 50)
    print("VERIFYING DATE COLUMNS")
    print("=" * 50)
    
    all_match = True
    for name in df_names[1:]:
        current_dates = dataframes[name]['date'].reset_index(drop=True)
        
        # Check if dates match
        if len(reference_dates) != len(current_dates):
            print(f"❌ {name}: Different number of dates ({len(current_dates)} vs {len(reference_dates)})")
            all_match = False
        elif not reference_dates.equals(current_dates):
            print(f"❌ {name}: Date values don't match")
            all_match = False
        else:
            print(f"✓ {name}: Dates match with {df_names[0]}")
    
    if all_match:
        print("\n✅ All dataframes have identical date columns!")
    else:
        print("\n⚠️ Date columns are not identical across all dataframes!")
    
    return all_match

def extract_time_periods(df: pd.DataFrame, column_name: str = 'closest_column') -> Dict[str, List[Tuple[str, str]]]:
    """
    Extract time periods for each unique value in the specified column.
    
    Parameters:
    df: DataFrame with 'date' and specified column
    column_name: Name of the column to analyze (default: 'closest_column')
    
    Returns:
    Dictionary with unique values as keys and list of time periods as values
    """
    periods = {}
    
    # Ensure date column is datetime
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # Get unique values (excluding NaN)
    unique_values = df[column_name].dropna().unique()
    
    for value in unique_values:
        value_periods = []
        
        # Find all occurrences of this value
        mask = df[column_name] == value
        indices = df[mask].index.tolist()
        
        if not indices:
            continue
        
        # Group consecutive indices
        start_idx = indices[0]
        prev_idx = indices[0]
        
        for idx in indices[1:]:
            if idx != prev_idx + 1:
                # End of consecutive sequence
                start_date = df.loc[start_idx, 'date'].strftime('%Y-%m-%d')
                end_date = df.loc[prev_idx, 'date'].strftime('%Y-%m-%d')
                value_periods.append((start_date, end_date))
                start_idx = idx
            prev_idx = idx
        
        # Add the last period
        start_date = df.loc[start_idx, 'date'].strftime('%Y-%m-%d')
        end_date = df.loc[prev_idx, 'date'].strftime('%Y-%m-%d')
        value_periods.append((start_date, end_date))
        
        periods[value] = value_periods
    
    return periods

def format_periods_output(periods: Dict[str, List[Tuple[str, str]]], df_name: str) -> None:
    """
    Format and print the time periods for a dataframe.
    
    Parameters:
    periods: Dictionary of time periods
    df_name: Name of the dataframe
    """
    print(f"\n📊 {df_name} Time Periods:")
    print("-" * 40)
    
    for value, time_periods in sorted(periods.items()):
        # Extract case letter if it matches pattern like 'equity_df_a'
        if '_df_' in value and value.split('_df_')[-1] in ['a', 'b', 'c', 'd']:
            case_letter = value.split('_df_')[-1]
            print(f"Case {case_letter}: ", end="")
        else:
            print(f"{value}: ", end="")
        
        if len(time_periods) == 1 and time_periods[0][0] == time_periods[0][1]:
            print(f"[{time_periods[0][0]}]")
        else:
            formatted_periods = [f"[{start} to {end}]" for start, end in time_periods]
            print(", ".join(formatted_periods))

def cross_check_periods(all_periods: Dict[str, Dict[str, List[Tuple[str, str]]]]) -> Dict[str, Dict[str, List[str]]]:
    """
    Cross-check time periods across all dataframes to find overlaps.
    
    Parameters:
    all_periods: Dictionary with df names as keys and their periods as values
    
    Returns:
    Dictionary showing which dataframes share the same periods for each case
    """
    # Extract common cases (a, b, c, d) and error
    common_cases = ['a', 'b', 'c', 'd', 'error']
    overlap_results = {}
    
    for case in common_cases:
        case_overlaps = {}
        
        # Collect all periods for this case from all dataframes
        df_periods = {}
        for df_name, periods in all_periods.items():
            for value, time_periods in periods.items():
                # Check if this value corresponds to the current case
                is_match = False
                if case == 'error' and value == 'error':
                    is_match = True
                elif case in ['a', 'b', 'c', 'd'] and '_df_' in value and value.endswith(f'_df_{case}'):
                    is_match = True
                
                if is_match:
                    df_periods[df_name] = time_periods
        
        # Find overlapping periods
        if len(df_periods) > 1:
            # Convert periods to date ranges for easier comparison
            for df1_name, df1_periods in df_periods.items():
                for df2_name, df2_periods in df_periods.items():
                    if df1_name >= df2_name:
                        continue
                    
                    overlaps = find_period_overlaps(df1_periods, df2_periods)
                    if overlaps:
                        key = f"{df1_name} & {df2_name}"
                        if case not in case_overlaps:
                            case_overlaps[case] = {}
                        case_overlaps[key] = overlaps
        
        if case_overlaps:
            overlap_results[case] = case_overlaps
    
    return overlap_results

def find_period_overlaps(periods1: List[Tuple[str, str]], periods2: List[Tuple[str, str]]) -> List[str]:
    """
    Find overlapping time periods between two lists of periods.
    
    Parameters:
    periods1, periods2: Lists of time periods
    
    Returns:
    List of overlapping period descriptions
    """
    overlaps = []
    
    for start1, end1 in periods1:
        for start2, end2 in periods2:
            # Convert to datetime for comparison
            s1, e1 = pd.to_datetime(start1), pd.to_datetime(end1)
            s2, e2 = pd.to_datetime(start2), pd.to_datetime(end2)
            
            # Check for overlap
            if s1 <= e2 and s2 <= e1:
                # Calculate the actual overlap
                overlap_start = max(s1, s2)
                overlap_end = min(e1, e2)
                
                if overlap_start == overlap_end:
                    overlaps.append(overlap_start.strftime('%Y-%m-%d'))
                else:
                    overlaps.append(f"{overlap_start.strftime('%Y-%m-%d')} to {overlap_end.strftime('%Y-%m-%d')}")
    
    return overlaps

def analyze_dataframes(dataframes: Dict[str, pd.DataFrame]) -> None:
    """
    Main function to analyze all dataframes.
    
    Parameters:
    dataframes: Dictionary with dataframe names as keys and dataframes as values
    """
    # Step 1: Verify date columns
    dates_match = verify_date_columns(dataframes)
    
    # Step 2: Extract time periods for each dataframe
    print("\n" + "=" * 50)
    print("TIME PERIODS BY DATAFRAME")
    print("=" * 50)
    
    all_periods = {}
    for df_name, df in dataframes.items():
        periods = extract_time_periods(df)
        all_periods[df_name] = periods
        format_periods_output(periods, df_name)
        
        # Show unique values
        unique_vals = df['closest_column'].dropna().unique()
        print(f"  Unique values: {sorted(unique_vals)}")
    
    # Step 3: Cross-check periods
    print("\n" + "=" * 50)
    print("CROSS-CHECK: OVERLAPPING PERIODS")
    print("=" * 50)
    
    overlaps = cross_check_periods(all_periods)
    
    if overlaps:
        for case, case_overlaps in sorted(overlaps.items()):
            print(f"\n📌 Case '{case}' overlaps:")
            for df_pair, overlap_periods in case_overlaps.items():
                print(f"  {df_pair}:")
                for period in overlap_periods:
                    print(f"    • {period}")
    else:
        print("\nNo overlapping periods found between dataframes.")
    
    # Additional analysis: Find exact matches (same value at same time)
    print("\n" + "=" * 50)
    print("EXACT MATCHES ACROSS DATAFRAMES")
    print("=" * 50)
    
    if len(dataframes) > 1:
        find_exact_matches(dataframes)

def find_exact_matches(dataframes: Dict[str, pd.DataFrame]) -> None:
    """
    Find dates where multiple dataframes have the same case value.
    
    Parameters:
    dataframes: Dictionary with dataframe names as keys and dataframes as values
    """
    df_names = list(dataframes.keys())
    
    # Merge all dataframes on date
    merged = dataframes[df_names[0]][['date', 'closest_column']].copy()
    merged = merged.rename(columns={'closest_column': f'{df_names[0]}_value'})
    
    for df_name in df_names[1:]:
        df_temp = dataframes[df_name][['date', 'closest_column']].copy()
        df_temp = df_temp.rename(columns={'closest_column': f'{df_name}_value'})
        merged = merged.merge(df_temp, on='date', how='outer')
    
    # Find rows where values match
    value_columns = [f'{name}_value' for name in df_names]
    
    for case in ['a', 'b', 'c', 'd', 'error']:
        matches = []
        
        for idx, row in merged.iterrows():
            matching_dfs = []
            
            for col in value_columns:
                val = row[col]
                if pd.notna(val):
                    if case == 'error' and val == 'error':
                        matching_dfs.append(col.replace('_value', ''))
                    elif case != 'error' and '_df_' in str(val) and str(val).endswith(f'_df_{case}'):
                        matching_dfs.append(col.replace('_value', ''))
            
            if len(matching_dfs) > 1:
                matches.append((row['date'], matching_dfs))
        
        if matches:
            print(f"\nCase '{case}' exact matches:")
            for date, dfs in matches[:5]:  # Show first 5 matches
                print(f"  {pd.to_datetime(date).strftime('%Y-%m-%d')}: {', '.join(dfs)}")
            if len(matches) > 5:
                print(f"  ... and {len(matches) - 5} more matches")

# Example usage:
if __name__ == "__main__":
    # Create sample dataframes for demonstration
    import pandas as pd
    from datetime import datetime, timedelta
    
    # Generate sample dates
    dates = pd.date_range(start='2024-01-01', end='2024-01-20', freq='D')
    
    # Create sample dataframes
    equity_result = pd.DataFrame({
        'date': dates,
        'closest_column': ['equity_df_a'] * 5 + ['equity_df_b'] * 3 + 
                          ['equity_df_c'] * 4 + ['error'] * 2 + 
                          ['equity_df_d'] * 4 + ['equity_df_a'] * 2
    })
    
    bond_result = pd.DataFrame({
        'date': dates,
        'closest_column': ['bond_df_a'] * 4 + ['bond_df_b'] * 5 + 
                          ['bond_df_c'] * 3 + ['error'] * 3 + 
                          ['bond_df_d'] * 3 + ['bond_df_a'] * 2
    })
    
    commodity_result = pd.DataFrame({
        'date': dates,
        'closest_column': ['commodity_df_a'] * 3 + ['commodity_df_b'] * 4 + 
                          ['zero_value'] * 2 + ['commodity_df_c'] * 5 + 
                          ['error'] * 2 + ['commodity_df_d'] * 4
    })
    
    # Analyze the dataframes
    dataframes = {
        'equity_result': equity_result,
        'bond_result': bond_result,
        'commodity_result': commodity_result
    }
    
    analyze_dataframes(dataframes)
