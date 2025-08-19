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
