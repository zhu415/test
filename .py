import pandas as pd

def compare_dataframe_columns(df1, df2, column_name, df1_name='df1', df2_name='df2'):
    """
    Compare a specific column between two dataframes.
    
    Parameters:
    -----------
    df1 : pandas.DataFrame
        First dataframe
    df2 : pandas.DataFrame
        Second dataframe
    column_name : str
        Name of the column to compare
    df1_name : str, optional
        Name/suffix for the first dataframe (default: 'df1')
    df2_name : str, optional
        Name/suffix for the second dataframe (default: 'df2')
    
    Returns:
    --------
    pandas.DataFrame
        A dataframe with columns named using the provided df names as suffixes
    """
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
    
    # Create comparison dataframe with custom column names
    comparison_df = pd.DataFrame({
        f'{df1_name}_{column_name}': col1,
        f'{df2_name}_{column_name}': col2,
        'difference': diff
    })
    
    return comparison_df


# Example usage
if __name__ == "__main__":
    # Create sample dataframes
    df1 = pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie'],
        'score': [85, 90, 78],
        'age': [25, 30, 35]
    })
    
    df2 = pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie'],
        'score': [88, 90, 82],
        'age': [26, 30, 35]
    })
    
    # Compare the 'score' column
    result = compare_dataframe_columns(df1, df2, 'score', 'baseline', 'updated')
    print("Comparing 'score' column:")
    print(result)
    print("\n")
    
    # Compare the 'age' column
    result = compare_dataframe_columns(df1, df2, 'age', 'baseline', 'updated')
    print("Comparing 'age' column:")
    print(result)
