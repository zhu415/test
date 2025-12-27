import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

def visualize_valuation_results(df, output_path=None, figsize=(15, 12)):
    """
    Visualize valuation results with three subplots for different DateToMatch types.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame from process_directory with columns: Index, DateToMatch_Type, Date, Value
    output_path : str, optional
        Path to save the figure
    figsize : tuple, optional
        Figure size (width, height)
    """
    
    # Convert Date column to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Get unique indices and DateToMatch types
    indices = df['Index'].unique()
    date_to_match_types = ['BuildDate', 'ExpiryDate', 'Empty']
    
    if len(indices) != 2:
        print(f"WARNING: Expected 2 indices, found {len(indices)}: {indices}")
        print("Visualization is designed for exactly 2 indices")
    
    index1 = indices[0]
    index2 = indices[1] if len(indices) > 1 else indices[0]
    
    # Calculate global y-axis ranges for consistency across all subplots
    values1 = df[df['Index'] == index1]['Value']
    values2 = df[df['Index'] == index2]['Value']
    
    # Add some padding (5%) to the ranges
    padding = 0.05
    y1_min = values1.min() * (1 - padding) if values1.min() > 0 else values1.min() * (1 + padding)
    y1_max = values1.max() * (1 + padding) if values1.max() > 0 else values1.max() * (1 - padding)
    y2_min = values2.min() * (1 - padding) if values2.min() > 0 else values2.min() * (1 + padding)
    y2_max = values2.max() * (1 + padding) if values2.max() > 0 else values2.max() * (1 - padding)
    
    # Get the overall date range
    all_dates = df['Date'].unique()
    start_date = df['Date'].min()
    end_date = df['Date'].max()
    
    # Define colors for the two indices
    color1 = 'blue'
    color2 = 'red'
    
    # Create figure with 3 subplots
    fig, axes = plt.subplots(3, 1, figsize=figsize)
    fig.suptitle('Index Valuation Results Comparison', fontsize=16, fontweight='bold')
    
    for idx, dtm_type in enumerate(date_to_match_types):
        ax = axes[idx]
        
        # Filter data for this DateToMatch type
        df_dtm = df[df['DateToMatch_Type'] == dtm_type]
        
        # Get data for each index
        df1 = df_dtm[df_dtm['Index'] == index1].sort_values('Date')
        df2 = df_dtm[df_dtm['Index'] == index2].sort_values('Date')
        
        # Create twin axis
        ax2 = ax.twinx()
        
        # Plot first index on left y-axis
        if not df1.empty:
            line1 = ax.plot(df1['Date'], df1['Value'], 
                           color=color1, linewidth=2, label=index1, marker='o', markersize=3)
        
        # Plot second index on right y-axis
        if not df2.empty:
            line2 = ax2.plot(df2['Date'], df2['Value'], 
                            color=color2, linewidth=2, label=index2, marker='s', markersize=3)
        
        # Set consistent y-axis ranges
        ax.set_ylim(y1_min, y1_max)
        ax2.set_ylim(y2_min, y2_max)
        
        # Set y-axis labels with matching colors
        ax.set_ylabel(index1, fontsize=12, fontweight='bold', color=color1)
        ax2.set_ylabel(index2, fontsize=12, fontweight='bold', color=color2)
        
        # Color the y-axis tick labels to match
        ax.tick_params(axis='y', labelcolor=color1)
        ax2.tick_params(axis='y', labelcolor=color2)
        
        # Set x-axis label
        ax.set_xlabel('Date', fontsize=11)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
        # Set x-axis limits
        ax.set_xlim(start_date, end_date)
        
        # Customize x-axis ticks to show start and end dates explicitly
        # Set major locator for intermediate dates
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # Get current ticks
        current_ticks = ax.get_xticks()
        
        # Add start and end dates to ticks
        date_range = (end_date - start_date).days
        if date_range > 30:
            # For longer periods, show fewer intermediate ticks
            ax.xaxis.set_major_locator(mdates.MonthLocator())
        elif date_range > 7:
            # For medium periods, show weekly ticks
            ax.xaxis.set_major_locator(mdates.WeekdayLocator())
        
        # Ensure start and end dates are shown
        tick_dates = list(ax.get_xticks())
        start_date_num = mdates.date2num(start_date)
        end_date_num = mdates.date2num(end_date)
        
        if start_date_num not in tick_dates:
            tick_dates.insert(0, start_date_num)
        if end_date_num not in tick_dates:
            tick_dates.append(end_date_num)
        
        ax.set_xticks(tick_dates)
        
        # Rotate x-axis labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Set subplot title
        ax.set_title(f'DateToMatch: {dtm_type}', fontsize=13, fontweight='bold', pad=10)
        
        # Add grid
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Create combined legend
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='best', framealpha=0.9)
    
    # Adjust layout to prevent overlap
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    
    # Save figure if output path is provided
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to: {output_path}")
    
    plt.show()
    
    return fig


def create_summary_statistics_table(df, output_path=None):
    """
    Create a summary statistics table for the valuation results.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame from process_directory
    output_path : str, optional
        Path to save the summary table CSV
        
    Returns:
    --------
    pd.DataFrame
        Summary statistics table
    """
    
    summary = df.groupby(['Index', 'DateToMatch_Type']).agg({
        'Value': ['count', 'mean', 'std', 'min', 'max']
    }).round(4)
    
    # Flatten column names
    summary.columns = ['_'.join(col).strip() for col in summary.columns.values]
    summary = summary.reset_index()
    
    if output_path:
        summary.to_csv(output_path, index=False)
        print(f"Summary statistics saved to: {output_path}")
    
    print("\nSummary Statistics:")
    print(summary)
    
    return summary


# Complete workflow example
if __name__ == "__main__":
    # Step 1: Process XML files and create DataFrame
    df = save_results_to_csv(
        directory="./output",
        csv_output_path="./valuation_results.csv"
    )
    
    if len(df) > 0:
        # Step 2: Create pivot table
        pivot = create_pivot_table(df, output_path="./valuation_results_pivot.csv")
        print("\nPivot Table Preview:")
        print(pivot.head())
        
        # Step 3: Create summary statistics
        summary = create_summary_statistics_table(df, output_path="./summary_statistics.csv")
        
        # Step 4: Visualize results
        fig = visualize_valuation_results(df, output_path="./valuation_comparison.png")
```

**Key features of the visualization:**

1. **Three subplots** - one for each DateToMatch type (BuildDate, ExpiryDate, Empty)

2. **Dual y-axes** - left axis for first index (blue), right axis for second index (red)

3. **Consistent y-axis ranges** across all three subplots for comparability

4. **X-axis formatting**:
   - Shows dates from BuildDate to ExpiryDate
   - Explicitly displays start and end dates
   - Automatic intelligent tick spacing based on date range
   - Rotated labels for better readability

5. **Color-coded**:
   - Lines match their respective y-axis labels
   - Blue for first index (left y-axis)
   - Red for second index (right y-axis)

6. **Legends** on each subplot showing both indices

7. **Grid** for easier value reading

8. **High-resolution output** (300 DPI) when saved

**The output will look like:**
```
┌─────────────────────────────────────────────┐
│   Index Valuation Results Comparison        │
├─────────────────────────────────────────────┤
│  DateToMatch: BuildDate                     │
│  [Blue line for Index1, Red line for Index2]│
├─────────────────────────────────────────────┤
│  DateToMatch: ExpiryDate                    │
│  [Blue line for Index1, Red line for Index2]│
├─────────────────────────────────────────────┤
│  DateToMatch: Empty                         │
│  [Blue line for Index1, Red line for Index2]│
└─────────────────────────────────────────────┘
