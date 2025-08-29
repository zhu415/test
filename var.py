import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

def calculate_volatilities(df, window=90):
    """
    Calculate N-day volatility using three different methods.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with 'date' and 'price_per_share' columns
    window : int
        Rolling window size (default: 90)
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with date and three volatility calculations
    """
    
    # Calculate returns (assuming daily returns)
    df = df.copy()
    df['return'] = df['price_per_share'].pct_change()
    
    # Remove NaN values
    df = df.dropna()
    
    # Initialize results DataFrame
    results = pd.DataFrame()
    results['date'] = df['date']
    
    # Initialize arrays for storing results
    n = len(df)
    vol_method1 = np.full(n, np.nan)
    vol_method2 = np.full(n, np.nan)
    vol_method3 = np.full(n, np.nan)
    
    # Pre-compute returns array for easier indexing
    returns = df['return'].values
    annualization_factor = np.sqrt(252)  # Assuming 252 trading days per year
    
    # Method 1: Recursive calculation with P_t and Q_t (Exact N-day)
    if n >= window:
        # First window
        P = np.sum(returns[0:window])
        Q = np.sum(returns[0:window]**2)
        
        # Calculate variance and volatility for first window
        variance = (Q - P**2/window) / (window - 1)
        if variance > 0:
            vol_method1[window-1] = np.sqrt(variance) * annualization_factor
        
        # Recursive updates for subsequent windows
        for t in range(window, n):
            # Update P and Q recursively
            P = P - returns[t-window] + returns[t]
            Q = Q - returns[t-window]**2 + returns[t]**2
            
            # Calculate variance and volatility
            variance = (Q - P**2/window) / (window - 1)
            if variance > 0:
                vol_method1[t] = np.sqrt(variance) * annualization_factor
    
    # Method 2: Approximation with (N+1)-day data
    # Sum of (r_i - avg_N)^2 for i=1,...,N plus r_0^2
    window_NPlus1 = window + 1
    if n >= window_NPlus1:
        for t in range(window_NPlus1-1, n):
            # Get (N+1) days of returns
            returns_NPlus1 = returns[t-window:t+1]
            
            # Calculate N-day average (excluding r_0)
            avg_N = np.mean(returns_NPlus1[1:])
            
            # Calculate sum of squares
            sum_sq = np.sum((returns_NPlus1[1:] - avg_N)**2) + returns_NPlus1[0]**2
            
            # Calculate variance and volatility
            variance = sum_sq / (window - 1)
            if variance > 0:
                vol_method2[t] = np.sqrt(variance) * annualization_factor
    
    # Method 3: New approximation using (N-1)-day volatility
    # σ_N,t ≈ σ_{N-1},t * (1 + 0.5 * (VarRatio - 1) / (N-1))
    # where VarRatio = 252 * (r_{t-(N-1)} - μ_{N-1},t)^2 / σ_{N-1},t^2
    window_NMinus1 = window - 1
    
    if n >= window:  # Need at least N days for this calculation
        for t in range(window-1, n):
            # Get the most recent (N-1) days (excluding the oldest return)
            returns_NMinus1 = returns[t-window_NMinus1+1:t+1]  # (N-1) values
            
            # Calculate (N-1)-day mean and variance
            mu_NMinus1 = np.mean(returns_NMinus1)
            variance_NMinus1 = np.sum((returns_NMinus1 - mu_NMinus1)**2) / (window_NMinus1 - 1)
            
            if variance_NMinus1 > 0:
                # Calculate annualized (N-1)-day variance and volatility
                variance_NMinus1_annualized = variance_NMinus1 * 252
                sigma_NMinus1_annualized = np.sqrt(variance_NMinus1_annualized)
                
                # Get the dropped return (r_{t-(N-1)})
                r_dropped = returns[t-window_NMinus1]
                
                # Calculate VarRatio
                var_ratio = 252 * (r_dropped - mu_NMinus1)**2 / variance_NMinus1_annualized
                
                # Apply the approximation formula
                sigma_N_approx = sigma_NMinus1_annualized * (1 + 0.5 * (var_ratio - 1) / window_NMinus1)
                
                # Store the result
                vol_method3[t] = sigma_N_approx
    
    # Store results with dynamic column names
    results[f'vol_method1_exact_{window}day'] = vol_method1
    results[f'vol_method2_approx_{window+1}day'] = vol_method2
    results[f'vol_method3_approx_{window-1}day'] = vol_method3
    
    return results

def plot_volatilities(results, window=90):
    """
    Plot the three volatility methods for comparison.
    
    Parameters:
    -----------
    results : pd.DataFrame
        DataFrame with date and volatility calculations
    window : int
        Rolling window size (default: 90)
    """
    
    # Get column names dynamically
    col_method1 = f'vol_method1_exact_{window}day'
    col_method2 = f'vol_method2_approx_{window+1}day'
    col_method3 = f'vol_method3_approx_{window-1}day'
    
    # Create figure with subplots
    fig, axes = plt.subplots(3, 1, figsize=(12, 12))
    
    # Plot 1: All three methods together
    ax1 = axes[0]
    ax1.plot(results['date'], results[col_method1], 
             label=f'Method 1: Exact {window}-day (Recursive)', alpha=0.8, linewidth=1.5, color='blue')
    ax1.plot(results['date'], results[col_method2], 
             label=f'Method 2: Approximation ({window+1}-day data)', alpha=0.8, linewidth=1.5, color='orange')
    ax1.plot(results['date'], results[col_method3], 
             label=f'Method 3: Approximation ({window-1}-day based)', alpha=0.8, linewidth=1.5, color='green')
    
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Annualized Volatility')
    ax1.set_title(f'{window}-Day Rolling Volatility Comparison')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Differences between approximations and exact method
    ax2 = axes[1]
    
    # Calculate differences relative to Method 1 (exact)
    diff_2_1 = results[col_method2] - results[col_method1]
    diff_3_1 = results[col_method3] - results[col_method1]
    
    ax2.plot(results['date'], diff_2_1, 
             label=f'Method 2 vs Method 1 ({window+1}-day approx error)', alpha=0.8, linewidth=1.5, color='orange')
    ax2.plot(results['date'], diff_3_1, 
             label=f'Method 3 vs Method 1 ({window-1}-day approx error)', alpha=0.8, linewidth=1.5, color='green')
    
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Volatility Difference')
    ax2.set_title('Approximation Errors (Relative to Exact Method 1)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    # Plot 3: Percentage errors
    ax3 = axes[2]
    
    # Calculate percentage errors
    pct_error_2 = 100 * diff_2_1 / results[col_method1]
    pct_error_3 = 100 * diff_3_1 / results[col_method1]
    
    ax3.plot(results['date'], pct_error_2, 
             label='Method 2 % error', alpha=0.8, linewidth=1.5, color='orange')
    ax3.plot(results['date'], pct_error_3, 
             label='Method 3 % error', alpha=0.8, linewidth=1.5, color='green')
    
    ax3.set_xlabel('Date')
    ax3.set_ylabel('Percentage Error (%)')
    ax3.set_title('Relative Approximation Errors')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.show()
    
    # Print statistics
    print(f"\n=== {window}-Day Volatility Statistics ===")
    print(f"\nMethod 1 (Exact {window}-day Recursive):")
    print(f"  Mean: {results[col_method1].mean():.4f}")
    print(f"  Std:  {results[col_method1].std():.4f}")
    
    print(f"\nMethod 2 (Approximation with {window+1}-day data):")
    print(f"  Mean: {results[col_method2].mean():.4f}")
    print(f"  Std:  {results[col_method2].std():.4f}")
    
    print(f"\nMethod 3 (Approximation using {window-1}-day vol):")
    print(f"  Mean: {results[col_method3].mean():.4f}")
    print(f"  Std:  {results[col_method3].std():.4f}")
    
    print("\n=== Approximation Error Statistics ===")
    print(f"Method 2 - Max absolute error: {np.nanmax(np.abs(diff_2_1)):.6f}")
    print(f"Method 2 - Mean absolute error: {np.nanmean(np.abs(diff_2_1)):.6f}")
    print(f"Method 2 - RMSE: {np.sqrt(np.nanmean(diff_2_1**2)):.6f}")
    
    print(f"\nMethod 3 - Max absolute error: {np.nanmax(np.abs(diff_3_1)):.6f}")
    print(f"Method 3 - Mean absolute error: {np.nanmean(np.abs(diff_3_1)):.6f}")
    print(f"Method 3 - RMSE: {np.sqrt(np.nanmean(diff_3_1**2)):.6f}")
    
    print("\n=== Percentage Error Statistics ===")
    print(f"Method 2 - Mean % error: {np.nanmean(pct_error_2):.4f}%")
    print(f"Method 2 - Std % error: {np.nanstd(pct_error_2):.4f}%")
    
    print(f"\nMethod 3 - Mean % error: {np.nanmean(pct_error_3):.4f}%")
    print(f"Method 3 - Std % error: {np.nanstd(pct_error_3):.4f}%")
    
    return fig

# Example usage with sample data
def create_sample_data(n_days=500):
    """
    Create sample data for demonstration.
    """
    np.random.seed(42)
    dates = pd.date_range(start='2022-01-01', periods=n_days, freq='D')
    
    # Simulate price with some volatility clustering
    returns = np.random.normal(0.0005, 0.02, n_days)
    
    # Add volatility clustering
    for i in range(100, 150):
        returns[i] *= 2  # Higher volatility period
    for i in range(300, 350):
        returns[i] *= 1.5  # Another high volatility period
    
    prices = 100 * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'date': dates,
        'price_per_share': prices
    })
    
    return df

# Main execution
if __name__ == "__main__":
    # Create sample data (replace with your actual dataframe)
    df = create_sample_data(500)
    
    # You can now specify different window sizes
    window_size = 90  # Change this to any value you want
    
    print(f"Calculating {window_size}-day volatilities using three methods...")
    results = calculate_volatilities(df, window=window_size)
    
    print("Plotting results...")
    fig = plot_volatilities(results, window=window_size)
    
    # Display sample of results including all methods
    print(f"\n=== Sample Results (rows {window_size}-{window_size+10}) ===")
    display_cols = ['date'] + [col for col in results.columns if 'vol_method' in col]
    print(results[display_cols].iloc[window_size:window_size+11].to_string())
    
    # Check correlation between methods
    print("\n=== Correlation Matrix ===")
    vol_cols = [col for col in results.columns if 'vol_method' in col]
    corr_matrix = results[vol_cols].corr()
    print(corr_matrix)
    
    # Example: Try different window sizes
    print("\n" + "="*60)
    print("Testing with different window sizes...")
    for test_window in [30, 60, 90, 120]:
        print(f"\n--- Window size: {test_window} days ---")
        test_results = calculate_volatilities(df, window=test_window)
        col1 = f'vol_method1_exact_{test_window}day'
        print(f"Mean volatility (exact): {test_results[col1].mean():.4f}")
