"""
Bond Price Calculator from Excel Data

Reads yield curve and hazard rate data from an Excel file,
calculates zero-coupon bond prices, survival probabilities,
and risky bond prices to compare with index values.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Tuple, List


def read_excel_data(file_path: str, sheet_name: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Read the yield curve, hazard rate, and index valuation data from Excel.
    
    Parameters:
        file_path: Path to the Excel file
        sheet_name: Name of the sheet to read
        
    Returns:
        Tuple of (yield_curve_df, hazard_rate_df, index_valuation_df)
    """
    # Read the entire sheet
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
    
    # Row 0 contains merged headers (A1B1, C1D1, E1F1)
    # Row 1 contains column sub-headers (Date, YieldPoint, Date, Yield, Date in XML, IndexValue)
    
    # Extract yield curve data (columns A and B, i.e., 0 and 1)
    yield_curve_df = pd.DataFrame({
        'Date': pd.to_datetime(df.iloc[2:, 0]),
        'YieldPoint': pd.to_numeric(df.iloc[2:, 1], errors='coerce')
    }).dropna().reset_index(drop=True)
    
    # Extract hazard rate data (columns C and D, i.e., 2 and 3)
    hazard_rate_df = pd.DataFrame({
        'Date': pd.to_datetime(df.iloc[2:, 2]),
        'HazardRate': pd.to_numeric(df.iloc[2:, 3], errors='coerce')
    }).dropna(subset=['Date']).reset_index(drop=True)
    
    # Extract index valuation data (columns E and F, i.e., 4 and 5)
    # The date column might contain XML-style dates like <Date>2026-01-27</Date>
    index_dates = df.iloc[2:, 4].astype(str)
    # Parse XML-style dates if present
    index_dates = index_dates.str.extract(r'(\d{4}-\d{2}-\d{2})', expand=False)
    
    index_valuation_df = pd.DataFrame({
        'Date': pd.to_datetime(index_dates),
        'IndexValue': pd.to_numeric(df.iloc[2:, 5], errors='coerce')
    }).dropna().reset_index(drop=True)
    
    return yield_curve_df, hazard_rate_df, index_valuation_df


def calculate_discount_factor(yield_curve_df: pd.DataFrame, 
                               valuation_date: datetime,
                               target_date: datetime) -> float:
    """
    Calculate the discount factor (zero-coupon bond price) from the yield curve.
    Uses linear interpolation for yields.
    
    Parameters:
        yield_curve_df: DataFrame with Date and YieldPoint columns
        valuation_date: The base date for discounting
        target_date: The date to discount back from
        
    Returns:
        Discount factor P(0, T)
    """
    if target_date <= valuation_date:
        return 1.0
    
    # Calculate time to maturity in years (ACT/365)
    T = (target_date - valuation_date).days / 365.0
    
    # Interpolate yield at target date
    yield_curve_df = yield_curve_df.sort_values('Date').reset_index(drop=True)
    
    # Convert dates to numeric for interpolation
    dates_numeric = (yield_curve_df['Date'] - valuation_date).dt.days / 365.0
    yields = yield_curve_df['YieldPoint'].values
    
    # Linear interpolation
    yield_at_T = np.interp(T, dates_numeric, yields)
    
    # Discount factor: P(0,T) = exp(-r * T)
    discount_factor = np.exp(-yield_at_T * T)
    
    return discount_factor


def calculate_survival_probability(hazard_rate_df: pd.DataFrame,
                                    valuation_date: datetime,
                                    target_date: datetime) -> float:
    """
    Calculate the survival probability using piecewise constant hazard rates.
    
    The hazard rate in row i applies from the date in row (i-1) to the date in row i.
    
    Parameters:
        hazard_rate_df: DataFrame with Date and HazardRate columns
        valuation_date: The base date
        target_date: The date to calculate survival probability to
        
    Returns:
        Survival probability Q(0, T)
    """
    if target_date <= valuation_date:
        return 1.0
    
    hazard_rate_df = hazard_rate_df.sort_values('Date').reset_index(drop=True)
    
    # Initialize cumulative hazard
    cumulative_hazard = 0.0
    
    # Start from valuation date
    current_date = valuation_date
    
    for i in range(len(hazard_rate_df)):
        period_end = hazard_rate_df.loc[i, 'Date']
        hazard_rate = hazard_rate_df.loc[i, 'HazardRate']
        
        # Skip if we haven't reached this period yet
        if period_end <= current_date:
            continue
        
        # Skip NaN hazard rates (like the first row which has no rate)
        if pd.isna(hazard_rate):
            current_date = period_end
            continue
        
        # Calculate the overlap with target date
        period_start = current_date
        effective_end = min(period_end, target_date)
        
        if effective_end > period_start:
            # Time in years
            dt = (effective_end - period_start).days / 365.0
            cumulative_hazard += hazard_rate * dt
        
        current_date = period_end
        
        if current_date >= target_date:
            break
    
    # Survival probability: Q(0,T) = exp(-integral of hazard rate)
    survival_prob = np.exp(-cumulative_hazard)
    
    return survival_prob


def calculate_risky_bond_price(yield_curve_df: pd.DataFrame,
                                hazard_rate_df: pd.DataFrame,
                                valuation_date: datetime,
                                target_date: datetime,
                                recovery_rate: float = 0.4) -> float:
    """
    Calculate the risky zero-coupon bond price.
    
    Risky Bond Price = Discount Factor * [Survival Prob + (1 - Survival Prob) * Recovery Rate]
    
    For a defaultable zero-coupon bond:
    V = P(0,T) * [Q(0,T) + (1 - Q(0,T)) * R]
    
    where:
    - P(0,T) is the risk-free discount factor
    - Q(0,T) is the survival probability
    - R is the recovery rate
    
    Parameters:
        yield_curve_df: DataFrame with yield curve data
        hazard_rate_df: DataFrame with hazard rate data
        valuation_date: The base date
        target_date: The maturity date
        recovery_rate: Recovery rate in case of default (default 0.4)
        
    Returns:
        Risky bond price
    """
    discount_factor = calculate_discount_factor(yield_curve_df, valuation_date, target_date)
    survival_prob = calculate_survival_probability(hazard_rate_df, valuation_date, target_date)
    
    # Risky bond price formula
    risky_price = discount_factor * (survival_prob + (1 - survival_prob) * recovery_rate)
    
    return risky_price


def calculate_all_prices(file_path: str, 
                          sheet_name: str,
                          recovery_rate: float = 0.4) -> pd.DataFrame:
    """
    Main function to read data and calculate all bond prices.
    
    Parameters:
        file_path: Path to Excel file
        sheet_name: Name of the sheet
        recovery_rate: Recovery rate (default 0.4)
        
    Returns:
        DataFrame with calculated prices and comparison to index values
    """
    # Read data
    yield_curve_df, hazard_rate_df, index_valuation_df = read_excel_data(file_path, sheet_name)
    
    print("=" * 60)
    print("DATA SUMMARY")
    print("=" * 60)
    print(f"\nYield Curve Data ({len(yield_curve_df)} points):")
    print(yield_curve_df.head(10))
    
    print(f"\nHazard Rate Data ({len(hazard_rate_df)} points):")
    print(hazard_rate_df)
    
    print(f"\nIndex Valuation Data ({len(index_valuation_df)} points):")
    print(index_valuation_df.head(10))
    
    # Use the first date as valuation date
    valuation_date = yield_curve_df['Date'].min()
    print(f"\nValuation Date: {valuation_date.strftime('%Y-%m-%d')}")
    print(f"Recovery Rate: {recovery_rate}")
    
    # Calculate prices for each date in the index valuation
    results = []
    
    for _, row in index_valuation_df.iterrows():
        target_date = row['Date']
        index_value = row['IndexValue']
        
        discount_factor = calculate_discount_factor(yield_curve_df, valuation_date, target_date)
        survival_prob = calculate_survival_probability(hazard_rate_df, valuation_date, target_date)
        calculated_price = calculate_risky_bond_price(
            yield_curve_df, hazard_rate_df, valuation_date, target_date, recovery_rate
        )
        
        # Calculate difference
        diff = calculated_price - index_value
        diff_pct = (diff / index_value * 100) if index_value != 0 else 0
        
        results.append({
            'Date': target_date,
            'DiscountFactor': discount_factor,
            'SurvivalProb': survival_prob,
            'CalculatedPrice': calculated_price,
            'IndexValue': index_value,
            'Difference': diff,
            'DiffPercent': diff_pct
        })
    
    results_df = pd.DataFrame(results)
    
    print("\n" + "=" * 60)
    print("CALCULATION RESULTS")
    print("=" * 60)
    print(results_df.to_string(index=False))
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    print(f"Mean Absolute Difference: {results_df['Difference'].abs().mean():.12f}")
    print(f"Max Absolute Difference: {results_df['Difference'].abs().max():.12f}")
    print(f"Mean Percentage Difference: {results_df['DiffPercent'].abs().mean():.6f}%")
    
    return results_df


# Example usage
if __name__ == "__main__":
    import sys
    
    # Default values - modify these or pass as arguments
    file_path = "input.xlsx"  # Change to your file path
    sheet_name = "Sheet1"      # Change to your sheet name
    recovery_rate = 0.4
    
    # Parse command line arguments if provided
    if len(sys.argv) >= 2:
        file_path = sys.argv[1]
    if len(sys.argv) >= 3:
        sheet_name = sys.argv[2]
    if len(sys.argv) >= 4:
        recovery_rate = float(sys.argv[3])
    
    print(f"Reading from: {file_path}")
    print(f"Sheet: {sheet_name}")
    print(f"Recovery Rate: {recovery_rate}")
    print()
    
    try:
        results = calculate_all_prices(file_path, sheet_name, recovery_rate)
        
        # Optionally save results
        output_path = "bond_price_results.xlsx"
        results.to_excel(output_path, index=False)
        print(f"\nResults saved to: {output_path}")
        
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        print("\nUsage: python bond_price_calculator.py <file_path> <sheet_name> [recovery_rate]")
    except Exception as e:
        print(f"Error: {e}")
        raise
