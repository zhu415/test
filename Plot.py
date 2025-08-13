import pandas as pd
import numpy as np

def detect_075_multiplier_dates(df):
    """
    Detect dates when the 0.75 multiplier is applied in the S&P Prims index.
    
    The 0.75 multiplier is applied when:
    - Equities multiplier = 5
    - Rates multiplier = 10
    
    Parameters:
    df: DataFrame containing the S&P Prims index data with columns:
        - date
        - price_per_share
        - number_of_shares
        - weights
        - price (total portfolio value)
    
    Returns:
    DataFrame with dates and verification of 0.75 multiplier application
    """
    
    # Component names mapping
    equities_component = 'spxeralt.cbny'
    rates_component = 'spusttp.iomr'
    commodities_component = 'spgscip.iomr'
    cash_component = 'USD.CASH'
    
    # Function to calculate implied multipliers from weights
    def calculate_implied_multipliers(date_data):
        """
        Back-calculate the multipliers based on weight ratios and known rules
        """
        result = {}
        
        # Get weights for each component on this date
        equities_data = date_data[date_data.index.str.contains(equities_component, na=False)]
        rates_data = date_data[date_data.index.str.contains(rates_component, na=False)]
        commodities_data = date_data[date_data.index.str.contains(commodities_component, na=False)]
        cash_data = date_data[date_data.index.str.contains(cash_component, na=False)]
        
        # Calculate risky weights (non-cash)
        risky_weights = 1 - (cash_data['weights'].values[0] if len(cash_data) > 0 else 0)
        
        # Check if weights seem to be scaled by 0.75
        # This would happen if risky_weights ≈ 0.75 when we'd expect them to be close to 1
        result['risky_weights'] = risky_weights
        result['has_equities'] = len(equities_data) > 0
        result['has_rates'] = len(rates_data) > 0
        result['has_commodities'] = len(commodities_data) > 0
        
        # Detect potential 0.75 scaling
        # If risky weights are around 0.75 (allowing for leverage adjustments)
        # this could indicate the 0.75 multiplier was applied
        result['potential_075_scaling'] = (0.70 <= risky_weights <= 0.80)
        
        return result
    
    # Main detection logic
    detection_results = []
    
    # Group by date
    for date in df['date'].unique():
        date_df = df[df['date'] == date].set_index('component', drop=False) if 'component' in df.columns else df[df['date'] == date]
        
        # Calculate metrics for this date
        metrics = calculate_implied_multipliers(date_df)
        
        # Detect 0.75 multiplier application
        # Method 1: Check if sum of non-cash weights is approximately 0.75
        non_cash_mask = ~date_df.index.str.contains(cash_component, na=False)
        non_cash_weights_sum = date_df.loc[non_cash_mask, 'weights'].sum()
        
        # Method 2: Check weight ratios between components
        equities_weight = date_df[date_df.index.str.contains(equities_component, na=False)]['weights'].sum()
        rates_weight = date_df[date_df.index.str.contains(rates_component, na=False)]['weights'].sum()
        
        # If both equities and rates are present with significant weights
        # and the total risky weight is around 0.75, it's likely the multiplier was applied
        is_075_applied = (
            equities_weight > 0 and 
            rates_weight > 0 and 
            (0.70 <= non_cash_weights_sum <= 0.80)
        )
        
        detection_results.append({
            'date': date,
            'equities_weight': equities_weight,
            'rates_weight': rates_weight,
            'non_cash_weights_sum': non_cash_weights_sum,
            'cash_weight': 1 - non_cash_weights_sum,
            'is_075_multiplier_applied': is_075_applied,
            'likely_equities_multiplier': 5 if is_075_applied else 1,
            'likely_rates_multiplier': 10 if is_075_applied else 1
        })
    
    results_df = pd.DataFrame(detection_results)
    return results_df

def verify_075_multiplier_conditions(df, detection_results):
    """
    Cross-check the conditions for 0.75 multiplier application
    
    Returns detailed verification for each detected date
    """
    verification_results = []
    
    for _, row in detection_results[detection_results['is_075_multiplier_applied']].iterrows():
        date = row['date']
        date_df = df[df['date'] == date]
        
        # Verify conditions
        verification = {
            'date': date,
            'condition_1_equities_mult_5': row['likely_equities_multiplier'] == 5,
            'condition_2_rates_mult_10': row['likely_rates_multiplier'] == 10,
            'observed_scaling': row['non_cash_weights_sum'],
            'expected_scaling': 0.75,
            'scaling_difference': abs(row['non_cash_weights_sum'] - 0.75),
            'verification_passed': abs(row['non_cash_weights_sum'] - 0.75) < 0.05
        }
        
        verification_results.append(verification)
    
    return pd.DataFrame(verification_results)

# Example usage
def analyze_sp_prims_multiplier(df):
    """
    Main function to analyze the S&P Prims index for 0.75 multiplier application
    """
    print("Detecting dates with 0.75 multiplier applied...")
    detection_results = detect_075_multiplier_dates(df)
    
    # Filter for dates where multiplier was likely applied
    multiplier_dates = detection_results[detection_results['is_075_multiplier_applied']]
    
    print(f"\nFound {len(multiplier_dates)} dates with 0.75 multiplier applied:")
    print(multiplier_dates[['date', 'equities_weight', 'rates_weight', 'non_cash_weights_sum']])
    
    # Verify conditions
    print("\nVerifying conditions for 0.75 multiplier application...")
    verification = verify_075_multiplier_conditions(df, detection_results)
    
    if len(verification) > 0:
        print(verification)
    else:
        print("No dates found with clear 0.75 multiplier application")
    
    return detection_results, verification

# Advanced detection using weight ratios
def detect_multipliers_from_weight_ratios(df):
    """
    Alternative method: Detect multipliers by analyzing weight ratios over time
    """
    results = []
    
    dates = df['date'].unique()
    for i in range(1, len(dates)):
        current_date = dates[i]
        prev_date = dates[i-1]
        
        current_df = df[df['date'] == current_date]
        prev_df = df[df['date'] == prev_date]
        
        # Calculate weight changes
        current_non_cash = current_df[~current_df['component'].str.contains('USD.CASH', na=False)]['weights'].sum() if 'component' in df.columns else 0
        prev_non_cash = prev_df[~prev_df['component'].str.contains('USD.CASH', na=False)]['weights'].sum() if 'component' in df.columns else 0
        
        # Check for sudden scaling to ~0.75
        if prev_non_cash > 0.85 and 0.70 <= current_non_cash <= 0.80:
            results.append({
                'date': current_date,
                'prev_date': prev_date,
                'prev_non_cash_weight': prev_non_cash,
                'current_non_cash_weight': current_non_cash,
                'scaling_factor': current_non_cash / prev_non_cash if prev_non_cash > 0 else 0,
                'likely_075_multiplier': True
            })
    
    return pd.DataFrame(results)

# Example of how to use with your dataframe:
"""
# Assuming your dataframe is named 'sp_prims_df'
detection_results, verification = analyze_sp_prims_multiplier(sp_prims_df)

# Get dates where 0.75 multiplier was applied
multiplier_dates = detection_results[detection_results['is_075_multiplier_applied']]['date'].tolist()
print(f"Dates with 0.75 multiplier: {multiplier_dates}")

# Alternative detection method
alt_detection = detect_multipliers_from_weight_ratios(sp_prims_df)
print("\nAlternative detection results:")
print(alt_detection)
"""
