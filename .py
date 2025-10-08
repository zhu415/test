#########################################
########## Extract Excel Infos ##########
#########################################

import pandas as pd
import os
from pathlib import Path
import numpy as np
from datetime import datetime, time, timedelta

# Check for required dependencies
try:
    import openpyxl
except ImportError:
    print("Warning: openpyxl not installed. Install with: pip install openpyxl")
    print("This is required for reading .xlsx and .xlsm files")

try:
    import xlrd
except ImportError:
    print("Info: xlrd not installed. Install with: pip install xlrd (for .xls files)")

try:
    import pyxlsb
except ImportError:
    print("Info: pyxlsb not installed. Install with: pip install pyxlsb (for .xlsb files)")

def extract_performance_data(file_path, sheet_name="Performance By CalcDuration"):
    """
    Extract Sum and Max values from Test Run 1 and Test Run 2 in the Performance By CalcDuration sheet.
    
    Parameters:
    file_path (Path): Path to the Excel file
    sheet_name (str): Name of the performance sheet
    
    Returns:
    dict: Dictionary with calc_time_prod, calc_time_qa, max_calc_time_prod, max_calc_time_qa
    """
    try:
        # Read the sheet without header to find the structure
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        # Find the row containing "Test Run 1" and "Test Run 2"
        test_run_row = None
        for idx, row in df.iterrows():
            row_str = ' '.join([str(cell) for cell in row if pd.notna(cell)])
            if "Test Run 1" in row_str and "Test Run 2" in row_str:
                test_run_row = idx
                break
        
        if test_run_row is None:
            print(f"  Could not find Test Run headers in {sheet_name}")
            return None
        
        # Find the header row with column names (#Position, Sum, Max, etc.)
        # It should be right after the Test Run row
        header_row = test_run_row + 1
        
        # Set up the dataframe with proper headers
        df.columns = df.iloc[header_row]
        df = df.iloc[header_row + 1:].reset_index(drop=True)
        
        # The structure should have columns for Test Run 1 and Test Run 2
        # We need to find Sum and Max columns for each test run
        
        # Look for the row with "PVRM" or similar identifier
        # For now, we'll take the first data row
        if len(df) > 0:
            first_data_row = df.iloc[0]
            
            # Find Sum and Max columns
            # The columns should be organized as: [Test Run 1 cols] [Test Run 2 cols]
            cols = list(df.columns)
            
            # Try to find Sum and Max for Test Run 1 (first occurrence)
            sum_cols = [i for i, col in enumerate(cols) if 'Sum' in str(col)]
            max_cols = [i for i, col in enumerate(cols) if 'Max' in str(col)]
            
            if len(sum_cols) >= 2 and len(max_cols) >= 2:
                # First Sum and Max are for Test Run 1, second are for Test Run 2
                calc_time_prod = first_data_row.iloc[sum_cols[0]]
                max_calc_time_prod = first_data_row.iloc[max_cols[0]]
                calc_time_qa = first_data_row.iloc[sum_cols[1]]
                max_calc_time_qa = first_data_row.iloc[max_cols[1]]
                
                return {
                    'calc_time_prod': calc_time_prod,
                    'calc_time_qa': calc_time_qa,
                    'max_calc_time_prod': max_calc_time_prod,
                    'max_calc_time_qa': max_calc_time_qa
                }
        
        print(f"  Could not extract performance data from {sheet_name}")
        return None
        
    except Exception as e:
        print(f"  Error extracting performance data: {str(e)}")
        return None

def extract_excel_data(directory_path, sheet_name, field_names, value_columns, field_column_name="Field"):
    """
    Extract data from Excel files in a directory based on field names and specified columns.
    Now also extracts performance data from "Performance By CalcDuration" sheet.
    
    Parameters:
    directory_path (str): Path to the directory containing Excel files
    sheet_name (str): Name of the sheet to search in (e.g., "Analysis by PVRM")
    field_names (list): List of field names to search for in the field column
    value_columns (dict): Dictionary mapping column labels to actual column names
                         e.g., {'gnu1': 'GNU 1 ($)', 'gnu2': 'GNU 2 ($)', 'gnu_diff': 'GNU diff ($)'}
    field_column_name (str): Name of the column containing field names (default: "Field")
    
    Returns:
    pandas.DataFrame: DataFrame with extracted data including performance metrics
    """
    
    # Initialize list to store results
    results = []
    
    # Get all Excel files in the directory
    directory = Path(directory_path)
    excel_files = list(directory.glob("*.xlsx")) + list(directory.glob("*.xlsm")) + list(directory.glob("*.csv"))
    
    # Filter out Excel temporary files (starting with ~$)
    excel_files = [f for f in excel_files if not f.name.startswith('~$')]
    
    if not excel_files:
        print(f"No Excel files found in {directory_path}")
        return pd.DataFrame()
    
    for file_path in excel_files:
        try:
            print(f"Processing file: {file_path.name}")
            
            # Get filename without extension
            filename = file_path.stem
            
            # Extract performance data from "Performance By CalcDuration" sheet
            perf_data = None
            if file_path.suffix.lower() != '.csv':
                perf_data = extract_performance_data(file_path)
            
            # Read the Excel file - read all data to handle hierarchical structure
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            else:
                # Read without header to get the raw structure
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            
            print(f"  Sheet shape: {df.shape}")
            
            # Find the header row that contains "Field" 
            field_header_row = None
            field_col_index = None
            
            for idx, row in df.iterrows():
                for col_idx, cell_value in enumerate(row):
                    if str(cell_value).strip() == "Field":
                        field_header_row = idx
                        field_col_index = col_idx
                        break
                if field_header_row is not None:
                    break
            
            if field_header_row is None:
                print(f"  Could not find 'Field' header in {filename}")
                continue
                
            print(f"  Found 'Field' header at row {field_header_row}, column {field_col_index}")
            
            # Set the header row and get column names
            df.columns = df.iloc[field_header_row]
            df = df.iloc[field_header_row + 1:].reset_index(drop=True)
            
            # Clean column names
            df.columns = [str(col).strip() if pd.notna(col) else f"Unnamed_{i}" for i, col in enumerate(df.columns)]
            
            print(f"  Available columns after processing: {list(df.columns)}")
            
            # Check if required columns exist
            required_cols = list(value_columns.values())
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                print(f"Warning: Missing columns in {filename}: {missing_cols}")
                print(f"Available columns: {list(df.columns)}")
                continue
            
            # Search for each field name - look for exact matches 
            for field_name in field_names:
                # Find rows where the Field column exactly matches the field name
                field_col = df.columns[field_col_index] if field_col_index < len(df.columns) else "Field"
                matching_rows = df[df[field_col].astype(str).str.strip() == field_name]
                
                if not matching_rows.empty:
                    for _, row in matching_rows.iterrows():
                        # Check if the row has actual values (not NaN/empty)
                        has_values = True
                        row_values = {}
                        
                        for col_key, col_name in value_columns.items():
                            if col_name in df.columns:
                                value = row[col_name]
                                if pd.isna(value) or str(value).strip() == '':
                                    has_values = False
                                    break
                                row_values[col_key] = value
                            else:
                                print(f"  Warning: Column '{col_name}' not found")
                                has_values = False
                                break
                        
                        if has_values:
                            result = {
                                'filename': filename,
                                'field_name': field_name,  # Use the input field_name, not the one from file
                            }
                            
                            # Add values for each specified column (keep raw values)
                            for col_key, value in row_values.items():
                                result[f'{col_key}_value'] = value
                            
                            # Add performance data if available (keep raw values)
                            if perf_data:
                                result.update(perf_data)
                            
                            results.append(result)
                            
                            # Print extracted values
                            value_str = ", ".join([f"{col_key}={value}" for col_key, value in row_values.items()])
                            print(f"  Found {field_name}: {value_str}")
                        else:
                            print(f"  Found {field_name} but no valid values in data columns")
                else:
                    print(f"  Field '{field_name}' not found in {filename}")
                    # Debug: show what field names are actually available
                    if field_col_index < len(df.columns):
                        available_fields = df[df.columns[field_col_index]].dropna().astype(str).str.strip()
                        available_fields = available_fields[available_fields != ''].unique()[:10]  # Show first 10
                        print(f"  Available field names (sample): {list(available_fields)}")
        
        except Exception as e:
            print(f"Error processing {file_path.name}: {str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    # Create DataFrame from results
    if results:
        result_df = pd.DataFrame(results)
        return result_df
    else:
        print("No data extracted from any files")
        return pd.DataFrame()

def parse_time_value(time_value):
    """
    Parse various time formats and return total seconds.
    Handles: datetime.time, timedelta, string formats like "3:55:24" or "0 days 03:55:24"
    """
    if pd.isna(time_value):
        return None
    
    try:
        # If it's already a timedelta
        if isinstance(time_value, timedelta):
            return int(time_value.total_seconds())
        
        # If it's a datetime.time object
        if isinstance(time_value, time):
            return time_value.hour * 3600 + time_value.minute * 60 + time_value.second
        
        # If it's a string
        if isinstance(time_value, str):
            time_str = str(time_value).strip()
            
            # Handle "0 days HH:MM:SS" format
            if 'days' in time_str or 'day' in time_str:
                # Remove the days part, we only want HH:MM:SS
                time_str = time_str.split()[-1]
            
            # Parse HH:MM:SS format
            parts = time_str.split(':')
            if len(parts) == 3:
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
        
        # If it's a number, assume it's already in seconds
        return int(float(time_value))
    
    except Exception as e:
        print(f"Warning: Could not parse time value '{time_value}': {e}")
        return None

def format_time_hm(time_value):
    """
    Format time to hour and minutes notation.
    Input can be: datetime.time, timedelta, string like "3:55:24" or "0 days 03:55:24"
    Examples: 3:55:24 -> 3h55m, 0:45:30 -> 45m
    """
    total_seconds = parse_time_value(time_value)
    
    if total_seconds is None:
        return str(time_value) if not pd.isna(time_value) else ''
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}h{minutes}m"
    else:
        return f"{minutes}m"

def format_number_k(value):
    """
    Format number to k/M notation with sign.
    Examples: 35531.56 -> +35k, -74206.05 -> -74k, 1500000 -> +1.5M
    """
    if pd.isna(value):
        return ''
    
    # Convert to float if it's a string with commas
    if isinstance(value, str):
        value = float(value.replace(',', ''))
    
    sign = '+' if value >= 0 else ''
    abs_value = abs(value)
    
    if abs_value >= 1_000_000:
        formatted = f"{sign}{value/1_000_000:.0f}M"
    elif abs_value >= 1_000:
        formatted = f"{sign}{value/1_000:.0f}k"
    else:
        formatted = f"{sign}{value:.0f}"
    
    return formatted

def clean_numeric_value(value):
    """
    Clean a single numeric value by removing commas and converting to float.
    """
    if pd.isna(value):
        return value
    
    if isinstance(value, str):
        return float(value.replace(',', ''))
    
    return float(value)

def create_final_dataframe(extracted_data, field_names):
    """
    Create the final dataframe with all required columns.
    
    Returns:
    tuple: (raw_dataframe, formatted_dataframe)
    """
    # Create summary dataframe grouped by filename and field_name
    final_data = []
    
    # Group by filename to process each file
    for filename in extracted_data['filename'].unique():
        file_data = extracted_data[extracted_data['filename'] == filename]
        
        for field_name in field_names:
            field_data = file_data[file_data['field_name'] == field_name]
            
            if not field_data.empty:
                # Take the first row
                row = field_data.iloc[0]
                
                # Get raw values without any cleaning
                gnu1_raw = row.get('gnu1_value', '')
                gnu2_raw = row.get('gnu2_value', '')
                gnu_diff_raw = row.get('gnu_diff_value', '')
                
                # Clean for calculation
                gnu1 = clean_numeric_value(gnu1_raw)
                gnu2 = clean_numeric_value(gnu2_raw)
                gnu_diff = clean_numeric_value(gnu_diff_raw)
                
                # Calculate diff / GNU 1
                diff_div_gnu1 = (gnu_diff / gnu1) if (not pd.isna(gnu1) and gnu1 != 0) else ''
                
                final_row = {
                    'Index': filename,
                    'Field': field_name,
                    'GNU 1 ($)': gnu1_raw,
                    'GNU 2 ($)': gnu2_raw,
                    'GNU diff ($)': gnu_diff_raw,
                    'diff / GNU 1': diff_div_gnu1,
                    'Calc time prod': row.get('calc_time_prod', ''),
                    'Calc time qa': row.get('calc_time_qa', ''),
                    'Max calc time prod': row.get('max_calc_time_prod', ''),
                    'Max calc time qa': row.get('max_calc_time_qa', '')
                }
                
                final_data.append(final_row)
    
    raw_df = pd.DataFrame(final_data)
    
    # Create formatted version
    formatted_df = raw_df.copy()
    
    # Format monetary columns
    for col in ['GNU 1 ($)', 'GNU 2 ($)', 'GNU diff ($)']:
        if col in formatted_df.columns:
            formatted_df[col] = formatted_df[col].apply(lambda x: format_number_k(clean_numeric_value(x)))
    
    # Replace diff / GNU 1 with Relative diff (%) in formatted version
    if 'diff / GNU 1' in formatted_df.columns:
        formatted_df['Relative diff (%)'] = formatted_df['diff / GNU 1'].apply(
            lambda x: f"{x*100:.2f}%" if (not pd.isna(x) and x != '') else ''
        )
        formatted_df = formatted_df.drop(columns=['diff / GNU 1'])
    
    # Format time columns
    for col in ['Calc time prod', 'Calc time qa', 'Max calc time prod', 'Max calc time qa']:
        if col in formatted_df.columns:
            formatted_df[col] = formatted_df[col].apply(format_time_hm)
    
    return raw_df, formatted_df

# Example usage
if __name__ == "__main__":
    # Configuration parameters
    DIRECTORY_PATH = "/path/to/your/excel/files"  # Update this path
    SHEET_NAME = "Analysis by PVRM"  # Main analysis sheet
    
    # Field names to extract
    FIELD_NAMES = [
        "PosCcyDelta", 
        "PosCcyDelta_TPlusN", 
        "PosKappa", 
        "PosKappaSkewPlus", 
        "PosTV", 
        "PosRho", 
        "P&L"
    ]
    
    # Column mapping for the Analysis by PVRM sheet
    VALUE_COLUMNS = {
        'gnu1': 'GNU 1 ($)',
        'gnu2': 'GNU 2 ($)',
        'gnu_diff': 'GNU diff ($)'
    }
    
    # Extract data from both sheets
    extracted_data = extract_excel_data(
        directory_path=DIRECTORY_PATH,
        sheet_name=SHEET_NAME,
        field_names=FIELD_NAMES,
        value_columns=VALUE_COLUMNS,
        field_column_name="Field"
    )
    
    if not extracted_data.empty:
        # Create final dataframes (raw and formatted)
        raw_df, formatted_df = create_final_dataframe(extracted_data, FIELD_NAMES)
        
        # Display results
        print("\n" + "="*80)
        print("RAW DATA:")
        print("="*80)
        print(raw_df.to_string(index=False))
        
        print("\n" + "="*80)
        print("FORMATTED DATA:")
        print("="*80)
        print(formatted_df.to_string(index=False))
        
        # Save to CSV files
        raw_output = "extracted_data_raw.csv"
        formatted_output = "extracted_data_formatted.csv"
        
        raw_df.to_csv(raw_output, index=False)
        formatted_df.to_csv(formatted_output, index=False)
        
        print(f"\nRaw data saved to {raw_output}")
        print(f"Formatted data saved to {formatted_output}")
        
        # Optional: Display summary statistics for raw data
        print("\n" + "="*80)
        print("SUMMARY STATISTICS (Raw Data):")
        print("="*80)
        numeric_cols = ['diff / GNU 1']
        for col in numeric_cols:
            if col in raw_df.columns:
                valid_values = raw_df[col][raw_df[col] != '']
                if len(valid_values) > 0:
                    print(f"\n{col}:")
                    print(f"  Mean: {valid_values.mean():.4f}")
                    print(f"  Std:  {valid_values.std():.4f}")
                    print(f"  Min:  {valid_values.min():.4f}")
                    print(f"  Max:  {valid_values.max():.4f}")
    else:
        print("No data was extracted.")

# Alternative function for more flexible column matching
def extract_excel_data_flexible(directory_path, sheet_name, field_names, column_patterns=None):
    """
    More flexible version that can handle variations in column names.
    
    Parameters:
    directory_path (str): Path to the directory containing Excel files
    sheet_name (str): Name of the sheet to search in
    field_names (list): List of field names to search for
    column_patterns (dict): Dictionary mapping standard names to possible column name patterns
                           e.g., {'gnu1': ['GNU 1', 'GNU1', 'GNU 1 ($)'], 'gnu2': ['GNU 2', 'GNU2', 'GNU 2 ($)']}
    """
    
    if column_patterns is None:
        column_patterns = {
            'gnu1': ['GNU 1 ($)', 'GNU 1', 'GNU1'],
            'gnu2': ['GNU 2 ($)', 'GNU 2', 'GNU2'],
            'gnu_diff': ['GNU diff ($)', 'GNU diff', 'GNU_diff', 'Diff']
        }
    
    results = []
    directory = Path(directory_path)
    excel_files = list(directory.glob("*.xlsx")) + list(directory.glob("*.xlsm")) + list(directory.glob("*.csv"))
    
    # Filter out Excel temporary files (starting with ~$)
    excel_files = [f for f in excel_files if not f.name.startswith('~$')]
    
    for file_path in excel_files:
        try:
            filename = file_path.stem
            
            # Extract performance data
            perf_data = None
            if file_path.suffix.lower() != '.csv':
                perf_data = extract_performance_data(file_path)
            
            # Read file
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Find matching columns
            col_mapping = {}
            for standard_name, patterns in column_patterns.items():
                for pattern in patterns:
                    matching_cols = [col for col in df.columns if pattern in col]
                    if matching_cols:
                        col_mapping[standard_name] = matching_cols[0]
                        break
            
            if 'gnu1' not in col_mapping or 'gnu2' not in col_mapping:
                print(f"Required columns not found in {filename}")
                continue
            
            # Search for field names
            for field_name in field_names:
                matching_rows = df[df['Field'].str.contains(field_name, case=False, na=False)]
                
                for _, row in matching_rows.iterrows():
                    result = {
                        'filename': filename,
                        'field_name': field_name,
                        'gnu1_value': row[col_mapping['gnu1']],
                        'gnu2_value': row[col_mapping['gnu2']],
                    }
                    
                    if 'gnu_diff' in col_mapping:
                        result['gnu_diff_value'] = row[col_mapping['gnu_diff']]
                    
                    # Add performance data if available
                    if perf_data:
                        result.update(perf_data)
                    
                    results.append(result)
        
        except Exception as e:
            print(f"Error processing {file_path.name}: {str(e)}")
    
    return pd.DataFrame(results) if results else pd.DataFrame()
