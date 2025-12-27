def create_pivot_table(df, output_path=None):
    """
    Create a pivot table for easier comparison across DateToMatch types.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame from process_all_output_files
    output_path : str, optional
        Path to save the pivot table CSV
        
    Returns:
    --------
    pd.DataFrame
        Pivot table with Date as index, and columns for each Index-DateToMatch combination
    """
    
    # Create a combined column name
    df['Index_DTM'] = df['Index'] + '_' + df['DateToMatch_Type']
    
    # Create pivot table
    pivot = df.pivot_table(
        values='Value',
        index='Date',
        columns='Index_DTM',
        aggfunc='first'
    )
    
    if output_path:
        pivot.to_csv(output_path)
        print(f"Pivot table saved to: {output_path}")
    
    return pivot


# Example usage for pivot table:
if __name__ == "__main__":
    # After getting the main dataframe
    df = save_results_to_csv(
        output_dir="./output",
        original_input_path="your_input_file.xml",
        indices=["SPX500", "SPX500_Weekly"],
        csv_output_path="./valuation_results.csv",
        date_step=1
    )
    
    # Create pivot table
    pivot = create_pivot_table(df, output_path="./valuation_results_pivot.csv")
    print("\nPivot Table:")
    print(pivot.head())
```

**The output CSV will have the following structure:**
```
Index,DateToMatch_Type,Date,Value
SPX500,BuildDate,2025-11-28,100.5
SPX500,BuildDate,2025-11-29,101.2
SPX500,BuildDate,2025-11-30,102.1
...
SPX500,ExpiryDate,2025-11-28,100.3
SPX500,ExpiryDate,2025-11-29,101.0
...
SPX500,Empty,2025-11-28,100.7
...
SPX500_Weekly,BuildDate,2025-11-28,150.5
...
```

**The pivot table CSV will look like:**
```
Date,SPX500_BuildDate,SPX500_ExpiryDate,SPX500_Empty,SPX500_Weekly_BuildDate,...
2025-11-28,100.5,100.3,100.7,150.5,...
2025-11-29,101.2,101.0,101.5,151.2,...
...
