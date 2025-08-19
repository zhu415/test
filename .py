def calculate_with_leverage(self,
                               df: pd.DataFrame,
                               target_volatility: float = 0.055,  # Default 5.5%
                               max_leverage: float = 1.0,  # Default 100%
                               lag_days: int = 2,
                               T0_date: Optional[str] = None) -> pd.DataFrame:
        """
        Calculate realized volatility and weights with leverage cap.
        
        Weight on date t = min(max_leverage, target_volatility / realized_vol_{t-lag_days})
        where lag_days refers to trading days (not calendar days) in the 'date' column.
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with portfolio data
        target_volatility : float
            Target volatility level (e.g., 0.055 for 5.5%)
        max_leverage : float
            Maximum allowed leverage (e.g., 1.0 for 100%)
        lag_days : int
            Number of trading days lag between volatility calculation and weight implementation
        T0_date : str, optional
            Start date for the index
        
        Returns:
        --------
        pd.DataFrame
            DataFrame with columns: date, short_term_vol, long_term_vol, realized_vol, 
            leverage_factor, applied_weight
        """
        # Calculate realized volatility
        vol_df = self.calculate_realized_volatility(df, T0_date)
        
        # Calculate leverage factor (target_vol / realized_vol)
        vol_df['leverage_factor'] = target_volatility / vol_df['realized_vol']
        
        # Apply max leverage cap to get the weight
        # Weight = min(max_leverage, leverage_factor)
        vol_df['weight'] = vol_df['leverage_factor'].clip(upper=max_leverage)
        
        # Apply lag to weight implementation (lag_days trading days, not calendar days)
        # shift(lag_days) shifts by the number of rows, which corresponds to trading days
        vol_df['applied_weight'] = vol_df['weight'].shift(lag_days)
        
        # Fill initial NaN values with max_leverage (typically 100%)
        vol_df['applied_weight'] = vol_df['applied_weight'].fillna(max_leverage)
        
        # Add informational columns
        vol_df['target_vol'] = target_volatility
        vol_df['max_leverage'] = max_leverage
        vol_df['lag_days'] = lag_days
        
        # Calculate the effective volatility (applied_weight * realized_vol)
        vol_df['effective_vol'] = vol_df['applied_weight'] * vol_df['realized_vol']
        
        return vol_df


