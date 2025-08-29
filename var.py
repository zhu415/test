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
    
    # Method 1: Exact 90-day volatility with recursive formula
    window = 90
    annualization_factor = np.sqrt(252)  # Assuming 252 trading days per year
    
    # Initialize arrays for storing results
    n = len(df)
    vol_method1 = np.full(n, np.nan)
    vol_method2 = np.full(n, np.nan)
    vol_method3 = np.full(n, np.nan)
    
    # Pre-compute returns array for easier indexing
    returns = df['return'].values
    
    # Method 1: Recursive calculation with P_t and Q_t
    # Initialize P and Q for the first window
    if n >= window:
        # First window (indices 0 to 89)
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
            variance = sum_sq / (window - 1)
            if variance > 0:
                vol_method2[t] = np.sqrt(variance) * annualization_factor
    
    # Method 3: Exact calculation with standard formula
    # Sum of (r_i - avg_90)^2 for i=0,...,89
    if n >= window:
        for t in range(window-1, n):
            # Get 90 days of returns (indices t-89 to t)
            returns_90 = returns[t-89:t+1]
            
            # Calculate mean and variance
            avg_90 = np.mean(returns_90)
            variance = np.sum((returns_90 - avg_90)**2) / (window - 1)
            
            if variance > 0:
                vol_method3[t] = np.sqrt(variance) * annualization_factor
    
    # Store results
    results['vol_method1_recursive'] = vol_method1
    results['vol_method2_approx'] = vol_method2
    results['vol_method3_exact'] = vol_method3
    
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
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot 1: All three methods together
    ax1 = axes[0]
    ax1.plot(results['date'], results['vol_method1_recursive'], 
             label='Method 1: Recursive (Exact)', alpha=0.8, linewidth=1.5)
    ax1.plot(results['date'], results['vol_method2_approx'], 
             label='Method 2: Approximation (91-day)', alpha=0.8, linewidth=1.5)
    ax1.plot(results['date'], results['vol_method3_exact'], 
             label='Method 3: Standard Exact', alpha=0.8, linewidth=1.5)
    
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Annualized Volatility')
    ax1.set_title('90-Day Rolling Volatility Comparison')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Differences between methods
    ax2 = axes[1]
    
    # Calculate differences
    diff_1_3 = results['vol_method1_recursive'] - results['vol_method3_exact']
    diff_2_3 = results['vol_method2_approx'] - results['vol_method3_exact']
    
    ax2.plot(results['date'], diff_1_3, 
             label='Method 1 vs Method 3 (should be ~0)', alpha=0.8, linewidth=1.5)
    ax2.plot(results['date'], diff_2_3, 
             label='Method 2 vs Method 3 (approximation error)', alpha=0.8, linewidth=1.5)
    
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Volatility Difference')
    ax2.set_title('Differences Between Methods (Relative to Method 3)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.show()
    
    # Print statistics
    print("\n=== Volatility Statistics ===")
    print("\nMethod 1 (Recursive Exact):")
    print(f"  Mean: {results['vol_method1_recursive'].mean():.4f}")
    print(f"  Std:  {results['vol_method1_recursive'].std():.4f}")
    
    print("\nMethod 2 (Approximation with 91 days):")
    print(f"  Mean: {results['vol_method2_approx'].mean():.4f}")
    print(f"  Std:  {results['vol_method2_approx'].std():.4f}")
    
    print("\nMethod 3 (Standard Exact):")
    print(f"  Mean: {results['vol_method3_exact'].mean():.4f}")
    print(f"  Std:  {results['vol_method3_exact'].std():.4f}")
    
    print("\n=== Method Comparison ===")
    print(f"Max absolute difference Method 1 vs 3: {np.nanmax(np.abs(diff_1_3)):.6f}")
    print(f"Max absolute difference Method 2 vs 3: {np.nanmax(np.abs(diff_2_3)):.6f}")
    
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
    
    # Display first few rows of results
    print("\n=== First 95 rows of results ===")
    print(results[['date', 'vol_method1_recursive', 'vol_method2_approx', 'vol_method3_exact']].head(95))
