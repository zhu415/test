import pandas as pd
import re

def parse_txt_to_dataframe(file_path):
    """
    Parse a structured text file into a DataFrame.
    
    The file format:
    - Index names have no leading spaces
    - Underliers have 2 leading spaces, format: "underlier : weight"
    - Time periods have 2 leading spaces, format: "period : growth spread"
    - Empty lines separate index blocks
    """
    
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    data = []
    current_index = None
    underliers = {}
    time_periods = {}
    
    for line in lines:
        # Remove trailing newline
        line = line.rstrip('\n')
        
        # Skip empty lines - they signal end of current index block
        if not line.strip():
            if current_index and (underliers or time_periods):
                # Save the current index data
                for underlier, weight in underliers.items():
                    for period, growth_spread in time_periods.items():
                        data.append({
                            'Index': current_index,
                            'Underlier': underlier,
                            'Weight': weight,
                            'Period': period,
                            'Growth_Spread': growth_spread
                        })
                # Reset for next index
                underliers = {}
                time_periods = {}
            continue
        
        # Check indentation level
        if not line.startswith(' '):
            # This is an index name (no leading spaces)
            current_index = line.strip()
            underliers = {}
            time_periods = {}
        elif line.startswith('  ') and not line.startswith('   '):
            # This has exactly 2 leading spaces
            content = line.strip()
            if ' : ' in content:
                key, value = content.split(' : ', 1)
                
                # Determine if it's an underlier or time period
                # Time periods typically contain 'm', 'y', or start with a digit
                if re.match(r'^\d+[my]', key.lower()) or key.lower() in ['6m', '1y', '2y', '3y', '5y', '10y']:
                    time_periods[key] = value
                else:
                    underliers[key] = value
    
    # Don't forget the last index block if file doesn't end with empty line
    if current_index and (underliers or time_periods):
        for underlier, weight in underliers.items():
            for period, growth_spread in time_periods.items():
                data.append({
                    'Index': current_index,
                    'Underlier': underlier,
                    'Weight': weight,
                    'Period': period,
                    'Growth_Spread': growth_spread
                })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    return df

# Alternative approach: If you want a different structure (one row per index)
def parse_txt_to_wide_dataframe(file_path):
    """
    Parse text file into a wide format DataFrame where each index is one row.
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    data = []
    current_index = None
    current_data = {}
    
    for line in lines:
        line = line.rstrip('\n')
        
        if not line.strip():
            if current_index and current_data:
                current_data['Index'] = current_index
                data.append(current_data)
                current_data = {}
            continue
        
        if not line.startswith(' '):
            current_index = line.strip()
            current_data = {}
        elif line.startswith('  ') and not line.startswith('   '):
            content = line.strip()
            if ' : ' in content:
                key, value = content.split(' : ', 1)
                # Create column names based on the type of data
                if re.match(r'^\d+[my]', key.lower()):
                    column_name = f"Period_{key}"
                else:
                    column_name = f"Underlier_{key}"
                current_data[column_name] = value
    
    # Don't forget the last block
    if current_index and current_data:
        current_data['Index'] = current_index
        data.append(current_data)
    
    df = pd.DataFrame(data)
    # Reorder columns to have Index first
    if 'Index' in df.columns:
        cols = ['Index'] + [col for col in df.columns if col != 'Index']
        df = df[cols]
    
    return df
