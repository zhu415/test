import pandas as pd
import numpy as np

# Assuming your dataframe is called 'df' with columns 'date' and 'applied_leverage'
# and your time periods list is defined as:
# time_periods = ['[2022-01-01, 2022-04-01)', '[2022-06-01, 2022-07-15)', ...]

# Ensure date column is datetime
df['date'] = pd.to_datetime(df['date'])

# Create a copy of the original applied_leverage column
df['applied_leverage_rescaled'] = df['applied_leverage'].copy()

# Parse and apply rescaling for each time period
for period in time_periods:
   # Remove brackets and split by comma
   period_clean = period.strip('[]()').strip()
   dates = period_clean.split(',')
   
   # Parse start and end dates
   start_date = pd.to_datetime(dates[0].strip())
   end_date = pd.to_datetime(dates[1].strip())
   
   # Determine inclusivity based on brackets
   left_inclusive = period[0] == '['
   right_inclusive = period[-1] == ']'
   
   # Create mask for dates within the period
   if left_inclusive and not right_inclusive:  # [start, end)
       mask = (df['date'] >= start_date) & (df['date'] < end_date)
   elif left_inclusive and right_inclusive:  # [start, end]
       mask = (df['date'] >= start_date) & (df['date'] <= end_date)
   elif not left_inclusive and right_inclusive:  # (start, end]
       mask = (df['date'] > start_date) & (df['date'] <= end_date)
   else:  # (start, end)
       mask = (df['date'] > start_date) & (df['date'] < end_date)
   
   # Apply rescaling to rows within the period
   df.loc[mask, 'applied_leverage_rescaled'] *= 0.75

# Check the results
print(f"Original applied_leverage sum: {df['applied_leverage'].sum():.2f}")
print(f"Rescaled applied_leverage sum: {df['applied_leverage_rescaled'].sum():.2f}")

# View sample of affected rows (optional)
for period in time_periods[:1]:  # Show first period as example
   period_clean = period.strip('[]()').strip()
   dates = period_clean.split(',')
   start_date = pd.to_datetime(dates[0].strip())
   
   print(f"\nSample rows from period {period}:")
   display(df[df['date'] >= start_date].head(5)[['date', 'applied_leverage', 'applied_leverage_rescaled']])
