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



import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import mplcursors  # For interactive tooltips

def visualize_valuation_results(df, output_path=None, figsize=(15, 12), interactive=True):
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
    interactive : bool, optional
        If True, enable interactive tooltips (works in interactive environments)
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
    start_date = df['Date'].min()
    end_date = df['Date'].max()
    
    # Format dates for display
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Define colors for the two indices
    color1 = 'blue'
    color2 = 'red'
    
    # Create figure with 3 subplots
    fig, axes = plt.subplots(3, 1, figsize=figsize)
    fig.suptitle(f'Index Valuation Results Comparison\nBuildDate: {start_date_str}  |  ExpiryDate: {end_date_str}', 
                 fontsize=16, fontweight='bold')
    
    # Store line objects for interactive tooltips
    all_lines = []
    
    for idx, dtm_type in enumerate(date_to_match_types):
        ax = axes[idx]
        
        # Filter data for this DateToMatch type
        df_dtm = df[df['DateToMatch_Type'] == dtm_type]
        
        # Get data for each index
        df1 = df_dtm[df_dtm['Index'] == index1].sort_values('Date')
        df2 = df_dtm[df_dtm['Index'] == index2].sort_values('Date')
        
        # Create twin axis
        ax2 = ax.twinx()
        
        # Plot first index on left y-axis (thinner line)
        if not df1.empty:
            line1 = ax.plot(df1['Date'], df1['Value'], 
                           color=color1, linewidth=1.2, label=index1, 
                           marker='o', markersize=2, alpha=0.8)
            all_lines.extend(line1)
        
        # Plot second index on right y-axis (thinner line)
        if not df2.empty:
            line2 = ax2.plot(df2['Date'], df2['Value'], 
                            color=color2, linewidth=1.2, label=index2, 
                            marker='s', markersize=2, alpha=0.8)
            all_lines.extend(line2)
        
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
        
        # Set x-axis limits with a bit of padding to avoid label overlap
        date_range = (end_date - start_date).days
        padding_days = max(1, date_range * 0.02)  # 2% padding
        ax.set_xlim(start_date - pd.Timedelta(days=padding_days), 
                    end_date + pd.Timedelta(days=padding_days))
        
        # Customize x-axis ticks to avoid overlap
        if date_range > 60:
            # For longer periods, show monthly ticks
            ax.xaxis.set_major_locator(mdates.MonthLocator())
        elif date_range > 30:
            # For medium-long periods, show bi-weekly ticks
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        elif date_range > 14:
            # For medium periods, show weekly ticks
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        else:
            # For short periods, show every few days
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, date_range // 7)))
        
        # Manually set ticks to include start and end dates
        tick_locs = list(ax.get_xticks())
        start_date_num = mdates.date2num(start_date)
        end_date_num = mdates.date2num(end_date)
        
        # Remove ticks that are too close to start/end dates (within 3% of range)
        threshold = (end_date_num - start_date_num) * 0.03
        tick_locs = [t for t in tick_locs 
                     if abs(t - start_date_num) > threshold and abs(t - end_date_num) > threshold]
        
        # Add start and end dates
        tick_locs = [start_date_num] + tick_locs + [end_date_num]
        tick_locs = sorted(set(tick_locs))
        
        ax.set_xticks(tick_locs)
        
        # Rotate x-axis labels and adjust alignment
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=9)
        
        # Set subplot title
        ax.set_title(f'DateToMatch: {dtm_type}', fontsize=13, fontweight='bold', pad=10)
        
        # Add grid
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        
        # Create combined legend
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='best', framealpha=0.9, fontsize=10)
    
    # Adjust layout to prevent overlap
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # Add interactive tooltips if requested
    if interactive:
        cursor = mplcursors.cursor(all_lines, hover=True)
        
        @cursor.connect("add")
        def on_add(sel):
            # Get the data point
            x, y = sel.target
            # Convert x (date number) back to date
            date = mdates.num2date(x).strftime('%Y-%m-%d')
            # Format the annotation
            sel.annotation.set_text(f'Date: {date}\nValue: {y:.4f}')
            sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)
    
    # Save figure if output path is provided
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to: {output_path}")
    
    plt.show()
    
    return fig


def create_interactive_html_plot(df, output_path='valuation_interactive.html'):
    """
    Create an interactive HTML plot using Plotly that shows values on hover.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame from process_directory
    output_path : str
        Path to save the HTML file
    """
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        print("Plotly not installed. Install with: pip install plotly")
        return None
    
    # Convert Date column to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Get unique indices and DateToMatch types
    indices = df['Index'].unique()
    date_to_match_types = ['BuildDate', 'ExpiryDate', 'Empty']
    
    index1 = indices[0]
    index2 = indices[1] if len(indices) > 1 else indices[0]
    
    # Get date range
    start_date = df['Date'].min()
    end_date = df['Date'].max()
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Calculate global y-axis ranges
    values1 = df[df['Index'] == index1]['Value']
    values2 = df[df['Index'] == index2]['Value']
    
    padding = 0.05
    y1_min = values1.min() * (1 - padding)
    y1_max = values1.max() * (1 + padding)
    y2_min = values2.min() * (1 - padding)
    y2_max = values2.max() * (1 + padding)
    
    # Create subplots
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=[f'DateToMatch: {dtm}' for dtm in date_to_match_types],
        specs=[[{"secondary_y": True}],
               [{"secondary_y": True}],
               [{"secondary_y": True}]],
        vertical_spacing=0.12
    )
    
    # Add traces for each DateToMatch type
    for idx, dtm_type in enumerate(date_to_match_types):
        row = idx + 1
        
        # Filter data
        df_dtm = df[df['DateToMatch_Type'] == dtm_type]
        df1 = df_dtm[df_dtm['Index'] == index1].sort_values('Date')
        df2 = df_dtm[df_dtm['Index'] == index2].sort_values('Date')
        
        # Add trace for index1 (left y-axis)
        if not df1.empty:
            fig.add_trace(
                go.Scatter(
                    x=df1['Date'],
                    y=df1['Value'],
                    name=index1,
                    mode='lines+markers',
                    line=dict(color='blue', width=1.5),
                    marker=dict(size=4),
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                  'Date: %{x|%Y-%m-%d}<br>' +
                                  'Value: %{y:.4f}<br>' +
                                  '<extra></extra>',
                    showlegend=(idx == 0)  # Only show legend for first subplot
                ),
                row=row, col=1, secondary_y=False
            )
        
        # Add trace for index2 (right y-axis)
        if not df2.empty:
            fig.add_trace(
                go.Scatter(
                    x=df2['Date'],
                    y=df2['Value'],
                    name=index2,
                    mode='lines+markers',
                    line=dict(color='red', width=1.5),
                    marker=dict(size=4, symbol='square'),
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                  'Date: %{x|%Y-%m-%d}<br>' +
                                  'Value: %{y:.4f}<br>' +
                                  '<extra></extra>',
                    showlegend=(idx == 0)
                ),
                row=row, col=1, secondary_y=True
            )
        
        # Update y-axes
        fig.update_yaxes(title_text=index1, title_font=dict(color='blue'), 
                        tickfont=dict(color='blue'),
                        range=[y1_min, y1_max],
                        row=row, col=1, secondary_y=False)
        fig.update_yaxes(title_text=index2, title_font=dict(color='red'),
                        tickfont=dict(color='red'),
                        range=[y2_min, y2_max],
                        row=row, col=1, secondary_y=True)
        
        # Update x-axis
        fig.update_xaxes(title_text='Date', row=row, col=1)
    
    # Update layout
    fig.update_layout(
        title=f'Index Valuation Results Comparison<br>' +
              f'<sub>BuildDate: {start_date_str}  |  ExpiryDate: {end_date_str}</sub>',
        height=1000,
        hovermode='closest',
        showlegend=True,
        legend=dict(x=1.15, y=1)
    )
    
    # Save to HTML
    fig.write_html(output_path)
    print(f"Interactive HTML plot saved to: {output_path}")
    
    return fig


# Complete workflow example
if __name__ == "__main__":
    # Install mplcursors if not already installed
    # pip install mplcursors
    # pip install plotly  # Optional, for interactive HTML plots
    
    # Step 1: Process XML files and create DataFrame
    df = save_results_to_csv(
        directory="./output",
        csv_output_path="./valuation_results.csv"
    )
    
    if len(df) > 0:
        # Step 2: Create pivot table
        pivot = create_pivot_table(df, output_path="./valuation_results_pivot.csv")
        
        # Step 3: Create summary statistics
        summary = create_summary_statistics_table(df, output_path="./summary_statistics.csv")
        
        # Step 4: Visualize results (matplotlib with interactive tooltips)
        fig = visualize_valuation_results(
            df, 
            output_path="./valuation_comparison.png",
            interactive=True  # Enable hover tooltips
        )
        
        # Step 5: Create interactive HTML plot (Plotly - fully interactive)
        interactive_fig = create_interactive_html_plot(
            df,
            output_path="./valuation_interactive.html"
        )
        print("\nOpen 'valuation_interactive.html' in your browser for a fully interactive plot!")
