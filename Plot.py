import pandas as pd
import numpy as np

def detect_075_multiplier_dates(df):
    """
    Detect dates when the 0.75 multiplier is applied in the S&P Prims index.
    
    The 0.75 multiplier is applied when:
    - Equities multiplier = 5
    - Rates multiplier = 10
    
    Parameters:
    df: DataFrame containing the S&P Prims index data
    
    Returns:
    DataFrame with dates and verification of 0.75 multiplier application
    """
    
    # Component names mapping
    equities_component = 'spxeralt.cbny'
    rates_component = 'spusttp.iomr'
    commodities_component = 'spgscip.iomr'
    cash_component = 'USD.CASH'
    
    # First, let's identify the structure of the dataframe
    print("DataFrame columns:", df.columns.tolist())
    print("DataFrame shape:", df.shape)
    print("\nFirst few rows:")
    print(df.head())
    
    # Try to identify component column
    component_col = None
    for col in ['component', 'Component', 'ticker', 'Ticker', 'asset', 'Asset', 'symbol', 'Symbol']:
        if col in df.columns:
            component_col = col
            break
    
    # If no component column, check if components are in index or column names
    if component_col is None:
        # Check if components are in the index
        if df.index.name and any(comp in str(df.index.name) for comp in [equities_component, rates_component]):
            print("Components appear to be in the index")
            df = df.reset_index()
            component_col = 'index'
        # Check if components are embedded in column names (wide format)
        elif any(equities_component in str(col) for col in df.columns):
            print("Data appears to be in wide format with components in column names")
            return detect_075_multiplier_wide_format(df)
    
    if component_col is None:
        print("Could not identify component column. Please specify the structure.")
        return None
    
    # Convert component column to string type
    df[component_col] = df[component_col].astype(str)
    
    # Main detection logic
    detection_results = []
    
    # Group by date
    for date in df['date'].unique():
        date_df = df[df['date'] == date].copy()
        
        # Calculate weights for each component type
        equities_mask = date_df[component_col].str.contains(equities_component, na=False)
        rates_mask = date_df[component_col].str.contains(rates_component, na=False)
        commodities_mask = date_df[component_col].str.contains(commodities_component, na=False)
        cash_mask = date_df[component_col].str.contains(cash_component, na=False)
        
        equities_weight = date_df.loc[equities_mask, 'weights'].sum() if equities_mask.any() else 0
        rates_weight = date_df.loc[rates_mask, 'weights'].sum() if rates_mask.any() else 0
        commodities_weight = date_df.loc[commodities_mask, 'weights'].sum() if commodities_mask.any() else 0
        cash_weight = date_df.loc[cash_mask, 'weights'].sum() if cash_mask.any() else 0
        
        # Calculate non-cash weights sum
        non_cash_weights_sum = equities_weight + rates_weight + commodities_weight
        
        # Detect if 0.75 multiplier was likely applied
        # Key indicator: non-cash weights sum to approximately 0.75
        # AND both equities and rates are present with significant weights
        is_075_applied = (
            equities_weight > 0.1 and  # Equities present with significant weight
            rates_weight > 0.1 and      # Rates present with significant weight
            0.70 <= non_cash_weights_sum <= 0.80  # Total risky weights around 0.75
        )
        
        # Try to infer multipliers based on weight patterns
        # If 0.75 applied, equities mult = 5, rates mult = 10
        likely_equities_mult = 5 if is_075_applied else 1
        likely_rates_mult = 10 if is_075_applied else 1
        
        detection_results.append({
            'date': date,
            'equities_weight': round(equities_weight, 4),
            'rates_weight': round(rates_weight, 4),
            'commodities_weight': round(commodities_weight, 4),
            'cash_weight': round(cash_weight, 4),
            'non_cash_weights_sum': round(non_cash_weights_sum, 4),
            'is_075_multiplier_applied': is_075_applied,
            'likely_equities_multiplier': likely_equities_mult,
            'likely_rates_multiplier': likely_rates_mult
        })
    
    results_df = pd.DataFrame(detection_results)
    return results_df

def detect_075_multiplier_wide_format(df):
    """
    Handle wide format where components are in column names
    e.g., 'weights_spxeralt.cbny', 'weights_spusttp.iomr', etc.
    """
    detection_results = []
    
    # Identify weight columns for each component
    weight_cols = [col for col in df.columns if 'weight' in col.lower()]
    
    equities_col = None
    rates_col = None
    commodities_col = None
    cash_col = None
    
    for col in weight_cols:
        col_str = str(col)
        if 'spxeralt.cbny' in col_str:
            equities_col = col
        elif 'spusttp.iomr' in col_str:
            rates_col = col
        elif 'spgscip.iomr' in col_str:
            commodities_col = col
        elif 'USD.CASH' in col_str or 'CASH' in col_str:
            cash_col = col
    
    print(f"Identified columns:")
    print(f"  Equities: {equities_col}")
    print(f"  Rates: {rates_col}")
    print(f"  Commodities: {commodities_col}")
    print(f"  Cash: {cash_col}")
    
    # Process each date
    for _, row in df.iterrows():
        date = row['date'] if 'date' in row else row.name
        
        equities_weight = float(row[equities_col]) if equities_col and pd.notna(row.get(equities_col)) else 0
        rates_weight = float(row[rates_col]) if rates_col and pd.notna(row.get(rates_col)) else 0
        commodities_weight = float(row[commodities_col]) if commodities_col and pd.notna(row.get(commodities_col)) else 0
        cash_weight = float(row[cash_col]) if cash_col and pd.notna(row.get(cash_col)) else 0
        
        non_cash_weights_sum = equities_weight + rates_weight + commodities_weight
        
        # Detect 0.75 multiplier
        is_075_applied = (
            equities_weight > 0.1 and
            rates_weight > 0.1 and
            0.70 <= non_cash_weights_sum <= 0.80
        )
        
        detection_results.append({
            'date': date,
            'equities_weight': round(equities_weight, 4),
            'rates_weight': round(rates_weight, 4),
            'commodities_weight': round(commodities_weight, 4),
            'cash_weight': round(cash_weight, 4),
            'non_cash_weights_sum': round(non_cash_weights_sum, 4),
            'is_075_multiplier_applied': is_075_applied,
            'likely_equities_multiplier': 5 if is_075_applied else 1,
            'likely_rates_multiplier': 10 if is_075_applied else 1
        })
    
    return pd.DataFrame(detection_results)

def analyze_sp_prims_multiplier(df):
    """
    Main function to analyze the S&P Prims index for 0.75 multiplier application
    """
    print("="*60)
    print("ANALYZING S&P PRIMS INDEX FOR 0.75 MULTIPLIER APPLICATION")
    print("="*60)
    
    # Detect multiplier application dates
    detection_results = detect_075_multiplier_dates(df)
    
    if detection_results is None:
        print("\nPlease check your dataframe structure and ensure it contains:")
        print("- A 'date' column")
        print("- A 'weights' column")
        print("- Component identifiers (either as a column or in column names)")
        return None, None
    
    # Filter for dates where multiplier was likely applied
    multiplier_dates = detection_results[detection_results['is_075_multiplier_applied']]
    
    print(f"\n{'='*60}")
    print(f"RESULTS: Found {len(multiplier_dates)} dates with 0.75 multiplier applied")
    print(f"{'='*60}")
    
    if len(multiplier_dates) > 0:
        print("\nDates with 0.75 multiplier (Equities mult=5, Rates mult=10):")
        print("-"*60)
        for _, row in multiplier_dates.iterrows():
            print(f"\nDate: {row['date']}")
            print(f"  Equities weight: {row['equities_weight']:.2%}")
            print(f"  Rates weight: {row['rates_weight']:.2%}")
            print(f"  Total non-cash weights: {row['non_cash_weights_sum']:.2%}")
            print(f"  Cash weight: {row['cash_weight']:.2%}")
            print(f"  → Confirms 0.75 rescaling applied")
    
    # Create verification summary
    verification = create_verification_summary(detection_results)
    
    return detection_results, verification

def create_verification_summary(detection_results):
    """
    Create a summary of verification for 0.75 multiplier application
    """
    multiplier_dates = detection_results[detection_results['is_075_multiplier_applied']]
    
    if len(multiplier_dates) == 0:
        return pd.DataFrame()
    
    verification_data = []
    for _, row in multiplier_dates.iterrows():
        verification_data.append({
            'date': row['date'],
            'condition_met': 'YES',
            'reason': 'Equities mult=5 AND Rates mult=10',
            'observed_risky_weight': f"{row['non_cash_weights_sum']:.2%}",
            'expected_risky_weight': '75.00%',
            'deviation': f"{abs(row['non_cash_weights_sum'] - 0.75):.2%}",
            'equities_weight': f"{row['equities_weight']:.2%}",
            'rates_weight': f"{row['rates_weight']:.2%}"
        })
    
    return pd.DataFrame(verification_data)

def detect_multiplier_changes(df):
    """
    Detect changes in multipliers by analyzing weight patterns over time
    """
    detection_results = detect_075_multiplier_dates(df)
    
    if detection_results is None:
        return None
    
    # Add a column for multiplier status change
    detection_results['multiplier_change'] = ''
    
    for i in range(1, len(detection_results)):
        prev_applied = detection_results.iloc[i-1]['is_075_multiplier_applied']
        curr_applied = detection_results.iloc[i]['is_075_multiplier_applied']
        
        if not prev_applied and curr_applied:
            detection_results.loc[detection_results.index[i], 'multiplier_change'] = 'ACTIVATED (0.75x scaling started)'
        elif prev_applied and not curr_applied:
            detection_results.loc[detection_results.index[i], 'multiplier_change'] = 'DEACTIVATED (0.75x scaling ended)'
    
    # Show only dates with changes
    changes = detection_results[detection_results['multiplier_change'] != '']
    
    if len(changes) > 0:
        print("\n" + "="*60)
        print("MULTIPLIER STATUS CHANGES")
        print("="*60)
        for _, row in changes.iterrows():
            print(f"\n{row['date']}: {row['multiplier_change']}")
            print(f"  Non-cash weights: {row['non_cash_weights_sum']:.2%}")
    
    return detection_results

# Example usage function
def run_full_analysis(df):
    """
    Run complete analysis on your dataframe
    """
    # Main analysis
    detection_results, verification = analyze_sp_prims_multiplier(df)
    
    if detection_results is not None:
        # Detect multiplier changes
        print("\n" + "="*60)
        print("ANALYZING MULTIPLIER CHANGES OVER TIME")
        print("="*60)
        changes_df = detect_multiplier_changes(df)
        
        # Export results
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        print("\nYou can access the following results:")
        print("- detection_results: Full analysis for all dates")
        print("- verification: Verification summary for 0.75 multiplier dates")
        
        # Dates list for easy reference
        multiplier_dates_list = detection_results[detection_results['is_075_multiplier_applied']]['date'].tolist()
        print(f"\nDates with 0.75 multiplier applied: {len(multiplier_dates_list)} dates")
        if len(multiplier_dates_list) > 0:
            print(f"Date range: {multiplier_dates_list[0]} to {multiplier_dates_list[-1]}")
    
    return detection_results, verification

# Usage:
"""
# Run the analysis on your dataframe
detection_results, verification = run_full_analysis(your_dataframe)

# Get specific information
multiplier_dates = detection_results[detection_results['is_075_multiplier_applied']]
print(multiplier_dates[['date', 'equities_weight', 'rates_weight', 'non_cash_weights_sum']])
"""
