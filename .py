import numpy as np
from sklearn.metrics import mean_squared_error
import pandas as pd

def optimize_parameters_full(df, target_vol_df, 
                            T0_dates=None,
                            test_log_returns=True,
                            test_ordinary_returns=True,
                            use_weighted_returns=False):
    """
    Find optimal lambda parameters, T0_date, and return type by minimizing MSE against target volatility.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Your portfolio data
    target_vol_df : pd.DataFrame
        DataFrame containing 'date' and target volatility column
    T0_dates : list of str, optional
        List of start dates to test. If None, auto-generates candidates
    test_log_returns : bool
        Whether to test log returns
    test_ordinary_returns : bool
        Whether to test ordinary returns
    use_weighted_returns : bool
        Whether to use weighted portfolio returns from constituent assets
    """
    # Get the target volatility column name
    target_col = [col for col in target_vol_df.columns if col != 'date'][0]
    
    # Generate T0_date candidates if not provided
    if T0_dates is None:
        unique_dates = sorted(df['date'].unique())
        T0_dates = []
        # Create candidates from day 60 to day 180, every 30 days
        for i in range(60, min(180, len(unique_dates)), 30):
            date_str = str(unique_dates[i].date()) if hasattr(unique_dates[i], 'date') else str(unique_dates[i])
            T0_dates.append(date_str)
        if len(T0_dates) == 0:  # Fallback if dataset is small
            T0_dates = [None]  # Use default T0
    
    best_params = None
    best_mse = float('inf')
    best_result = None
    
    # Parameter ranges to test
    lambda_s_range = np.arange(0.85, 0.95, 0.02)
    lambda_l_range = np.arange(0.90, 0.98, 0.02)
    N_range = [20, 30, 40, 60]
    
    # Return types to test
    return_types = []
    if test_log_returns:
        return_types.append(True)
    if test_ordinary_returns:
        return_types.append(False)
    
    total_combinations = (len(lambda_s_range) * len(lambda_l_range) * 
                         len(N_range) * len(T0_dates) * len(return_types))
    current = 0
    
    print(f"Testing {total_combinations} parameter combinations...")
    print(f"T0 dates: {T0_dates}")
    print(f"Return types: {['log' if rt else 'ordinary' for rt in return_types]}")
    print(f"Using weighted returns: {use_weighted_returns}")
    print("-" * 70)
    
    for use_log_returns in return_types:
        for T0_date in T0_dates:
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
                                N=N,
                                use_log_returns=use_log_returns
                            )
                            
                            result = calc.calculate_realized_volatility(
                                df, 
                                T0_date,
                                use_weighted_returns=use_weighted_returns
                            )
                            
                            # Rename to avoid merge conflicts
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
                                        'use_log_returns': use_log_returns,
                                        'matched_dates': len(merged),
                                        'mse': mse
                                    }
                                    best_result = result
                                    
                                    return_type = "log" if use_log_returns else "ordinary"
                                    print(f"New best: {return_type} returns, T0={T0_date}, "
                                          f"λs={ls:.3f}, λl={ll:.3f}, N={N}, "
                                          f"MSE={mse:.6f}, Matched={len(merged)}")
                            
                        except Exception as e:
                            if current % 100 == 0:  # Print errors occasionally
                                print(f"Error at {current}/{total_combinations}: {e}")
                            continue
    
    print("-" * 70)
    if best_params:
        print(f"Best parameters found:")
        print(f"  Return type: {'log' if best_params['use_log_returns'] else 'ordinary'}")
        print(f"  T0_date: {best_params['T0_date']}")
        print(f"  lambda_s: {best_params['lambda_s']:.3f}")
        print(f"  lambda_l: {best_params['lambda_l']:.3f}")
        print(f"  N: {best_params['N']}")
        print(f"  MSE: {best_params['mse']:.6f}")
        print(f"  Matched dates: {best_params['matched_dates']}")
    
    return best_params, best_result


def quick_compare_return_types(df, target_vol_df, 
                              lambda_s=0.90, lambda_l=0.94, N=30,
                              T0_date=None, use_weighted_returns=False):
    """
    Quick comparison of log vs ordinary returns with fixed parameters.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Your portfolio data
    target_vol_df : pd.DataFrame
        DataFrame with 'date' and target volatility
    lambda_s, lambda_l, N : float, float, int
        Fixed parameters
    T0_date : str, optional
        Start date
    use_weighted_returns : bool
        Whether to use weighted portfolio returns
    """
    target_col = [col for col in target_vol_df.columns if col != 'date'][0]
    
    results = {}
    
    for use_log_returns in [True, False]:
        return_type = "log" if use_log_returns else "ordinary"
        
        try:
            calc = RealizedVolatilityCalculator(
                lambda_s=lambda_s,
                lambda_l=lambda_l,
                n=1,
                N=N,
                use_log_returns=use_log_returns
            )
            
            result = calc.calculate_realized_volatility(
                df, 
                T0_date,
                use_weighted_returns=use_weighted_returns
            )
            
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
                
                results[return_type] = {
                    'mse': mse,
                    'mae': mae,
                    'mean_target': merged[target_col].mean(),
                    'mean_ewma': merged['ewma_vol'].mean(),
                    'matched_dates': len(merged),
                    'result_df': result
                }
                
                print(f"{return_type.upper()} returns:")
                print(f"  MSE: {mse:.6f}")
                print(f"  MAE: {mae:.6f}")
                print(f"  Mean difference: {merged['ewma_vol'].mean() - merged[target_col].mean():.4f}")
                print(f"  Matched dates: {len(merged)}")
                print()
                
        except Exception as e:
            print(f"Error with {return_type} returns: {e}")
    
    return results


def optimize_with_constraints(df, target_vol_df, 
                             lambda_s_range=None,
                             lambda_l_range=None,
                             N_range=None,
                             T0_dates=None,
                             force_log_returns=None,
                             use_weighted_returns=False):
    """
    Optimization with custom parameter ranges and constraints.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Your portfolio data
    target_vol_df : pd.DataFrame
        Target volatility data
    lambda_s_range : array-like, optional
        Custom range for lambda_s (default: 0.85-0.95)
    lambda_l_range : array-like, optional
        Custom range for lambda_l (default: 0.90-0.98)
    N_range : list, optional
        Custom range for N (default: [20, 30, 40, 60])
    T0_dates : list, optional
        Custom T0 dates to test
    force_log_returns : bool, optional
        If True, only test log returns. If False, only test ordinary. If None, test both.
    use_weighted_returns : bool
        Whether to use weighted portfolio returns
    """
    # Set default ranges if not provided
    if lambda_s_range is None:
        lambda_s_range = np.arange(0.85, 0.95, 0.02)
    if lambda_l_range is None:
        lambda_l_range = np.arange(0.90, 0.98, 0.02)
    if N_range is None:
        N_range = [20, 30, 40, 60]
    
    # Determine which return types to test
    test_log = True
    test_ordinary = True
    if force_log_returns is not None:
        test_log = force_log_returns
        test_ordinary = not force_log_returns
    
    return optimize_parameters_full(
        df, 
        target_vol_df,
        T0_dates=T0_dates,
        test_log_returns=test_log,
        test_ordinary_returns=test_ordinary,
        use_weighted_returns=use_weighted_returns
    )


# Example usage:
"""
# 1. Full optimization with all parameters
best_params, best_result = optimize_parameters_full(
    df, 
    target_vol_df,
    T0_dates=['2022-03-01', '2022-04-01', '2022-05-01'],
    test_log_returns=True,
    test_ordinary_returns=True,
    use_weighted_returns=False  # Set to True to use weighted returns
)

# 2. Quick comparison of return types
comparison = quick_compare_return_types(
    df,
    target_vol_df,
    lambda_s=0.90,
    lambda_l=0.94,
    N=30,
    T0_date='2022-03-01',
    use_weighted_returns=False
)

# 3. Optimize with constraints (e.g., only ordinary returns, specific T0 dates)
best_params, best_result = optimize_with_constraints(
    df,
    target_vol_df,
    lambda_s_range=np.arange(0.88, 0.92, 0.01),  # Finer grid
    lambda_l_range=np.arange(0.93, 0.96, 0.01),
    N_range=[25, 30, 35],
    T0_dates=['2022-03-15', '2022-04-01'],
    force_log_returns=False,  # Only test ordinary returns
    use_weighted_returns=True  # Use weighted portfolio returns
)
"""
