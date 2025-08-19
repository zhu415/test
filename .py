import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Tuple

def calculate_realized_volatility(
    df: pd.DataFrame,
    n: int = 1,  # Number of days for return calculation
    N_S: int = 20,  # Short-term window (e.g., 20 trading days)
    N_L: int = 60,  # Long-term window (e.g., 60 trading days)
    annualization_factor: int = 252  # Trading days per year
) -> pd.DataFrame:
    """
    Calculate Realized Volatility based on weighted portfolio returns.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with columns: 'date', 'symbol', 'weight', 'price_per_share'
    n : int
        Number of days for return calculation (default: 1 for daily returns)
    N_S : int
        Number of trading days for short-term volatility (default: 20)
    N_L : int
        Number of trading days for long-term volatility (default: 60)
    annualization_factor : int
        Number of trading days per year (default: 252)
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with dates and 'realized_vol' column
    """
    
    # Step 1: Filter out cash components and normalize weights
    df_filtered = df[df['symbol'] != 'USD.CASH'].copy()
    
    # Normalize weights by date (so they sum to 1 for non-cash components)
    df_filtered['normalized_weight'] = df_filtered.groupby('date')['weight'].transform(
        lambda x: x / x.sum()
    )
    
    # Step 2: Calculate weighted returns for each component
    df_filtered = df_filtered.sort_values(['symbol', 'date'])
    
    # Calculate individual log returns for each symbol
    df_filtered['log_return'] = df_filtered.groupby('symbol')['price_per_share'].transform(
        lambda x: np.log(x / x.shift(n))
    )
    
    # Step 3: Calculate portfolio-level weighted log returns
    # Multiply log returns by normalized weights
    df_filtered['weighted_log_return'] = df_filtered['log_return'] * df_filtered['normalized_weight']
    
    # Sum weighted returns by date to get portfolio returns
    portfolio_returns = df_filtered.groupby('date')['weighted_log_return'].sum().reset_index()
    portfolio_returns.columns = ['date', 'portfolio_log_return']
    portfolio_returns = portfolio_returns.sort_values('date').reset_index(drop=True)
    
    # Step 4: Calculate variances using rolling windows
    # For variance calculation, we use squared log returns
    portfolio_returns['squared_log_return'] = portfolio_returns['portfolio_log_return'] ** 2
    
    # Short-term variance (rolling mean of squared returns)
    portfolio_returns['variance_S'] = portfolio_returns['squared_log_return'].rolling(
        window=N_S, min_periods=N_S
    ).mean()
    
    # Long-term variance (rolling mean of squared returns)
    portfolio_returns['variance_L'] = portfolio_returns['squared_log_return'].rolling(
        window=N_L, min_periods=N_L
    ).mean()
    
    # Step 5: Calculate realized volatilities
    # Short-term realized volatility
    portfolio_returns['realized_volatility_S'] = np.sqrt(
        (annualization_factor / n) * portfolio_returns['variance_S']
    )
    
    # Long-term realized volatility
    portfolio_returns['realized_volatility_L'] = np.sqrt(
        (annualization_factor / n) * portfolio_returns['variance_L']
    )
    
    # Step 6: Calculate final realized volatility (max of short and long term)
    portfolio_returns['realized_vol'] = portfolio_returns[
        ['realized_volatility_S', 'realized_volatility_L']
    ].max(axis=1)
    
    # Return dataframe with date and realized_vol
    result_df = portfolio_returns[['date', 'realized_vol']].copy()
    
    return result_df


def calculate_realized_volatility_detailed(
    df: pd.DataFrame,
    n: int = 1,
    N_S: int = 20,
    N_L: int = 60,
    annualization_factor: int = 252
) -> pd.DataFrame:
    """
    Same calculation but returns more detailed information for analysis.
    """
    
    # Filter out cash and normalize weights
    df_filtered = df[df['symbol'] != 'USD.CASH'].copy()
    
    df_filtered['normalized_weight'] = df_filtered.groupby('date')['weight'].transform(
        lambda x: x / x.sum()
    )
    
    df_filtered = df_filtered.sort_values(['symbol', 'date'])
    
    df_filtered['log_return'] = df_filtered.groupby('symbol')['price_per_share'].transform(
        lambda x: np.log(x / x.shift(n))
    )
    
    df_filtered['weighted_log_return'] = df_filtered['log_return'] * df_filtered['normalized_weight']
    
    portfolio_returns = df_filtered.groupby('date')['weighted_log_return'].sum().reset_index()
    portfolio_returns.columns = ['date', 'portfolio_log_return']
    portfolio_returns = portfolio_returns.sort_values('date').reset_index(drop=True)
    
    portfolio_returns['squared_log_return'] = portfolio_returns['portfolio_log_return'] ** 2
    
    portfolio_returns['variance_S'] = portfolio_returns['squared_log_return'].rolling(
        window=N_S, min_periods=N_S
    ).mean()
    
    portfolio_returns['variance_L'] = portfolio_returns['squared_log_return'].rolling(
        window=N_L, min_periods=N_L
    ).mean()
    
    portfolio_returns['realized_volatility_S'] = np.sqrt(
        (annualization_factor / n) * portfolio_returns['variance_S']
    )
    
    portfolio_returns['realized_volatility_L'] = np.sqrt(
        (annualization_factor / n) * portfolio_returns['variance_L']
    )
    
    portfolio_returns['realized_vol'] = portfolio_returns[
        ['realized_volatility_S', 'realized_volatility_L']
    ].max(axis=1)
    
    # Return all columns for detailed analysis
    return portfolio_returns


def plot_volatility_analysis(detailed_df: pd.DataFrame) -> None:
    """
    Create visualizations for volatility analysis.
    
    Parameters:
    -----------
    detailed_df : pd.DataFrame
        DataFrame from calculate_realized_volatility_detailed()
    """
    
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))
    
    # Plot 1: Portfolio Log Returns
    axes[0].plot(detailed_df['date'], detailed_df['portfolio_log_return'], 
                 color='blue', alpha=0.6, linewidth=0.8)
    axes[0].axhline(y=0, color='red', linestyle='--', alpha=0.5)
    axes[0].set_title('Portfolio Log Returns Over Time', fontsize=12, fontweight='bold')
    axes[0].set_xlabel('Date')
    axes[0].set_ylabel('Log Return')
    axes[0].grid(True, alpha=0.3)
    
    # Plot 2: Variance Comparison
    axes[1].plot(detailed_df['date'], detailed_df['variance_S'], 
                 label=f'Short-term Variance', color='green', alpha=0.8)
    axes[1].plot(detailed_df['date'], detailed_df['variance_L'], 
                 label=f'Long-term Variance', color='orange', alpha=0.8)
    axes[1].set_title('Short-term vs Long-term Variance', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('Date')
    axes[1].set_ylabel('Variance')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    # Plot 3: Realized Volatility
    axes[2].plot(detailed_df['date'], detailed_df['realized_volatility_S'], 
                 label='Short-term Vol', color='green', alpha=0.7)
    axes[2].plot(detailed_df['date'], detailed_df['realized_volatility_L'], 
                 label='Long-term Vol', color='orange', alpha=0.7)
    axes[2].plot(detailed_df['date'], detailed_df['realized_vol'], 
                 label='Realized Vol (Max)', color='red', linewidth=2)
    axes[2].set_title('Realized Volatility (Annualized)', fontsize=12, fontweight='bold')
    axes[2].set_xlabel('Date')
    axes[2].set_ylabel('Annualized Volatility')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)
    
    # Add percentage formatting for volatility
    axes[2].yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.1%}'.format(y)))
    
    plt.tight_layout()
    plt.show()


def print_volatility_summary(result_df: pd.DataFrame) -> None:
    """
    Print summary statistics for the realized volatility.
    
    Parameters:
    -----------
    result_df : pd.DataFrame
        DataFrame with 'date' and 'realized_vol' columns
    """
    print("\n" + "="*60)
    print("REALIZED VOLATILITY SUMMARY")
    print("="*60)
    
    # Remove NaN values for statistics
    vol_clean = result_df['realized_vol'].dropna()
    
    if len(vol_clean) > 0:
        print(f"\nNumber of observations: {len(vol_clean)}")
        print(f"Date range: {result_df['date'].min()} to {result_df['date'].max()}")
        print(f"\nVolatility Statistics (Annualized):")
        print(f"  Mean:     {vol_clean.mean():.2%}")
        print(f"  Median:   {vol_clean.median():.2%}")
        print(f"  Std Dev:  {vol_clean.std():.2%}")
        print(f"  Min:      {vol_clean.min():.2%}")
        print(f"  Max:      {vol_clean.max():.2%}")
        print(f"  25%:      {vol_clean.quantile(0.25):.2%}")
        print(f"  75%:      {vol_clean.quantile(0.75):.2%}")
        
        # Recent volatility
        if len(vol_clean) >= 5:
            print(f"\nMost Recent 5 Days:")
            recent = result_df.dropna(subset=['realized_vol']).tail(5)
            for _, row in recent.iterrows():
                print(f"  {row['date']}: {row['realized_vol']:.2%}")
    else:
        print("\nNo valid volatility values calculated.")
        print("Check if you have enough data points for the specified windows.")
    
    print("="*60)


# ==========================================
# JUPYTER NOTEBOOK USAGE EXAMPLES
# ==========================================

# Cell 1: Load your data
# Assuming you have your dataframe 'df' with columns: date, symbol, weight, price_per_share
# df = pd.read_csv('your_data.csv')  # or however you load your data

# Cell 2: Calculate realized volatility (simple version - just gets realized_vol)
# result_df = calculate_realized_volatility(
#     df,
#     n=1,      # Daily returns
#     N_S=20,   # 20-day short-term window
#     N_L=60    # 60-day long-term window
# )

# Cell 3: View the results
# result_df.head(10)

# Cell 4: Calculate with detailed information
# detailed_df = calculate_realized_volatility_detailed(
#     df,
#     n=1,
#     N_S=20,
#     N_L=60
# )

# Cell 5: Print summary statistics
# print_volatility_summary(result_df)

# Cell 6: Create visualizations
# plot_volatility_analysis(detailed_df)

# Cell 7: Export results
# result_df.to_csv('realized_volatility_results.csv', index=False)


# ==========================================
# SAMPLE DATA GENERATION FOR TESTING
# ==========================================

def generate_sample_data(n_days: int = 250, n_stocks: int = 3) -> pd.DataFrame:
    """
    Generate sample data for testing the volatility calculation.
    
    Parameters:
    -----------
    n_days : int
        Number of trading days to simulate
    n_stocks : int
        Number of stocks in the portfolio
    
    Returns:
    --------
    pd.DataFrame
        Sample dataframe with required columns
    """
    np.random.seed(42)  # For reproducibility
    
    dates = pd.date_range('2024-01-01', periods=n_days, freq='B')  # Business days only
    
    # Generate stock symbols
    stock_symbols = [f'STOCK_{i+1}' for i in range(n_stocks)]
    symbols = stock_symbols + ['USD.CASH']
    
    data = []
    
    # Initialize prices for each symbol
    initial_prices = {symbol: np.random.uniform(50, 200) for symbol in stock_symbols}
    initial_prices['USD.CASH'] = 1.0
    
    # Generate time series data
    for i, date in enumerate(dates):
        # Generate weights that sum to 1
        if n_stocks > 0:
            stock_weights = np.random.dirichlet(np.ones(n_stocks) * 2)  # Dirichlet for random weights
            cash_weight = np.random.uniform(0.02, 0.1)  # 2-10% cash
            
            # Normalize so total = 1
            total_non_cash = sum(stock_weights)
            stock_weights = stock_weights * (1 - cash_weight)
        
        for j, symbol in enumerate(symbols):
            if symbol == 'USD.CASH':
                price = 1.0
                weight = cash_weight
            else:
                # Random walk for stock prices
                if i == 0:
                    price = initial_prices[symbol]
                else:
                    prev_price = [d['price_per_share'] for d in data 
                                if d['symbol'] == symbol and d['date'] == dates[i-1]][0]
                    # Add some volatility and trend
                    daily_return = np.random.normal(0.0005, 0.02)  # 0.05% daily drift, 2% daily vol
                    price = prev_price * np.exp(daily_return)
                
                weight = stock_weights[j]
            
            data.append({
                'date': date,
                'symbol': symbol,
                'weight': weight,
                'price_per_share': price
            })
    
    return pd.DataFrame(data)


# ==========================================
# QUICK START EXAMPLE FOR JUPYTER NOTEBOOK
# ==========================================

# To use in Jupyter Notebook, run these cells:

# Cell 1: Generate sample data (or load your own)
sample_df = generate_sample_data(n_days=250, n_stocks=5)
print(f"Sample data shape: {sample_df.shape}")
print(f"Date range: {sample_df['date'].min()} to {sample_df['date'].max()}")
print(f"Symbols: {sample_df['symbol'].unique()}")

# Cell 2: Calculate realized volatility
result = calculate_realized_volatility(
    sample_df,
    n=1,      # Daily returns
    N_S=20,   # 20-day short-term window
    N_L=60    # 60-day long-term window
)

# Cell 3: View results
print("\nFirst 10 rows with realized volatility:")
print(result.head(10))
print("\nLast 10 rows with realized volatility:")
print(result.tail(10))

# Cell 4: Get detailed results for analysis
detailed = calculate_realized_volatility_detailed(
    sample_df,
    n=1,
    N_S=20,
    N_L=60
)

# Cell 5: Print summary
print_volatility_summary(result)

# Cell 6: Create visualizations
plot_volatility_analysis(detailed)
