import numpy as np
from sklearn.metrics import mean_squared_error
import pandas as pd

def optimize_parameters(df, target_vol_df, T0_date=None):
    """
    Find optimal lambda parameters by minimizing MSE against target volatility.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Your portfolio data
    target_vol_df : pd.DataFrame
        DataFrame containing 'date' and target volatility column
    T0_date : str, optional
        Start date for calculation
    """
    # Get the target volatility column name (assuming it's not 'date')
    target_col = [col for col in target_vol_df.columns if col != 'date'][0]
    
    best_params = None
    best_mse = float('inf')
    best_result = None
    
    # Parameter ranges to test
    lambda_s_range = np.arange(0.85, 0.95, 0.02)
    lambda_l_range = np.arange(0.90, 0.98, 0.02)
    N_range = [20, 30, 40, 60]
    
    for ls in lambda_s_range:
        for ll in lambda_l_range:
            for N in N_range:
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
                    
                    # IMPORTANT: Merge on date to align the series
                    merged = pd.merge(
                        result[['date', 'realized_vol']], 
                        target_vol_df[['date', target_col]], 
                        on='date', 
                        how='inner'  # Only compare dates that exist in both
                    )
                    
                    # Calculate MSE only on matched dates
                    if len(merged) > 0:
                        mse = mean_squared_error(
                            merged[target_col], 
                            merged['realized_vol']
                        )
                        
                        if mse < best_mse:
                            best_mse = mse
                            best_params = {
                                'lambda_s': ls, 
                                'lambda_l': ll, 
                                'N': N,
                                'matched_dates': len(merged)
                            }
                            best_result = result
                            print(f"New best: λs={ls:.3f}, λl={ll:.3f}, N={N}, "
                                  f"MSE={mse:.6f}, Matched dates={len(merged)}")
                        
                except Exception as e:
                    print(f"Error with λs={ls}, λl={ll}, N={N}: {e}")
                    continue
    
    return best_params, best_result

# Example usage:
# Assuming your target volatility dataframe is called 'target_df' with columns ['date', 'target_vol']
# best_params, best_result = optimize_parameters(df, target_df, T0_date='2022-01-01')
