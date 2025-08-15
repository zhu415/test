import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import warnings

class RealizedVolatilityCalculator:
    """
    Calculate realized volatility for a portfolio using exponentially weighted moving averages
    for both short-term and long-term volatility measures.
    """
    
    def __init__(self, 
                 lambda_s: float = 0.94,  # Short-term decay factor
                 lambda_l: float = 0.97,  # Long-term decay factor
                 n: int = 1,              # Number of days for return calculation
                 N: int = 60,             # Number of trading days for initial variance
                 annualization_factor: int = 252,  # Trading days per year
                 use_log_returns: bool = True):  # Whether to use log returns or ordinary returns
        """
        Initialize the volatility calculator with parameters.
        
        Parameters:
        -----------
        lambda_s : float
            Short-term decay factor for exponential weighting (0 < lambda_s < 1)
        lambda_l : float
            Long-term decay factor for exponential weighting (0 < lambda_l < 1)
        n : int
            Number of days inherent in the return calculation
        N : int
            Number of trading days observed for calculating initial variance
        annualization_factor : int
            Number of trading days per year (typically 252)
        use_log_returns : bool
            If True, use log returns. If False, use ordinary returns
        """
        self.lambda_s = lambda_s
        self.lambda_l = lambda_l
        self.n = n
        self.N = N
        self.annualization_factor = annualization_factor
        self.use_log_returns = use_log_returns
        
        # Validate parameters
        if not (0 < lambda_s < 1):
            raise ValueError("lambda_s must be between 0 and 1")
        if not (0 < lambda_l < 1):
            raise ValueError("lambda_l must be between 0 and 1")
        if n < 1:
            raise ValueError("n must be at least 1")
        if N < 1:
            raise ValueError("N must be at least 1")
    
    def calculate_portfolio_value(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate the portfolio value for each date.
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with columns: 'date', 'symbol', 'weight', 'price_per_share', 
            'number_of_shares', 'fee_price'
        
        Returns:
        --------
        pd.Series
            Portfolio values indexed by date
        """
        # Option 1: Use fee_price as portfolio price (if it represents total portfolio value)
        if 'fee_price' in df.columns:
            portfolio_values = df.groupby('date')['fee_price'].first()
        
        # Option 2: Calculate from components if fee_price is not the portfolio value
        else:
            # Calculate value for each position
            df['position_value'] = df['price_per_share'] * df['number_of_shares']
            
            # Sum position values by date to get portfolio value
            portfolio_values = df.groupby('date')['position_value'].sum()
        
        return portfolio_values.sort_index()
    
    def calculate_weighted_portfolio_returns(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate weighted portfolio returns based on constituent asset returns.
        
        Return on day t is calculated as:
        sum(weight_on_day_t * return_of_asset_on_day_t)
        where return_of_asset = (price_{t+1} / price_t) - 1
        
        Weights are normalized excluding 'USD.CASH' assets.
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with columns: 'date', 'symbol', 'weight', 'price_per_share'
        
        Returns:
        --------
        pd.Series
            Portfolio returns indexed by date
        """
        # Sort by date and symbol for consistent processing
        df_sorted = df.sort_values(['date', 'symbol']).copy()
        
        # Calculate individual asset returns
        asset_returns_list = []
        
        for symbol in df_sorted['symbol'].unique():
            # Get data for this symbol
            symbol_data = df_sorted[df_sorted['symbol'] == symbol].copy()
            symbol_data = symbol_data.sort_values('date')
            
            # Calculate returns: (price_{t+1} / price_t) - 1
            symbol_data['return'] = symbol_data['price_per_share'].pct_change()
            
            # Shift returns back one day so return aligns with the weight day
            # (return from t to t+1 should be associated with weight on day t)
            symbol_data['return'] = symbol_data['return'].shift(-1)
            
            asset_returns_list.append(symbol_data[['date', 'symbol', 'weight', 'return']])
        
        # Combine all asset returns
        all_returns = pd.concat(asset_returns_list, ignore_index=True)
        
        # Calculate weighted returns by date
        portfolio_returns = []
        
        for date in sorted(all_returns['date'].unique()):
            date_data = all_returns[all_returns['date'] == date].copy()
            
            # Exclude USD.CASH from weight normalization
            non_cash_data = date_data[date_data['symbol'] != 'USD.CASH'].copy()
            
            if len(non_cash_data) > 0:
                # Normalize weights of non-cash assets to sum to 1
                weight_sum = non_cash_data['weight'].sum()
                if weight_sum > 0:
                    non_cash_data['normalized_weight'] = non_cash_data['weight'] / weight_sum
                else:
                    non_cash_data['normalized_weight'] = 0
                
                # Calculate weighted return (excluding NaN returns)
                valid_returns = non_cash_data.dropna(subset=['return'])
                if len(valid_returns) > 0:
                    weighted_return = (valid_returns['normalized_weight'] * valid_returns['return']).sum()
                    portfolio_returns.append({
                        'date': date,
                        'return': weighted_return
                    })
        
        # Convert to Series
        returns_df = pd.DataFrame(portfolio_returns)
        if len(returns_df) > 0:
            returns_series = returns_df.set_index('date')['return'].sort_index()
        else:
            returns_series = pd.Series(dtype=float)
        
        return returns_series
    
    def calculate_log_returns(self, prices: pd.Series, lag: int = 1) -> pd.Series:
        """
        Calculate log returns with specified lag.
        
        Parameters:
        -----------
        prices : pd.Series
            Price series indexed by date
        lag : int
            Number of periods to lag for return calculation
        
        Returns:
        --------
        pd.Series
            Log returns
        """
        return np.log(prices / prices.shift(lag))
    
    def calculate_initial_variance(self, 
                                  log_returns: pd.Series, 
                                  T0_idx: int,
                                  is_short_term: bool = True) -> float:
        """
        Calculate initial variance at T0 using weighted historical returns.
        
        Parameters:
        -----------
        log_returns : pd.Series
            Log returns series
        T0_idx : int
            Index position of T0 in the series
        is_short_term : bool
            Whether to use short-term or long-term parameters
        
        Returns:
        --------
        float
            Initial variance at T0
        """
        lambda_val = self.lambda_s if is_short_term else self.lambda_l
        
        # Get the returns from m+1 to T0 (N observations before T0)
        start_idx = max(0, T0_idx - self.N + 1)
        historical_returns = log_returns.iloc[start_idx:T0_idx + 1].dropna()
        
        if len(historical_returns) == 0:
            return 0.0
        
        # Calculate weights
        weights = []
        weighting_factor = 0
        
        for i, _ in enumerate(historical_returns):
            # Weight decreases as we go back in time
            time_from_T0 = len(historical_returns) - 1 - i
            alpha = (1 - lambda_val) * (lambda_val ** time_from_T0)
            weights.append(alpha)
            weighting_factor += alpha
        
        # Normalize weights
        if weighting_factor > 0:
            weights = [w / weighting_factor for w in weights]
        
        # Calculate weighted variance
        squared_returns = historical_returns ** 2
        variance = sum(w * r2 for w, r2 in zip(weights, squared_returns))
        
        return variance
    
    def calculate_ewma_variance(self,
                               log_returns: pd.Series,
                               initial_variance: float,
                               lambda_val: float) -> pd.Series:
        """
        Calculate exponentially weighted moving average variance.
        
        Parameters:
        -----------
        log_returns : pd.Series
            Log returns series
        initial_variance : float
            Initial variance value
        lambda_val : float
            Decay factor
        
        Returns:
        --------
        pd.Series
            EWMA variance series
        """
        variance = pd.Series(index=log_returns.index, dtype=float)
        
        # Set initial variance
        if len(log_returns) > 0:
            variance.iloc[0] = initial_variance
        
        # Calculate EWMA variance for subsequent periods
        for i in range(1, len(log_returns)):
            if pd.isna(log_returns.iloc[i]):
                variance.iloc[i] = variance.iloc[i-1]
            else:
                variance.iloc[i] = (lambda_val * variance.iloc[i-1] + 
                                   (1 - lambda_val) * (log_returns.iloc[i] ** 2))
        
        return variance
    
    def calculate_realized_volatility(self, 
                                     df: pd.DataFrame,
                                     T0_date: Optional[str] = None,
                                     use_weighted_returns: bool = False) -> pd.DataFrame:
        """
        Calculate realized volatility for the portfolio.
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with portfolio data
        T0_date : str, optional
            Start date for the index (format: 'YYYY-MM-DD')
            If None, uses the date after N observations
        use_weighted_returns : bool
            If True, use weighted portfolio returns based on constituent assets
            If False, use portfolio value changes (fee_price or calculated value)
        
        Returns:
        --------
        pd.DataFrame
            DataFrame with columns: date, short_term_vol, long_term_vol, realized_vol
        """
        # Get returns based on method choice
        if use_weighted_returns:
            # Use weighted portfolio returns from constituent assets
            returns = self.calculate_weighted_portfolio_returns(df)
            
            # If not using log returns, the returns are already calculated
            if self.use_log_returns:
                # Convert ordinary returns to log returns
                returns = np.log(1 + returns)
        else:
            # Use portfolio value method (original)
            portfolio_values = self.calculate_portfolio_value(df)
            
            if self.use_log_returns:
                returns = self.calculate_log_returns(portfolio_values, lag=self.n)
            else:
                # Calculate ordinary returns
                returns = portfolio_values.pct_change(periods=self.n)
        
        # Determine T0
        if T0_date:
            T0_idx = returns.index.get_loc(pd.Timestamp(T0_date))
        else:
            T0_idx = min(self.N, len(returns) - 1)
        
        # Calculate initial variances at T0
        initial_var_s = self.calculate_initial_variance(returns, T0_idx, is_short_term=True)
        initial_var_l = self.calculate_initial_variance(returns, T0_idx, is_short_term=False)
        
        # Calculate EWMA variances starting from T0
        returns_from_T0 = returns.iloc[T0_idx:]
        
        # Short-term variance
        variance_s = self.calculate_ewma_variance(returns_from_T0, initial_var_s, self.lambda_s)
        
        # Long-term variance
        variance_l = self.calculate_ewma_variance(returns_from_T0, initial_var_l, self.lambda_l)
        
        # Convert variance to volatility (annualized)
        vol_s = np.sqrt((self.annualization_factor / self.n) * variance_s)
        vol_l = np.sqrt((self.annualization_factor / self.n) * variance_l)
        
        # Realized volatility is the maximum of short-term and long-term
        realized_vol = pd.DataFrame({
            'date': variance_s.index,
            'short_term_vol': vol_s.values,
            'long_term_vol': vol_l.values
        })
        
        realized_vol['realized_vol'] = realized_vol[['short_term_vol', 'long_term_vol']].max(axis=1)
        
        return realized_vol
    
    def calculate_with_leverage(self,
                               df: pd.DataFrame,
                               target_volatility: float,
                               max_leverage: float,
                               lag_days: int = 2,
                               T0_date: Optional[str] = None,
                               use_weighted_returns: bool = False) -> pd.DataFrame:
        """
        Calculate realized volatility and leverage factors.
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with portfolio data
        target_volatility : float
            Target volatility level
        max_leverage : float
            Maximum allowed leverage
        lag_days : int
            Lag between leverage calculation and implementation
        T0_date : str, optional
            Start date for the index
        use_weighted_returns : bool
            If True, use weighted portfolio returns based on constituent assets
        
        Returns:
        --------
        pd.DataFrame
            DataFrame with volatility measures and leverage factors
        """
        # Calculate realized volatility
        vol_df = self.calculate_realized_volatility(df, T0_date, use_weighted_returns)
        
        # Calculate leverage factor (with lag)
        vol_df['leverage_factor'] = target_volatility / vol_df['realized_vol']
        vol_df['leverage_factor'] = vol_df['leverage_factor'].clip(upper=max_leverage)
        
        # Apply lag to leverage implementation
        vol_df['applied_leverage'] = vol_df['leverage_factor'].shift(lag_days)
        vol_df['applied_leverage'] = vol_df['applied_leverage'].fillna(1.0)
        
        return vol_df


# Utility function for plotting (optional)
def plot_volatility(vol_df: pd.DataFrame, figsize=(12, 8)):
    """
    Plot the volatility measures over time.
    
    Parameters:
    -----------
    vol_df : pd.DataFrame
        DataFrame with volatility results
    figsize : tuple
        Figure size for the plot
    """
    import matplotlib.pyplot as plt
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize)
    
    # Plot volatilities
    ax1.plot(vol_df['date'], vol_df['short_term_vol'], label='Short-term Vol', alpha=0.7)
    ax1.plot(vol_df['date'], vol_df['long_term_vol'], label='Long-term Vol', alpha=0.7)
    ax1.plot(vol_df['date'], vol_df['realized_vol'], label='Realized Vol', linewidth=2)
    ax1.set_ylabel('Volatility')
    ax1.set_title('Portfolio Realized Volatility')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot leverage if available
    if 'applied_leverage' in vol_df.columns:
        ax2.plot(vol_df['date'], vol_df['applied_leverage'], label='Applied Leverage', color='green')
        ax2.set_ylabel('Leverage Factor')
        ax2.set_xlabel('Date')
        ax2.set_title('Leverage Factor Over Time')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
    else:
        ax2.set_visible(False)
    
    plt.tight_layout()
    plt.show()
    
    return fig


# ============================================
# EXAMPLE USAGE IN JUPYTER NOTEBOOK
# ============================================

# Step 1: Initialize the calculator with your parameters
# For log returns (original method):
calc_log = RealizedVolatilityCalculator(
    lambda_s=0.94,  # Short-term decay factor
    lambda_l=0.97,  # Long-term decay factor  
    n=1,            # Daily returns (n=1 for daily, n=5 for weekly)
    N=60,           # 60 days for initial variance calculation
    use_log_returns=True  # Use log returns
)

# For ordinary returns:
calc_ordinary = RealizedVolatilityCalculator(
    lambda_s=0.94,
    lambda_l=0.97,
    n=1,
    N=60,
    use_log_returns=False  # Use ordinary returns
)

# Step 2: Calculate realized volatility using portfolio values (original method)
# volatility_results = calc_log.calculate_realized_volatility(
#     df,
#     T0_date='2024-03-01'
# )

# Step 3: Calculate using weighted portfolio returns (new method)
# volatility_weighted = calc_ordinary.calculate_realized_volatility(
#     df,
#     T0_date='2024-03-01',
#     use_weighted_returns=True  # Use weighted returns from constituent assets
# )

# Step 4: Compare both methods
# print("Portfolio value method:")
# print(volatility_results.head())
# print("\nWeighted returns method:")
# print(volatility_weighted.head())

# ============================================
# QUICK START EXAMPLE WITH SAMPLE DATA
# ============================================

# Create sample data for testing
def create_sample_data(n_days=100, n_assets=3):
    """Create sample portfolio data for testing"""
    dates = pd.date_range('2024-01-01', periods=n_days, freq='D')
    symbols = ['AAPL', 'GOOGL', 'MSFT']
    
    data = []
    for date in dates:
        for i, symbol in enumerate(symbols):
            data.append({
                'date': date,
                'symbol': symbol,
                'weight': [0.4, 0.35, 0.25][i],
                'price_per_share': np.random.uniform(100, 200),
                'number_of_shares': [100, 50, 75][i],
                'fee_price': np.random.uniform(50000, 60000)  # Portfolio value
            })
    
    return pd.DataFrame(data)

# Test with sample data
# sample_df = create_sample_data(n_days=200)
# sample_results = calc.calculate_realized_volatility(sample_df)
# print("Sample Results:")
# print(sample_results.describe())
