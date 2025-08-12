import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import pandas as pd

# Create figure
fig, ax = plt.subplots(figsize=(12, 8))

# Plot original weight
ax.plot(relativeChange_df['date'], relativeChange_df['sum_weight_excl_USD_CASH'], 
        'b-', linewidth=1, label='Original Weight')

# Plot relative change ratio
ax.plot(relativeChange_df['date'], relativeChange_df['ratio'], 
        'g-', linewidth=1, label='Relative Change Ratio')

# Get highlight data
highlight_data = relativeChange_df[relativeChange_df['date'].isin(dates_list)]

# For weight: highlight at the current date
ax.scatter(highlight_data['date'], highlight_data['sum_weight_excl_USD_CASH'], 
          color='red', s=50, zorder=5, marker='o', label='Large Change Dates (Weight)')

# For ratio: adjust highlighting based on whether ratio is positive or negative
ratio_highlight_dates = []
ratio_highlight_values = []

for _, row in highlight_data.iterrows():
    current_date = row['date']
    ratio_value = row['ratio']
    
    if ratio_value > 0:
        # For positive ratio, highlight the previous date where the spike occurs
        current_idx = relativeChange_df[relativeChange_df['date'] == current_date].index[0]
        if current_idx > 0:
            prev_date = relativeChange_df.iloc[current_idx - 1]['date']
            ratio_highlight_dates.append(prev_date)
            ratio_highlight_values.append(ratio_value)
    else:
        # For negative ratio, highlight at the current date
        ratio_highlight_dates.append(current_date)
        ratio_highlight_values.append(ratio_value)

# Plot the ratio highlights
ax.scatter(ratio_highlight_dates, ratio_highlight_values, 
          color='red', s=50, zorder=5, marker='^', label='Large Change Dates (Ratio)')

# Add horizontal reference lines for the targets
ax.axhline(y=targets[0], color='orange', linestyle='--', alpha=0.7, label=f'Target: {targets[0]:.3f}')
ax.axhline(y=targets[1], color='orange', linestyle='--', alpha=0.7, label=f'Target: {targets[1]:.3f}')

# Labels and formatting
ax.set_ylabel('Value')
ax.set_xlabel('Date')
ax.set_title('Relative changes in sum of weights (excl CASH) overtime')
ax.legend()
ax.grid(True, alpha=0.3)

# Format x-axis dates
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

plt.tight_layout()
plt.show()
