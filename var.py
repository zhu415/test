import pandas as pd
import numpy as np

def calculate_portfolio_value(df):
    """
    Calculate the total portfolio value for each date (excluding cash)
    """
    # Filter out cash components
    portfolio_df = df[df['symbol'] != 'USD.CASH'].copy()
    
    # Calculate portfolio value for each date
    portfolio_df['position_value'] = portfolio_df['price_per_share'] * portfolio_df['number_of_shares']
    
    # Group by date and sum the position values
    portfolio_values = portfolio_df.groupby('date')['position_value'].sum().reset_index()
    portfolio_values.columns = ['date', 'portfolio_value']
    
    return portfolio_values.sort_values('date')

def calculate_garch_style_variance(portfolio_values, initial_var=None, alpha=0.03, beta=0.97):
    """
    Calculate realized variance using the GARCH-style formula:
    var_(t+1) = 0.97 * var_(t) + 0.03 * log(risky_(t+1) / risky_(t))^2
    
    Parameters:
    portfolio_values: DataFrame with 'date' and 'portfolio_value' columns
    initial_var: Initial variance (if None, uses first squared log return)
    alpha: Weight on new information (default: 0.03)
    beta: Weight on previous variance (default: 0.97)
    """
    df = portfolio_values.copy().sort_values('date')
    
    # Calculate log returns
    df['log_return'] = np.log(df['portfolio_value'] / df['portfolio_value'].shift(1))
    df['squared_log_return'] = df['log_return'] ** 2
    
    # Initialize variance series
    df['variance'] = np.nan
    df['volatility'] = np.nan
    
    # Set initial variance
    if initial_var is None:
        # Use first squared log return as initial variance
        initial_var = df['squared_log_return'].iloc[1] if not pd.isna(df['squared_log_return'].iloc[1]) else 0.01
    
    df.loc[df.index[1], 'variance'] = initial_var
    
    # Calculate variance using the GARCH-style formula
    for i in range(2, len(df)):
        if not pd.isna(df['squared_log_return'].iloc[i]):
            prev_var = df['variance'].iloc[i-1]
            new_info = df['squared_log_return'].iloc[i]
            df.loc[df.index[i], 'variance'] = beta * prev_var + alpha * new_info
    
    # Calculate volatility (annualized)
    df['volatility'] = np.sqrt(df['variance'] * 252)  # Assuming 252 trading days per year
    
    return df

def calculate_realized_volatility_standard(portfolio_values, window=30):
    """
    Calculate realized volatility using standard rolling window approach
    
    Parameters:
    portfolio_values: DataFrame with 'date' and 'portfolio_value' columns
    window: Rolling window size in days (default: 30)
    """
    df = portfolio_values.copy().sort_values('date')
    
    # Calculate log returns
    df['log_return'] = np.log(df['portfolio_value'] / df['portfolio_value'].shift(1))
    
    # Calculate rolling realized volatility
    df['realized_variance'] = df['log_return'].rolling(window=window).var()
    df['realized_volatility'] = np.sqrt(df['realized_variance'] * 252)  # Annualized
    
    # Alternative: using standard deviation directly
    df['realized_vol_std'] = df['log_return'].rolling(window=window).std() * np.sqrt(252)
    
    return df

# Main calculation workflow
def calculate_portfolio_volatility(result_df, method='both', window=30, alpha=0.03, beta=0.97):
    """
    Complete workflow to calculate portfolio volatility
    
    Parameters:
    result_df: Your restructured dataframe
    method: 'garch', 'standard', or 'both'
    window: Rolling window for standard method
    alpha, beta: Parameters for GARCH-style method
    """
    
    print("Calculating Portfolio Volatility")
    print("=" * 50)
    
    # Step 1: Calculate portfolio values
    portfolio_values = calculate_portfolio_value(result_df)
    print(f"Portfolio calculated for {len(portfolio_values)} dates")
    print(f"Date range: {portfolio_values['date'].min()} to {portfolio_values['date'].max()}")
    
    results = {}
    
    if method in ['garch', 'both']:
        # Step 2: Calculate GARCH-style variance
        print(f"\nCalculating GARCH-style variance (α={alpha}, β={beta})...")
        garch_results = calculate_garch_style_variance(portfolio_values, alpha=alpha, beta=beta)
        results['garch'] = garch_results
        
        # Show summary
        valid_vol = garch_results['volatility'].dropna()
        if len(valid_vol) > 0:
            print(f"GARCH Volatility - Mean: {valid_vol.mean():.4f}, Std: {valid_vol.std():.4f}")
            print(f"GARCH Volatility - Min: {valid_vol.min():.4f}, Max: {valid_vol.max():.4f}")
    
    if method in ['standard', 'both']:
        # Step 3: Calculate standard realized volatility
        print(f"\nCalculating standard realized volatility (window={window})...")
        standard_results = calculate_realized_volatility_standard(portfolio_values, window=window)
        results['standard'] = standard_results
        
        # Show summary
        valid_vol = standard_results['realized_volatility'].dropna()
        if len(valid_vol) > 0:
            print(f"Standard Volatility - Mean: {valid_vol.mean():.4f}, Std: {valid_vol.std():.4f}")
            print(f"Standard Volatility - Min: {valid_vol.min():.4f}, Max: {valid_vol.max():.4f}")
    
    return results, portfolio_values

# Usage examples:

# Method 1: Calculate using your specific GARCH-style formula
results, portfolio_vals = calculate_portfolio_volatility(result_df, method='garch')
garch_volatility = results['garch']

# Method 2: Calculate using standard rolling window
results, portfolio_vals = calculate_portfolio_volatility(result_df, method='standard', window=30)
standard_volatility = results['standard']

# Method 3: Calculate both methods
results, portfolio_vals = calculate_portfolio_volatility(result_df, method='both')

# Display results
print("\nSample of GARCH-style results:")
if 'garch' in results:
    display_cols = ['date', 'portfolio_value', 'log_return', 'variance', 'volatility']
    print(results['garch'][display_cols].tail(10))

print("\nSample of Standard realized volatility results:")
if 'standard' in results:
    display_cols = ['date', 'portfolio_value', 'log_return', 'realized_volatility']
    print(results['standard'][display_cols].tail(10))

# Optional: Save results
# results['garch'].to_csv('garch_volatility.csv', index=False)
# results['standard'].to_csv('standard_volatility.csv', index=False)
