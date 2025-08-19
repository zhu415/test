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
                 use_log_returns: bool = True,     # Whether to use log returns in EWMA
                 use_normalized_price: bool = False,  # For log returns: whether to use normalized weighted price
                 use_individual_log_returns: bool = False):  # For log returns: whether to use weighted individual log returns
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
            If True, use log returns in EWMA. If False, use weighted returns in EWMA
        use_normalized_price : bool
            Only applies when use_log_returns=True and use_individual_log_returns=False. 
            If False: log return = log(fee_price_t / fee_price_{t-1})
            If True: uses normalized weighted prices from non-cash components
        use_individual_log_returns : bool
            Only applies when use_log_returns=True.
            If True: calculate log returns of individual assets, then apply weights
        """
        self.lambda_s = lambda_s
        self.lambda_l = lambda_l
        self.n = n
        self.N = N
        self.annualization_factor = annualization_factor
        self.use_log_returns = use_log_returns
        self.use_normalized_price = use_normalized_price
        self.use_individual_log_returns = use_individual_log_returns
        
        # Validate parameters
        if not (0 < lambda_s < 1):
            raise ValueError("lambda_s must be between 0 and 1")
        if not (0 < lambda_l < 1):
            raise ValueError("lambda_l must be between 0 and 1")
        if n < 1:
            raise ValueError("n must be at least 1")
        if N < 1:
            raise ValueError("N must be at least 1")
        
        # Validate logical combinations
        if use_individual_log_returns and not use_log_returns:
            raise ValueError("use_individual_log_returns requires use_log_returns=True")
        if use_individual_log_returns and use_normalized_price:
            print("Warning: use_individual_log_returns=True overrides use_normalized_price")
    
    def calculate_portfolio_value(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate the portfolio value for each date.
        
        For non-weighted method: Uses fee_price if available.
        For weighted method: Calculates weighted price using normalized non-cash weights.
        
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
    
    def calculate_weighted_portfolio_returns(self, df: pd.DataFrame, lag: Optional[int] = None) -> pd.Series:
        """
        Calculate weighted portfolio returns based on constituent asset returns.
        
        Return on date t is calculated as:
        sum(weight_on_date_{t-lag} * return_of_asset_from_{t-lag}_to_t)
        where return_of_asset = (price_t - price_{t-lag}) / price_{t-lag}
        
        Weights are normalized excluding 'USD.CASH' assets.
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with columns: 'date', 'symbol', 'weight', 'price_per_share'
        lag : int, optional
            Number of periods for return calculation. If None, uses self.n
        
        Returns:
        --------
        pd.Series
            Portfolio returns indexed by date
        """
        if lag is None:
            lag = self.n
            
        # Sort by date and symbol for consistent processing
        df_sorted = df.sort_values(['date', 'symbol']).copy()
        
        # Get unique dates sorted
        unique_dates = sorted(df_sorted['date'].unique())
        
        portfolio_returns = []
        
        # Process each date (starting from lag-th date since we need previous weights)
        for i in range(lag, len(unique_dates)):
            current_date = unique_dates[i]
            previous_date = unique_dates[i-lag]  # Use lag periods back
            
            # Get previous date's weights (excluding USD.CASH)
            prev_data = df_sorted[df_sorted['date'] == previous_date].copy()
            prev_data = prev_data[prev_data['symbol'] != 'USD.CASH'].copy()
            
            # Get current date's prices
            curr_data = df_sorted[df_sorted['date'] == current_date].copy()
            curr_data = curr_data[curr_data['symbol'] != 'USD.CASH'].copy()
            
            # Normalize previous weights
            if len(prev_data) > 0:
                weight_sum = prev_data['weight'].sum()
                if weight_sum > 0:
                    prev_data['normalized_weight'] = prev_data['weight'] / weight_sum
                else:
                    continue
                
                # Calculate returns for each asset
                weighted_return = 0
                for _, prev_row in prev_data.iterrows():
                    symbol = prev_row['symbol']
                    
                    # Find matching symbol in current date
                    curr_symbol_data = curr_data[curr_data['symbol'] == symbol]
                    if len(curr_symbol_data) > 0:
                        curr_price = curr_symbol_data['price_per_share'].iloc[0]
                        prev_price = prev_row['price_per_share']
                        
                        if prev_price > 0:  # Avoid division by zero
                            # Calculate return: (price_t - price_{t-lag}) / price_{t-lag}
                            asset_return = (curr_price - prev_price) / prev_price
                            # Apply normalized weight from previous date
                            weighted_return += prev_row['normalized_weight'] * asset_return
                
                portfolio_returns.append({
                    'date': current_date,
                    'return': weighted_return
                })
        
        # Convert to Series
        if len(portfolio_returns) > 0:
            returns_df = pd.DataFrame(portfolio_returns)
            returns_series = returns_df.set_index('date')['return'].sort_index()
        else:
            returns_series = pd.Series(dtype=float)
        
        return returns_series
    
    def calculate_normalized_price_returns(self, df: pd.DataFrame, lag: Optional[int] = None) -> pd.Series:
        """
        Calculate returns using normalized weighted prices (holding weights constant).
        
        Return on date t = (P_t - P_{t-lag}) / P_{t-lag}
        where P_t = sum(normalized_weight_{t-lag} * price_t) for non-USD.CASH assets
        
        This represents holding the same shares from t-lag to t, with returns from price changes.
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with columns: 'date', 'symbol', 'weight', 'price_per_share'
        lag : int, optional
            Number of periods for return calculation. If None, uses self.n
        
        Returns:
        --------
        pd.Series
            Returns indexed by date
        """
        if lag is None:
            lag = self.n
            
        # Sort by date and symbol for consistent processing
        df_sorted = df.sort_values(['date', 'symbol']).copy()
        
        # Get unique dates sorted
        unique_dates = sorted(df_sorted['date'].unique())
        
        portfolio_returns = []
        
        # Process each date (starting from lag-th date)
        for i in range(lag, len(unique_dates)):
            current_date = unique_dates[i]
            previous_date = unique_dates[i-lag]  # Use lag periods back
            
            # Get previous date's data (excluding USD.CASH)
            prev_data = df_sorted[df_sorted['date'] == previous_date].copy()
            prev_data = prev_data[prev_data['symbol'] != 'USD.CASH'].copy()
            
            # Get current date's data (excluding USD.CASH)
            curr_data = df_sorted[df_sorted['date'] == current_date].copy()
            curr_data = curr_data[curr_data['symbol'] != 'USD.CASH'].copy()
            
            # Normalize previous weights
            if len(prev_data) > 0:
                weight_sum = prev_data['weight'].sum()
                if weight_sum > 0:
                    prev_data['normalized_weight'] = prev_data['weight'] / weight_sum
                else:
                    continue
                
                # Calculate portfolio values using previous weights
                prev_portfolio_value = 0
                curr_portfolio_value = 0
                
                for _, prev_row in prev_data.iterrows():
                    symbol = prev_row['symbol']
                    normalized_weight = prev_row['normalized_weight']
                    prev_price = prev_row['price_per_share']
                    
                    # Previous portfolio value component
                    prev_portfolio_value += normalized_weight * prev_price
                    
                    # Find matching symbol in current date
                    curr_symbol_data = curr_data[curr_data['symbol'] == symbol]
                    if len(curr_symbol_data) > 0:
                        curr_price = curr_symbol_data['price_per_share'].iloc[0]
                        # Current portfolio value using PREVIOUS weights
                        curr_portfolio_value += normalized_weight * curr_price
                
                # Calculate return
                if prev_portfolio_value > 0:
                    portfolio_return = (curr_portfolio_value - prev_portfolio_value) / prev_portfolio_value
                    
                    portfolio_returns.append({
                        'date': current_date,
                        'return': portfolio_return
                    })
        
        # Convert to Series
        if len(portfolio_returns) > 0:
            returns_df = pd.DataFrame(portfolio_returns)
            returns_series = returns_df.set_index('date')['return'].sort_index()
        else:
            returns_series = pd.Series(dtype=float)
        
        return returns_series
    
    def calculate_weighted_individual_log_returns(self, df: pd.DataFrame, lag: Optional[int] = None) -> pd.Series:
        """
        Calculate weighted sum of individual asset log returns.
        
        Return on date t = sum(normalized_weight_{t-lag} * log(price_t / price_{t-lag}))
        for non-USD.CASH assets
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with columns: 'date', 'symbol', 'weight', 'price_per_share'
        lag : int, optional
            Number of periods for return calculation. If None, uses self.n
        
        Returns:
        --------
        pd.Series
            Weighted log returns indexed by date
        """
        if lag is None:
            lag = self.n
            
        # Sort by date and symbol for consistent processing
        df_sorted = df.sort_values(['date', 'symbol']).copy()
        
        # Get unique dates sorted
        unique_dates = sorted(df_sorted['date'].unique())
        
        portfolio_returns = []
        
        # Process each date (starting from lag-th date)
        for i in range(lag, len(unique_dates)):
            current_date = unique_dates[i]
            previous_date = unique_dates[i-lag]  # Use lag periods back
            
            # Get previous date's weights (excluding USD.CASH)
            prev_data = df_sorted[df_sorted['date'] == previous_date].copy()
            prev_data = prev_data[prev_data['symbol'] != 'USD.CASH'].copy()
            
            # Get current date's prices (excluding USD.CASH)
            curr_data = df_sorted[df_sorted['date'] == current_date].copy()
            curr_data = curr_data[curr_data['symbol'] != 'USD.CASH'].copy()
            
            # Normalize previous weights
            if len(prev_data) > 0:
                weight_sum = prev_data['weight'].sum()
                if weight_sum > 0:
                    prev_data['normalized_weight'] = prev_data['weight'] / weight_sum
                else:
                    continue
                
                # Calculate weighted log return
                weighted_log_return = 0
                
                for _, prev_row in prev_data.iterrows():
                    symbol = prev_row['symbol']
                    normalized_weight = prev_row['normalized_weight']
                    prev_price = prev_row['price_per_share']
                    
                    # Find matching symbol in current date
                    curr_symbol_data = curr_data[curr_data['symbol'] == symbol]
                    if len(curr_symbol_data) > 0 and prev_price > 0:
                        curr_price = curr_symbol_data['price_per_share'].iloc[0]
                        
                        # Calculate individual asset log return
                        individual_log_return = np.log(curr_price / prev_price)
                        
                        # Apply weight from previous date
                        weighted_log_return += normalized_weight * individual_log_return
                
                portfolio_returns.append({
                    'date': current_date,
                    'return': weighted_log_return
                })
        
        # Convert to Series
        if len(portfolio_returns) > 0:
            returns_df = pd.DataFrame(portfolio_returns)
            returns_series = returns_df.set_index('date')['return'].sort_index()
        else:
            returns_series = pd.Series(dtype=float)
        
        return returns_series
    
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
                                     T0_date: Optional[str] = None) -> pd.DataFrame:
        """
        Calculate realized volatility for the portfolio.
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with portfolio data
        T0_date : str, optional
            Start date for the index (format: 'YYYY-MM-DD')
            If None, uses the date after N observations
        
        Returns:
        --------
        pd.DataFrame
            DataFrame with columns: date, short_term_vol, long_term_vol, realized_vol
        """
        # Determine which returns to use based on configuration
        if self.use_log_returns:
            # Case 1: Log returns with three sub-cases
            if self.use_individual_log_returns:
                # Sub-case 3: Weighted individual log returns
                returns = self.calculate_weighted_individual_log_returns(df, lag=self.n)
            elif self.use_normalized_price:
                # Sub-case 2: Normalized weighted price method
                ordinary_returns = self.calculate_normalized_price_returns(df, lag=self.n)
                # Convert to log returns
                returns = np.log(1 + ordinary_returns)
            else:
                # Sub-case 1: Simple log returns using fee_price
                portfolio_values = self.calculate_portfolio_value(df)
                returns = self.calculate_log_returns(portfolio_values, lag=self.n)
        else:
            # Case 2: Weighted returns (not log)
            returns = self.calculate_weighted_portfolio_returns(df, lag=self.n)
        
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
                               target_volatility: float = 0.055,  # Default 5.5%
                               max_leverage: float = 1.0,  # Default 100%
                               lag_days: int = 2,
                               T0_date: Optional[str] = None) -> pd.DataFrame:
        """
        Calculate realized volatility and leveraged weights.
        
        Leveraged weight on date t = min(max_leverage, target_volatility / realized_vol_{t-lag_days})
        where lag_days refers to trading days (not calendar days) in the 'date' column.
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with portfolio data
        target_volatility : float
            Target volatility level (e.g., 0.055 for 5.5%)
        max_leverage : float
            Maximum allowed leverage/weight (e.g., 1.0 for 100%)
        lag_days : int
            Number of trading days lag for volatility (default 2 means use vol from t-2)
        T0_date : str, optional
            Start date for the index
        
        Returns:
        --------
        pd.DataFrame
            DataFrame with columns: date, short_term_vol, long_term_vol, realized_vol, 
            leveraged_weight
        """
        # Calculate realized volatility
        vol_df = self.calculate_realized_volatility(df, T0_date)
        
        # Shift realized volatility by lag_days to get vol_{t-lag_days}
        # This gives us the volatility from lag_days trading days ago
        vol_df['lagged_realized_vol'] = vol_df['realized_vol'].shift(lag_days)
        
        # Calculate leveraged weight for date t using vol from t-lag_days
        # leveraged_weight_t = min(max_leverage, target_volatility / realized_vol_{t-lag_days})
        vol_df['leveraged_weight'] = target_volatility / vol_df['lagged_realized_vol']
        vol_df['leveraged_weight'] = vol_df['leveraged_weight'].clip(upper=max_leverage)
        
        # Fill initial NaN values (first lag_days rows) with max_leverage
        vol_df['leveraged_weight'] = vol_df['leveraged_weight'].fillna(max_leverage)
        
        # Add informational columns
        vol_df['target_vol'] = target_volatility
        vol_df['max_leverage'] = max_leverage
        
        # Drop the temporary lagged column if you want cleaner output
        vol_df = vol_df.drop(columns=['lagged_realized_vol'])
        
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

# Four main use cases when use_log_returns=True:

# Case 1: Log returns with simple fee_price
calc_log_simple = RealizedVolatilityCalculator(
    lambda_s=0.94,
    lambda_l=0.97,
    n=1,
    N=60,
    use_log_returns=True,
    use_normalized_price=False,
    use_individual_log_returns=False
)
# Return = log(fee_price_t / fee_price_{t-1})

# Case 2: Log returns with normalized weighted prices (holding weights constant)
calc_log_normalized = RealizedVolatilityCalculator(
    lambda_s=0.94,
    lambda_l=0.97,
    n=1,
    N=60,
    use_log_returns=True,
    use_normalized_price=True,
    use_individual_log_returns=False
)
# Return = log(1 + ordinary_return) where ordinary_return uses constant weights

# Case 3: Weighted individual log returns (NEW)
calc_log_individual = RealizedVolatilityCalculator(
    lambda_s=0.94,
    lambda_l=0.97,
    n=1,
    N=60,
    use_log_returns=True,
    use_normalized_price=False,  # Ignored when use_individual_log_returns=True
    use_individual_log_returns=True
)
# Return = Σ(weight_{t-1} × log(price_t/price_{t-1})) for each non-cash asset

# Case 4: Weighted returns (not log)
calc_weighted = RealizedVolatilityCalculator(
    lambda_s=0.94,
    lambda_l=0.97,
    n=1,
    N=60,
    use_log_returns=False,
    use_normalized_price=False,  # Ignored when use_log_returns=False
    use_individual_log_returns=False  # Ignored when use_log_returns=False
)
# Return = Σ(weight_{t-1} × (price_t - price_{t-1})/price_{t-1})

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
# sample_results = calc_log_individual.calculate_realized_volatility(sample_df)
# print("Sample Results with Individual Log Returns:")
# print(sample_results.describe())
