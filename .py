import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

def optimize_parameters_with_T0(df, target_vol_df, T0_dates=None):
    """
    Find optimal lambda parameters and T0_date by minimizing MSE against target volatility.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Your portfolio data
    target_vol_df : pd.DataFrame
        DataFrame containing 'date' and target volatility column
    T0_dates : list of str, optional
        List of T0 dates to test. If None, will auto-generate candidates
    """
    # Get the target volatility column name
    target_col = [col for col in target_vol_df.columns if col != 'date'][0]
    
    # Generate T0_date candidates if not provided
    if T0_dates is None:
        # Get unique dates from the dataframe
        unique_dates = sorted(df['date'].unique())
        
        # Create T0 candidates: every 30 days from day 60 to day 180
        T0_candidates = []
        for i in range(60, min(180, len(unique_dates)), 30):
            T0_candidates.append(str(unique_dates[i].date()) if hasattr(unique_dates[i], 'date') else str(unique_dates[i]))
    else:
        T0_candidates = T0_dates
    
    best_params = None
    best_mse = float('inf')
    best_result = None
    
    # Parameter ranges to test
    lambda_s_range = np.arange(0.85, 0.95, 0.02)
    lambda_l_range = np.arange(0.90, 0.98, 0.02)
    N_range = [20, 30, 40, 60]
    
    total_combinations = len(lambda_s_range) * len(lambda_l_range) * len(N_range) * len(T0_candidates)
    current = 0
    
    print(f"Testing {total_combinations} parameter combinations...")
    print(f"T0 dates to test: {T0_candidates}")
    print("-" * 60)
    
    for T0_date in T0_candidates:
        for ls in lambda_s_range:
            for ll in lambda_l_range:
                for N in N_range:
                    current += 1
                    
                    if ls >= ll:  # Skip if short-term decay >= long-term decay
                        continue
                    
                    try:
                        calc = RealizedVolatilityCalculator(
                            lambda_s=ls,
                            lambda_l=ll,
                            n=1,
                            N=N
                        )
                        
                        result = calc.calculate_realized_volatility(df, T0_date)
                        
                        # Rename column to avoid conflicts
                        result_renamed = result[['date', 'realized_vol']].rename(
                            columns={'realized_vol': 'ewma_vol'}
                        )
                        
                        # Merge on date to align the series
                        merged = pd.merge(
                            result_renamed,
                            target_vol_df[['date', target_col]],
                            on='date',
                            how='inner'
                        )
                        
                        # Calculate MSE only on matched dates
                        if len(merged) > 0:
                            mse = mean_squared_error(
                                merged[target_col],
                                merged['ewma_vol']
                            )
                            
                            if mse < best_mse:
                                best_mse = mse
                                best_params = {
                                    'lambda_s': ls,
                                    'lambda_l': ll,
                                    'N': N,
                                    'T0_date': T0_date,
                                    'matched_dates': len(merged),
                                    'mse': mse
                                }
                                best_result = result
                                print(f"New best: T0={T0_date}, λs={ls:.3f}, λl={ll:.3f}, "
                                      f"N={N}, MSE={mse:.6f}, Matched={len(merged)}")
                        
                    except Exception as e:
                        if current % 100 == 0:  # Only print errors occasionally to avoid spam
                            print(f"Error at combination {current}/{total_combinations}: {e}")
                        continue
    
    print("-" * 60)
    print(f"Best parameters found:")
    print(f"  T0_date: {best_params['T0_date']}")
    print(f"  lambda_s: {best_params['lambda_s']:.3f}")
    print(f"  lambda_l: {best_params['lambda_l']:.3f}")
    print(f"  N: {best_params['N']}")
    print(f"  MSE: {best_params['mse']:.6f}")
    print(f"  Matched dates: {best_params['matched_dates']}")
    
    return best_params, best_result

# Simpler version for quick T0_date testing with fixed other parameters
def test_T0_dates(df, target_vol_df, lambda_s=0.90, lambda_l=0.94, N=30, T0_dates=None):
    """
    Test different T0_dates with fixed lambda parameters.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Your portfolio data
    target_vol_df : pd.DataFrame
        DataFrame with 'date' and target volatility
    lambda_s, lambda_l, N : float, float, int
        Fixed parameters to use
    T0_dates : list of str
        List of T0 dates to test
    """
    target_col = [col for col in target_vol_df.columns if col != 'date'][0]
    
    if T0_dates is None:
        # Auto-generate T0 candidates
        unique_dates = sorted(df['date'].unique())
        T0_dates = []
        for i in range(30, min(180, len(unique_dates)), 15):  # Every 15 days
            date_str = str(unique_dates[i].date()) if hasattr(unique_dates[i], 'date') else str(unique_dates[i])
            T0_dates.append(date_str)
    
    results = []
    
    calc = RealizedVolatilityCalculator(
        lambda_s=lambda_s,
        lambda_l=lambda_l,
        n=1,
        N=N
    )
    
    for T0_date in T0_dates:
        try:
            result = calc.calculate_realized_volatility(df, T0_date)
            
            # Rename to avoid conflicts
            result_renamed = result[['date', 'realized_vol']].rename(
                columns={'realized_vol': 'ewma_vol'}
            )
            
            merged = pd.merge(
                result_renamed,
                target_vol_df[['date', target_col]],
                on='date',
                how='inner'
            )
            
            if len(merged) > 0:
                mse = mean_squared_error(merged[target_col], merged['ewma_vol'])
                mae = np.mean(np.abs(merged[target_col] - merged['ewma_vol']))
                
                results.append({
                    'T0_date': T0_date,
                    'mse': mse,
                    'mae': mae,
                    'matched_dates': len(merged),
                    'mean_target': merged[target_col].mean(),
                    'mean_ewma': merged['ewma_vol'].mean()
                })
                
                print(f"T0={T0_date}: MSE={mse:.6f}, MAE={mae:.6f}, "
                      f"Matched={len(merged)}, "
                      f"Mean_diff={merged['ewma_vol'].mean() - merged[target_col].mean():.4f}")
        
        except Exception as e:
            print(f"Error with T0={T0_date}: {e}")
            continue
    
    # Convert to DataFrame for easy analysis
    results_df = pd.DataFrame(results)
    if len(results_df) > 0:
        results_df = results_df.sort_values('mse')
        print("\nBest T0_date results:")
        print(results_df.head())
    
    return results_df

# Usage examples:

# 1. Full grid search including T0_dates
# best_params, best_result = optimize_parameters_with_T0(
#     df, 
#     target_vol_df,
#     T0_dates=['2022-03-01', '2022-04-01', '2022-05-01', '2022-06-01']
# )

# 2. Test only T0_dates with fixed parameters
# t0_results = test_T0_dates(
#     df,
#     target_vol_df,
#     lambda_s=0.90,
#     lambda_l=0.94,
#     N=30,
#     T0_dates=['2022-02-01', '2022-03-01', '2022-04-01', '2022-05-01']
# )

# 3. Visualize results for different T0_dates
def plot_T0_comparison(df, target_vol_df, T0_dates, lambda_s=0.90, lambda_l=0.94, N=30):
    """
    Plot volatility curves for different T0_dates to visualize the impact.
    """
    import matplotlib.pyplot as plt
    
    target_col = [col for col in target_vol_df.columns if col != 'date'][0]
    
    fig, axes = plt.subplots(len(T0_dates), 1, figsize=(12, 4*len(T0_dates)))
    if len(T0_dates) == 1:
        axes = [axes]
    
    calc = RealizedVolatilityCalculator(lambda_s=lambda_s, lambda_l=lambda_l, n=1, N=N)
    
    for idx, T0_date in enumerate(T0_dates):
        ax = axes[idx]
        
        try:
            result = calc.calculate_realized_volatility(df, T0_date)
            result_renamed = result[['date', 'realized_vol']].rename(
                columns={'realized_vol': 'ewma_vol'}
            )
            
            merged = pd.merge(
                result_renamed,
                target_vol_df[['date', target_col]],
                on='date',
                how='inner'
            )
            
            mse = mean_squared_error(merged[target_col], merged['ewma_vol'])
            
            ax.plot(merged['date'], merged[target_col], label='Target Vol', alpha=0.7, color='blue')
            ax.plot(merged['date'], merged['ewma_vol'], label='EWMA Vol', alpha=0.7, color='red')
            ax.axvline(pd.to_datetime(T0_date), color='green', linestyle='--', alpha=0.5, label='T0')
            ax.set_title(f'T0={T0_date}, MSE={mse:.6f}')
            ax.set_xlabel('Date')
            ax.set_ylabel('Volatility')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Error with T0={T0_date}', transform=ax.transAxes)
    
    plt.tight_layout()
    plt.show()

# Usage:
# plot_T0_comparison(
#     df, 
#     target_vol_df,
#     T0_dates=['2022-02-01', '2022-03-01', '2022-04-01'],
#     lambda_s=0.90,
#     lambda_l=0.94,
#     N=30
# )
