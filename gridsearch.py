import numpy as np
from sklearn.metrics import mean_squared_error

def optimize_parameters(df, target_vol, T0_date=None):
    """
    Find optimal lambda parameters by minimizing MSE against target volatility.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Your portfolio data
    target_vol : pd.Series or np.array
        The desired volatility values (blue line in your chart)
    """
    best_params = None
    best_mse = float('inf')
    
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
                    
                    # Align the series and calculate MSE
                    # You'll need to align result['realized_vol'] with target_vol
                    mse = mean_squared_error(target_vol, result['realized_vol'])
                    
                    if mse < best_mse:
                        best_mse = mse
                        best_params = {'lambda_s': ls, 'lambda_l': ll, 'N': N}
                        print(f"New best: λs={ls:.3f}, λl={ll:.3f}, N={N}, MSE={mse:.6f}")
                        
                except Exception as e:
                    continue
    
    return best_params

# Use the optimal parameters
# best = optimize_parameters(df, target_volatility_series)
