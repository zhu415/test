import pandas as pd
import re

def restructure_dataframe(df):
    """
    Restructure the dataframe according to the specified requirements.
    
    Parameters:
    df: pandas DataFrame with columns 'date', 'name', 'values'
    
    Returns:
    pandas DataFrame with parsed and structured data
    """
    
    def parse_space_separated_values(value_str):
        """Parse space-separated values from a string"""
        if pd.isna(value_str):
            return []
        # Split by whitespace and convert to float
        return [float(x) for x in str(value_str).split()]
    
    def parse_enlist_value(value_str):
        """Parse numeric value after 'enlist ' pattern"""
        if pd.isna(value_str):
            return None
        # Extract number after "enlist "
        match = re.search(r'enlist\s+([0-9.-]+)', str(value_str))
        if match:
            return float(match.group(1))
        return None
    
    # Initialize list to store results
    result_rows = []
    
    # Process each unique date
    for date in df['date'].unique():
        date_data = df[df['date'] == date]
        
        # Extract data for each category
        weights_row = date_data[date_data['name'] == 'IndexComposition|NotionalFractions']
        prices_row = date_data[date_data['name'] == 'IndexComposition|Prices']
        symbols_row = date_data[date_data['name'] == 'IndexComposition|Symbols']
        shares_row = date_data[date_data['name'] == 'IndexComposition|Weights']
        fee_price_row = date_data[date_data['name'] == 'IndexFeeReport|Price']
        
        # Parse the values
        weights = []
        prices = []
        symbols = []
        shares = []
        fee_price = None
        
        if not weights_row.empty:
            weights = parse_space_separated_values(weights_row['values'].iloc[0])
        
        if not prices_row.empty:
            prices = parse_space_separated_values(prices_row['values'].iloc[0])
        
        if not symbols_row.empty:
            # Symbols might be strings, so handle differently
            symbols_str = str(symbols_row['values'].iloc[0])
            symbols = symbols_str.split() if not pd.isna(symbols_row['values'].iloc[0]) else []
        
        if not shares_row.empty:
            shares = parse_space_separated_values(shares_row['values'].iloc[0])
        
        if not fee_price_row.empty:
            fee_price = parse_enlist_value(fee_price_row['values'].iloc[0])
        
        # Check if all arrays have the same length
        max_length = max(len(weights), len(prices), len(symbols), len(shares))
        
        if max_length == 0:
            continue  # Skip if no data found
        
        # Ensure all arrays have the same length (pad with None if needed)
        weights.extend([None] * (max_length - len(weights)))
        prices.extend([None] * (max_length - len(prices)))
        symbols.extend([None] * (max_length - len(symbols)))
        shares.extend([None] * (max_length - len(shares)))
        
        # Create rows for this date
        for i in range(max_length):
            result_rows.append({
                'date': date,
                'symbol': symbols[i] if i < len(symbols) else None,
                'weight': weights[i] if i < len(weights) else None,
                'price_per_share': prices[i] if i < len(prices) else None,
                'number_of_shares': shares[i] if i < len(shares) else None,
                'fee_price': fee_price  # Repeated for all rows of the same date
            })
    
    # Create the result dataframe
    result_df = pd.DataFrame(result_rows)
    
    return result_df

def validate_parsing(df, result_df):
    """
    Validate the parsing results by checking data consistency
    """
    print("Validation Report:")
    print("=" * 50)
    
    # Check number of unique dates
    original_dates = df['date'].nunique()
    result_dates = result_df['date'].nunique()
    print(f"Original unique dates: {original_dates}")
    print(f"Result unique dates: {result_dates}")
    
    # Check for each date if parsing was successful
    for date in df['date'].unique():
        date_original = df[df['date'] == date]
        date_result = result_df[result_df['date'] == date]
        
        print(f"\nDate: {date}")
        print(f"  Result rows: {len(date_result)}")
        
        # Check if we have the expected name types
        name_types = date_original['name'].unique()
        print(f"  Available data types: {list(name_types)}")
        
        # Show sample of parsed data
        if len(date_result) > 0:
            print(f"  Sample parsed row:")
            print(f"    Symbol: {date_result['symbol'].iloc[0]}")
            print(f"    Weight: {date_result['weight'].iloc[0]}")
            print(f"    Price: {date_result['price_per_share'].iloc[0]}")
            print(f"    Shares: {date_result['number_of_shares'].iloc[0]}")
            print(f"    Fee Price: {date_result['fee_price'].iloc[0]}")

# Example usage:
# Assuming your dataframe is called 'df'
# result_df = restructure_dataframe(df)
# validate_parsing(df, result_df)

# Display sample of the result
# print("\nSample of restructured data:")
# print(result_df.head(10))

# Save to CSV if needed
# result_df.to_csv('restructured_data.csv', index=False)
