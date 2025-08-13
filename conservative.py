def plot_filtered_dataframes(filtered_dfs, plot_function, fig_name_format="rescaling_period_{i}_{period_clean}"):
    """
    Create plots for each filtered dataframe using a custom plotting function.
    
    Args:
        filtered_dfs (list): List of filtered dataframes from create_filtered_dataframes
        plot_function: The plotting function to use (e.g., plot_bars_and_lines_mpl)
        fig_name_format (str): Format string for figure names. Available variables:
            - {i}: period index (1-based)
            - {period_clean}: cleaned period string (e.g., "2024-01-14_to_2024-01-18")
            - {start_date}: start date (YYYY-MM-DD format)
            - {end_date}: end date (YYYY-MM-DD format)
            - {extended_start}: extended start date
            - {extended_end}: extended end date
    
    Returns:
        list: List of figure names that were created
    """
    figure_names = []
    
    print("=" * 60)
    print("CREATING PLOTS FOR FILTERED DATAFRAMES")
    print("=" * 60)
    
    for i, df in enumerate(filtered_dfs):
        if len(df) == 0:
            print(f"Skipping plot {i+1}: Empty dataframe")
            continue
            
        # Extract period information for customized figure name
        original_period = df.attrs.get('original_period', f'period_{i+1}')
        extended_period = df.attrs.get('extended_period', f'extended_{i+1}')
        
        # Parse the original period to get start and end dates
        period_clean_base = original_period.replace('[', '').replace(')', '').replace(', ', '_to_')
        
        # Extract individual date components
        try:
            period_dates = original_period.strip('[]()').split(', ')
            start_date = period_dates[0]
            end_date = period_dates[1]
        except:
            start_date = "unknown_start"
            end_date = "unknown_end"
        
        # Extract extended dates
        try:
            extended_dates = extended_period.strip('[]').split(', ')
            extended_start = extended_dates[0]
            extended_end = extended_dates[1]
        except:
            extended_start = "unknown_ext_start"
            extended_end = "unknown_ext_end"
        
        # Create customized figure name using the format string
        fig_name = fig_name_format.format(
            i=i+1,
            period_clean=period_clean_base,
            start_date=start_date,
            end_date=end_date,
            extended_start=extended_start,
            extended_end=extended_end
        )
        
        print(f"Creating plot {i+1}:")
        print(f"  Original period: {original_period}")
        print(f"  Extended period: {extended_period}")
        print(f"  Figure name: {fig_name}")
        print(f"  Dataframe shape: {df.shape}")
        
        try:
            # Call the plotting function with the filtered dataframe
            plot_function(df, save_fig=True, fig_name=fig_name)
            figure_names.append(fig_name)
            print(f"  ✓ Plot created successfully")
        except Exception as e:
            print(f"  ✗ Error creating plot: {str(e)}")
        
        print("-" * 40)
    
    print(f"\nTotal plots created: {len(figure_names)}")
    return figure_names
