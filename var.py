import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

def calculate_volatilities(df):
    """
    Calculate 90-day volatility using three different methods.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with 'date' and 'price_per_share' columns
    
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
    
    # Method 1: Recursive calculation with P_t and Q_t (Exact 90-day)
    window_90 = 90
    if n >= window_90:
        # First window (indices 0 to 89)
        P = np.sum(returns[0:window_90])
        Q = np.sum(returns[0:window_90]**2)
        
        # Calculate variance and volatility for first window
        variance = (Q - P**2/window_90) / (window_90 - 1)
        if variance > 0:
            vol_method1[window_90-1] = np.sqrt(variance) * annualization_factor
        
        # Recursive updates for subsequent windows
        for t in range(window_90, n):
            # Update P and Q recursively
            P = P - returns[t-window_90] + returns[t]
            Q = Q - returns[t-window_90]**2 + returns[t]**2
            
            # Calculate variance and volatility
            variance = (Q - P**2/window_90) / (window_90 - 1)
            if variance > 0:
                vol_method1[t] = np.sqrt(variance) * annualization_factor
    
    # Method 2: Approximation with 91-day data
    # Sum of (r_i - avg_90)^2 for i=1,...,90 plus r_0^2
    window_91 = 91
    if n >= window_91:
        for t in range(window_91-1, n):
            # Get 91 days of returns (indices t-90 to t)
            returns_91 = returns[t-90:t+1]
            
            # Calculate 90-day average (excluding r_0)
            avg_90 = np.mean(returns_91[1:])
            
            # Calculate sum of squares
            sum_sq = np.sum((returns_91[1:] - avg_90)**2) + returns_91[0]**2
            
            # Calculate variance and volatility
            variance = sum_sq / (window_90 - 1)
            if variance > 0:
                vol_method2[t] = np.sqrt(variance) * annualization_factor
    
    # Method 3: New approximation using 89-day volatility
    # σ_90,t ≈ σ_89,t * (1 + 0.5 * (VarRatio - 1) / 89)
    # where VarRatio = 252 * (r_{t-89} - μ_89,t)^2 / σ_89,t^2
    window_89 = 89
    
    if n >= window_90:  # Need at least 90 days for this calculation
        for t in range(window_90-1, n):
            # Get the most recent 89 days (excluding the oldest return r_{t-89})
            returns_89 = returns[t-88:t+1]  # indices from t-88 to t (89 values)
            
            # Calculate 89-day mean and variance
            mu_89 = np.mean(returns_89)
            variance_89 = np.sum((returns_89 - mu_89)**2) / (window_89 - 1)
            
            if variance_89 > 0:
                # Calculate annualized 89-day variance and volatility
                variance_89_annualized = variance_89 * 252
                sigma_89_annualized = np.sqrt(variance_89_annualized)
                
                # Get the dropped return (r_{t-89})
                r_dropped = returns[t-89]
                
                # Calculate VarRatio
                var_ratio = 252 * (r_dropped - mu_89)**2 / variance_89_annualized
                
                # Apply the approximation formula
                sigma_90_approx = sigma_89_annualized * (1 + 0.5 * (var_ratio - 1) / 89)
                
                # Store the result
                vol_method3[t] = sigma_90_approx
    
    # Store results
    results['vol_method1_exact_90'] = vol_method1
    results['vol_method2_approx_91day'] = vol_method2
    results['vol_method3_approx_89day'] = vol_method3
    
    return results

def plot_volatilities(results):
    """
    Plot the three volatility methods for comparison.
    
    Parameters:
    -----------
    results : pd.DataFrame
        DataFrame with date and volatility calculations
    """
    
    # Create figure with subplots
    fig, axes = plt.subplots(3, 1, figsize=(12, 12))
    
    # Plot 1: All three methods together
    ax1 = axes[0]
    ax1.plot(results['date'], results['vol_method1_exact_90'], 
             label='Method 1: Exact 90-day (Recursive)', alpha=0.8, linewidth=1.5, color='blue')
    ax1.plot(results['date'], results['vol_method2_approx_91day'], 
             label='Method 2: Approximation (91-day data)', alpha=0.8, linewidth=1.5, color='orange')
    ax1.plot(results['date'], results['vol_method3_approx_89day'], 
             label='Method 3: Approximation (89-day based)', alpha=0.8, linewidth=1.5, color='green')
    
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Annualized Volatility')
    ax1.set_title('90-Day Rolling Volatility Comparison')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Differences between approximations and exact method
    ax2 = axes[1]
    
    # Calculate differences relative to Method 1 (exact)
    diff_2_1 = results['vol_method2_approx_91day'] - results['vol_method1_exact_90']
    diff_3_1 = results['vol_method3_approx_89day'] - results['vol_method1_exact_90']
    
    ax2.plot(results['date'], diff_2_1, 
             label='Method 2 vs Method 1 (91-day approx error)', alpha=0.8, linewidth=1.5, color='orange')
    ax2.plot(results['date'], diff_3_1, 
             label='Method 3 vs Method 1 (89-day approx error)', alpha=0.8, linewidth=1.5, color='green')
    
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Volatility Difference')
    ax2.set_title('Approximation Errors (Relative to Exact Method 1)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    # Plot 3: Percentage errors
    ax3 = axes[2]
    
    # Calculate percentage errors
    pct_error_2 = 100 * diff_2_1 / results['vol_method1_exact_90']
    pct_error_3 = 100 * diff_3_1 / results['vol_method1_exact_90']
    
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
    print("\n=== Volatility Statistics ===")
    print("\nMethod 1 (Exact 90-day Recursive):")
    print(f"  Mean: {results['vol_method1_exact_90'].mean():.4f}")
    print(f"  Std:  {results['vol_method1_exact_90'].std():.4f}")
    
    print("\nMethod 2 (Approximation with 91-day data):")
    print(f"  Mean: {results['vol_method2_approx_91day'].mean():.4f}")
    print(f"  Std:  {results['vol_method2_approx_91day'].std():.4f}")
    
    print("\nMethod 3 (Approximation using 89-day vol):")
    print(f"  Mean: {results['vol_method3_approx_89day'].mean():.4f}")
    print(f"  Std:  {results['vol_method3_approx_89day'].std():.4f}")
    
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
    
    print("Calculating volatilities using three methods...")
    results = calculate_volatilities(df)
    
    print("Plotting results...")
    fig = plot_volatilities(results)
    
    # Display sample of results including all methods
    print("\n=== Sample Results (rows 90-100) ===")
    display_cols = ['date', 'vol_method1_exact_90', 'vol_method2_approx_91day', 'vol_method3_approx_89day']
    print(results[display_cols].iloc[90:101].to_string())
    
    # Check correlation between methods
    print("\n=== Correlation Matrix ===")
    corr_matrix = results[['vol_method1_exact_90', 'vol_method2_approx_91day', 'vol_method3_approx_89day']].corr()
    print(corr_matrix)
