“””
Bond Price Calculator from Excel Data

Reads yield curve and hazard rate data from an Excel file,
calculates risky bond prices using interpolated hazard rates and yields.

Formula:
V = [e^(-lambda*T) + (1 - e^(-lambda*T)) * R] * e^(-r*T)

Where:
- lambda = interpolated hazard rate at time T
- r = interpolated yield at time T
- R = recovery rate (default 0.4)
- T = time to maturity in years
“””

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Tuple

def read_excel_data(file_path: str, sheet_name: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
“””
Read the yield curve, hazard rate, and index valuation data from Excel.

```
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
```

def interpolate_rate(rate_df: pd.DataFrame,
rate_column: str,
valuation_date: datetime,
target_date: datetime) -> float:
“””
Interpolate a rate (yield or hazard) at the target date.

```
Parameters:
    rate_df: DataFrame with Date and rate columns
    rate_column: Name of the column containing the rate values
    valuation_date: The base date
    target_date: The date to interpolate at
    
Returns:
    Interpolated rate at target_date
"""
# Filter out NaN rates for interpolation
valid_df = rate_df.dropna(subset=[rate_column]).copy()
valid_df = valid_df.sort_values('Date').reset_index(drop=True)

if len(valid_df) == 0:
    return 0.0

# Convert dates to numeric (days from valuation date)
dates_numeric = (valid_df['Date'] - valuation_date).dt.days.values
rates = valid_df[rate_column].values

# Target date in numeric
T_days = (target_date - valuation_date).days

# Linear interpolation (extrapolates if outside range)
interpolated_rate = np.interp(T_days, dates_numeric, rates)

return interpolated_rate
```

def calculate_bond_price(yield_curve_df: pd.DataFrame,
hazard_rate_df: pd.DataFrame,
valuation_date: datetime,
target_date: datetime,
recovery_rate: float = 0.4) -> dict:
“””
Calculate the risky bond price using interpolated rates.

```
Formula: V = [e^(-lambda*T) + (1 - e^(-lambda*T)) * R] * e^(-r*T)

Parameters:
    yield_curve_df: DataFrame with yield curve data
    hazard_rate_df: DataFrame with hazard rate data
    valuation_date: The base date
    target_date: The maturity date
    recovery_rate: Recovery rate (default 0.4)
    
Returns:
    Dictionary with all intermediate values and final price
"""
if target_date <= valuation_date:
    return {
        'T': 0.0,
        'r': 0.0,
        'lambda': 0.0,
        'discount_factor': 1.0,
        'survival_prob': 1.0,
        'bond_price': 1.0
    }

# Time to maturity in years (ACT/365)
T = (target_date - valuation_date).days / 365.0

# Interpolate yield at target date
r = interpolate_rate(yield_curve_df, 'YieldPoint', valuation_date, target_date)

# Interpolate hazard rate at target date
lambda_rate = interpolate_rate(hazard_rate_df, 'HazardRate', valuation_date, target_date)

# Discount factor: P(T) = e^(-r*T)
discount_factor = np.exp(-r * T)

# Survival probability: Q(T) = e^(-lambda*T)
survival_prob = np.exp(-lambda_rate * T)

# Risky bond price: V = [Q(T) + (1 - Q(T)) * R] * P(T)
bond_price = (survival_prob + (1 - survival_prob) * recovery_rate) * discount_factor

return {
    'T': T,
    'r': r,
    'lambda': lambda_rate,
    'discount_factor': discount_factor,
    'survival_prob': survival_prob,
    'bond_price': bond_price
}
```

def calculate_all_prices(file_path: str,
sheet_name: str,
recovery_rate: float = 0.4) -> pd.DataFrame:
“””
Main function to read data and calculate all bond prices.

```
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
valuation_date = yield_curve_df['Date'].iloc[0]
print(f"\nValuation Date: {valuation_date.strftime('%Y-%m-%d')}")
print(f"Recovery Rate: {recovery_rate}")

print("\n" + "=" * 60)
print("FORMULA USED")
print("=" * 60)
print("V = [e^(-λ*T) + (1 - e^(-λ*T)) * R] * e^(-r*T)")
print("Where:")
print("  λ = interpolated hazard rate at time T")
print("  r = interpolated yield at time T")
print("  R = recovery rate")
print("  T = time to maturity in years (ACT/365)")

# Calculate prices for each date in the index valuation
results = []

for i in range(len(index_valuation_df)):
    target_date = index_valuation_df.loc[i, 'Date']
    index_value = index_valuation_df.loc[i, 'IndexValue']
    
    # Skip if any value is NaN
    if pd.isna(target_date) or pd.isna(index_value):
        continue
    
    calc = calculate_bond_price(
        yield_curve_df, hazard_rate_df, 
        valuation_date, target_date, 
        recovery_rate
    )
    
    # Calculate difference
    diff = calc['bond_price'] - index_value
    diff_pct = (diff / index_value * 100) if index_value != 0 else 0
    
    results.append({
        'Date': target_date,
        'T_years': calc['T'],
        'Yield_r': calc['r'],
        'Hazard_lambda': calc['lambda'],
        'DiscountFactor': calc['discount_factor'],
        'SurvivalProb': calc['survival_prob'],
        'CalculatedPrice': calc['bond_price'],
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
```

# =============================================================================

# FOR JUPYTER NOTEBOOK USAGE - Copy everything above and run like this:

# =============================================================================

# 

# file_path = r”C:\path\to\your\file.xlsx”

# sheet_name = “df_goldman”

# recovery_rate = 0.4

# 

# results = calculate_all_prices(file_path, sheet_name, recovery_rate)

# 

# =============================================================================

if **name** == “**main**”:
import sys

```
if len(sys.argv) < 3:
    print("Usage: python bond_price_calculator.py <file_path> <sheet_name> [recovery_rate]")
    print("\nFor Jupyter notebook, use:")
    print('  results = calculate_all_prices("your_file.xlsx", "sheet_name", 0.4)')
    sys.exit(1)

file_path = sys.argv[1]
sheet_name = sys.argv[2]
recovery_rate = float(sys.argv[3]) if len(sys.argv) >= 4 else 0.4

results = calculate_all_prices(file_path, sheet_name, recovery_rate)

# Save results
output_path = "bond_price_results.xlsx"
results.to_excel(output_path, index=False)
print(f"\nResults saved to: {output_path}")
```
