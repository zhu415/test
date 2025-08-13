def create_filtered_dataframes(df, time_periods):
    """
    Create filtered dataframes for each time period with extended date ranges.
    
    For each interval [start_date, end_date), create a filtered dataframe where:
    - Left boundary: start_date - 2 days (inclusive)
    - Right boundary: end_date + 2 days (inclusive)
    
    Args:
        df (DataFrame): Source dataframe to filter (must have 'date' column)
        time_periods (list): List of interval strings in format '[YYYY-MM-DD, YYYY-MM-DD)'
    
    Returns:
        list: List of filtered dataframes, one for each time period
    """
    filtered_dfs = []
    
    for i, period in enumerate(time_periods):
        # Parse the interval string
        # Remove brackets and split by comma
        period_clean = period.strip('[]()') 
        start_str, end_str = period_clean.split(', ')
        
        # Convert to datetime
        start_date = pd.to_datetime(start_str)
        end_date = pd.to_datetime(end_str)
        
        # Extend the range: subtract 2 days from start, add 2 days to end
        extended_start = start_date - pd.Timedelta(days=2)
        extended_end = end_date + pd.Timedelta(days=2)
        
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
        print(f"  Extended interval: [{extended_start.strftime('%Y-%m-%d')}, {extended_end.strftime('%Y-%m-%d')}]")
        print(f"  Filtered dataframe shape: {filtered_df.shape}")
        print()
    
    return filtered_dfs
