def create_filtered_dataframes(df, time_periods):
    """
    Create filtered dataframes for each time period with extended date ranges.
    
    For each interval [start_date, end_date), create a filtered dataframe where:
    - Left boundary: 2 trading dates before start_date (inclusive)
    - Right boundary: 2 trading dates after end_date (inclusive)
    
    Args:
        df (DataFrame): Source dataframe to filter (must have 'date' column)
        time_periods (list): List of interval strings in format '[YYYY-MM-DD, YYYY-MM-DD)'
    
    Returns:
        list: List of filtered dataframes, one for each time period
    """
    filtered_dfs = []
    
    # Sort dataframe by date to ensure proper order for finding trading dates
    df_sorted = df.sort_values('date').reset_index(drop=True)
    unique_dates = df_sorted['date'].unique()
    unique_dates = pd.to_datetime(unique_dates)
    unique_dates = sorted(unique_dates)
    
    for i, period in enumerate(time_periods):
        # Parse the interval string
        # Remove brackets and split by comma
        period_clean = period.strip('[]()') 
        start_str, end_str = period_clean.split(', ')
        
        # Convert to datetime
        start_date = pd.to_datetime(start_str)
        end_date = pd.to_datetime(end_str)
        
        # Find extended start: 2 trading dates before start_date
        try:
            start_idx = unique_dates.index(start_date)
            extended_start_idx = max(0, start_idx - 2)  # Ensure we don't go below 0
            extended_start = unique_dates[extended_start_idx]
        except ValueError:
            # If start_date not found in trading dates, use the closest available date
            extended_start = start_date
            print(f"  Warning: Start date {start_date} not found in trading dates")
        
        # Find extended end: 2 trading dates after end_date
        try:
            end_idx = unique_dates.index(end_date)
            extended_end_idx = min(len(unique_dates) - 1, end_idx + 2)  # Ensure we don't exceed array bounds
            extended_end = unique_dates[extended_end_idx]
        except ValueError:
            # If end_date not found, find the closest date and extend from there
            closest_end_idx = min(range(len(unique_dates)), 
                                 key=lambda x: abs((unique_dates[x] - end_date).days))
            extended_end_idx = min(len(unique_dates) - 1, closest_end_idx + 2)
            extended_end = unique_dates[extended_end_idx]
            print(f"  Warning: End date {end_date} not found in trading dates, using closest date")
        
        # Filter the dataframe for the extended period (both endpoints inclusive)
        mask = (df['date'] >= extended_start) & (df['date'] <= extended_end)
        filtered_df = df[mask].copy()
        
        # Add some metadata to the filtered dataframe
        filtered_df.attrs['original_period'] = period
        filtered_df.attrs['extended_period'] = f"[{extended_start.strftime('%Y-%m-%d')}, {extended_end.strftime('%Y-%m-%d')}]"
        filtered_df.attrs['period_index'] = i
        
        filtered_dfs.append(filtered_df)
        
        print(f"Period {i+1}: {period}")
        print(f"  Original interval: {period}")
        print(f"  Extended interval: [{extended_start.strftime('%Y-%m-%d')}, {extended_end.strftime('%Y-%m-%d')}] (based on trading dates)")
        print(f"  Trading dates used: {extended_start.strftime('%Y-%m-%d')} to {extended_end.strftime('%Y-%m-%d')}")
        print(f"  Filtered dataframe shape: {filtered_df.shape}")
        print()
    
    return filtered_dfs
