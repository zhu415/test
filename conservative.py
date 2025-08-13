def plot_filtered_dataframes(filtered_dfs, plot_function):
    """
    Create plots for each filtered dataframe using a custom plotting function.
    
    Args:
        filtered_dfs (list): List of filtered dataframes from create_filtered_dataframes
        plot_function: The plotting function to use (e.g., plot_bars_and_lines_mpl)
    
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
        
        # Create a customized figure name based on the time period
        # Clean the period string to make it filename-safe
        period_clean = original_period.replace('[', '').replace(')', '').replace(', ', '_to_')
        fig_name = f"rescaling_period_{i+1}_{period_clean}"
        
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
