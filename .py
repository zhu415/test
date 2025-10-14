import pandas as pd
import inspect

def compare_dataframe_columns(df1, df2, column_name):
    """
    Compare a specific column between two dataframes.
    Automatically extracts suffixes from dataframe variable names.
    
    Parameters:
    -----------
    df1 : pandas.DataFrame
        First dataframe
    df2 : pandas.DataFrame
        Second dataframe
    column_name : str
        Name of the column to compare
    
    Returns:
    --------
    pandas.DataFrame
        A dataframe with columns named using the extracted suffixes from df names
        
    Example:
    --------
    If you have dataframes named 'data_baseline_v1' and 'data_updated_v2',
    the returned columns will be 'baseline_v1_{column_name}', 'updated_v2_{column_name}', 'difference'
    """
    # Get the variable names of the dataframes from the calling context
    frame = inspect.currentframe()
    caller_frame = frame.f_back
    caller_locals = caller_frame.f_locals
    
    df1_name = None
    df2_name = None
    
    # Find the variable names
    for var_name, var_val in caller_locals.items():
        if var_val is df1 and df1_name is None:
            df1_name = var_name
        if var_val is df2 and df2_name is None:
            df2_name = var_name
    
    # Extract suffix after first underscore
    if df1_name and '_' in df1_name:
        df1_suffix = df1_name.split('_', 1)[1]  # Split only on first underscore
    else:
        df1_suffix = df1_name or 'df1'
    
    if df2_name and '_' in df2_name:
        df2_suffix = df2_name.split('_', 1)[1]  # Split only on first underscore
    else:
        df2_suffix = df2_name or 'df2'
    
    # Check if column exists in both dataframes
    if column_name not in df1.columns:
        raise ValueError(f"Column '{column_name}' not found in dataframe 1")
    if column_name not in df2.columns:
        raise ValueError(f"Column '{column_name}' not found in dataframe 2")
    
    # Extract the columns
    col1 = df1[column_name].reset_index(drop=True)
    col2 = df2[column_name].reset_index(drop=True)
    
    # Handle different lengths by padding with NaN
    max_len = max(len(col1), len(col2))
    col1 = col1.reindex(range(max_len))
    col2 = col2.reindex(range(max_len))
    
    # Calculate difference (for numeric columns)
    try:
        diff = col2 - col1
    except TypeError:
        # If columns are not numeric, show if values are equal
        diff = col1 == col2
    
    # Create comparison dataframe with extracted suffix names
    comparison_df = pd.DataFrame({
        f'{df1_suffix}_{column_name}': col1,
        f'{df2_suffix}_{column_name}': col2,
        'difference': diff
    })
    
    return comparison_df


# Example usage
if __name__ == "__main__":
    # Create sample dataframes with multiple underscores in names
    data_baseline_v1 = pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie'],
        'score': [85, 90, 78],
        'age': [25, 30, 35]
    })
    
    data_updated_v2 = pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie'],
        'score': [88, 90, 82],
        'age': [26, 30, 35]
    })
    
    # Compare the 'score' column - will use 'baseline_v1' and 'updated_v2' as suffixes
    result = compare_dataframe_columns(data_baseline_v1, data_updated_v2, 'score')
    print("Comparing 'score' column:")
    print(result)
    print("\n")
    
    # Compare the 'age' column
    result = compare_dataframe_columns(data_baseline_v1, data_updated_v2, 'age')
    print("Comparing 'age' column:")
    print(result)
