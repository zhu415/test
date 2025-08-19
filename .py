import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

def detect_075_multiplier(df, weight_col='sum_weight_exclu_USD_CASH', date_col='date'):
    """
    Detect periods when 0.75 multiplier was applied to portfolio weights.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing weight sums and dates
    weight_col : str
        Column name containing sum of weights
    date_col : str
        Column name containing dates
    
    Returns:
    --------
    dict : Analysis results including detected periods and statistics
    """
    
    # Create a copy to avoid modifying original
    data = df[[date_col, weight_col]].copy()
    data = data.sort_values(date_col).reset_index(drop=True)
    
    # 1. Analyze weight distribution
    weights = data[weight_col].values
    
    # 2. Identify clear thresholds
    # If multiplier is applied, max value should be around 0.75
    # If not applied, values can go up to 1.0
    max_weight = weights.max()
    
    # 3. Use clustering approach to separate two regimes
    # Method 1: Simple threshold-based detection
    # If weight > 0.75, likely no multiplier (assuming leverage can be 1)
    # If weight <= 0.75, need more analysis
    
    threshold_high = 0.76  # Slight buffer above 0.75
    clearly_no_multiplier = weights > threshold_high
    
    # 4. For ambiguous cases (weights <= 0.75), analyze the ratio
    # If multiplier applied: weight = 0.75 * leverage
    # If not applied: weight = 1.0 * leverage
    # So ratio = weight_with_multiplier / weight_without = 0.75
    
    # Method 2: Analyze local patterns
    # When switching between regimes, we expect jumps of ratio ~0.75
    weight_changes = np.diff(weights)
    weight_ratios = weights[1:] / weights[:-1]
    
    # 5. Advanced detection using statistical clustering
    from sklearn.mixture import GaussianMixture
    
    # Prepare features for clustering
    features = []
    window = 5  # Local window for feature extraction
    
    for i in range(len(weights)):
        feat = []
        # Current weight value
        feat.append(weights[i])
        
        # Local statistics
        start_idx = max(0, i - window)
        end_idx = min(len(weights), i + window + 1)
        local_weights = weights[start_idx:end_idx]
        
        # Local max (helps identify regime)
        feat.append(local_weights.max())
        
        # Distance from 0.75 and 1.0 anchors
        feat.append(abs(weights[i] - 0.75))
        feat.append(abs(weights[i] - 1.0))
        
        # Normalized weight (assuming max leverage = 1)
        feat.append(weights[i] / 0.75)  # If multiplier active, this estimates leverage
        
        features.append(feat)
    
    features = np.array(features)
    
    # Normalize features for clustering
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # Fit Gaussian Mixture Model
    gmm = GaussianMixture(n_components=2, random_state=42)
    clusters = gmm.fit_predict(features_scaled)
    
    # Determine which cluster corresponds to multiplier
    cluster_means = []
    for c in range(2):
        cluster_means.append(weights[clusters == c].mean())
    
    # Lower mean cluster likely has multiplier applied
    multiplier_cluster = 0 if cluster_means[0] < cluster_means[1] else 1
    has_multiplier = (clusters == multiplier_cluster)
    
    # 6. Refine detection using domain knowledge
    # Smooth out isolated points (reduce noise)
    from scipy.ndimage import binary_closing, binary_opening
    has_multiplier_refined = binary_closing(binary_opening(has_multiplier, iterations=2), iterations=2)
    
    # 7. Identify regime change points
    regime_changes = np.where(np.diff(has_multiplier_refined.astype(int)) != 0)[0] + 1
    
    # 8. Create period summary
    periods = []
    current_start = 0
    current_state = has_multiplier_refined[0]
    
    for change_idx in regime_changes:
        periods.append({
            'start_date': data.iloc[current_start][date_col],
            'end_date': data.iloc[change_idx - 1][date_col],
            'start_idx': current_start,
            'end_idx': change_idx - 1,
            'has_075_multiplier': bool(current_state),
            'avg_weight': weights[current_start:change_idx].mean(),
            'max_weight': weights[current_start:change_idx].max(),
            'min_weight': weights[current_start:change_idx].min()
        })
        current_start = change_idx
        current_state = has_multiplier_refined[change_idx]
    
    # Add final period
    periods.append({
        'start_date': data.iloc[current_start][date_col],
        'end_date': data.iloc[-1][date_col],
        'start_idx': current_start,
        'end_idx': len(data) - 1,
        'has_075_multiplier': bool(current_state),
        'avg_weight': weights[current_start:].mean(),
        'max_weight': weights[current_start:].max(),
        'min_weight': weights[current_start:].min()
    })
    
    # 9. Estimate leverage factors
    estimated_leverage = np.zeros(len(weights))
    for i in range(len(weights)):
        if has_multiplier_refined[i]:
            # weight = 0.75 * leverage
            estimated_leverage[i] = weights[i] / 0.75
        else:
            # weight = 1.0 * leverage
            estimated_leverage[i] = weights[i] / 1.0
    
    # 10. Prepare results
    results = {
        'data': data,
        'has_multiplier': has_multiplier_refined,
        'periods': pd.DataFrame(periods),
        'estimated_leverage': estimated_leverage,
        'regime_changes': regime_changes,
        'statistics': {
            'pct_with_multiplier': has_multiplier_refined.mean() * 100,
            'num_regime_changes': len(regime_changes),
            'avg_weight_with_multiplier': weights[has_multiplier_refined].mean() if has_multiplier_refined.any() else None,
            'avg_weight_without_multiplier': weights[~has_multiplier_refined].mean() if (~has_multiplier_refined).any() else None,
            'max_weight_observed': max_weight
        }
    }
    
    return results


def visualize_detection(results, figure_size=(15, 10)):
    """
    Visualize the detection results.
    
    Parameters:
    -----------
    results : dict
        Results from detect_075_multiplier function
    figure_size : tuple
        Figure size for plots
    """
    
    fig, axes = plt.subplots(3, 1, figsize=figure_size, sharex=True)
    
    data = results['data']
    weights = data[data.columns[1]].values
    dates = pd.to_datetime(data[data.columns[0]])
    has_multiplier = results['has_multiplier']
    
    # Plot 1: Original weights with regime shading
    ax1 = axes[0]
    ax1.plot(dates, weights, 'b-', alpha=0.7, label='Sum of Weights')
    
    # Shade multiplier periods
    for _, period in results['periods'].iterrows():
        if period['has_075_multiplier']:
            start_date = pd.to_datetime(period['start_date'])
            end_date = pd.to_datetime(period['end_date'])
            ax1.axvspan(start_date, end_date, alpha=0.2, color='red', label='0.75 Multiplier' if _ == 0 else '')
    
    ax1.axhline(y=0.75, color='r', linestyle='--', alpha=0.5, label='0.75 threshold')
    ax1.axhline(y=1.0, color='g', linestyle='--', alpha=0.5, label='1.0 threshold')
    ax1.set_ylabel('Sum of Weights')
    ax1.set_title('Weight Sum with Detected 0.75 Multiplier Periods')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Estimated leverage factor
    ax2 = axes[1]
    leverage = results['estimated_leverage']
    ax2.plot(dates, leverage, 'g-', alpha=0.7, label='Estimated Leverage')
    ax2.axhline(y=1.0, color='k', linestyle='--', alpha=0.5, label='Max Leverage (1.0)')
    ax2.set_ylabel('Leverage Factor')
    ax2.set_title('Estimated Leverage Factor (Reverse Engineered)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Binary indicator
    ax3 = axes[2]
    ax3.fill_between(dates, 0, has_multiplier.astype(int), alpha=0.7, label='0.75 Multiplier Active')
    ax3.set_ylabel('Multiplier Active')
    ax3.set_xlabel('Date')
    ax3.set_title('Binary Indicator: 0.75 Multiplier Detection')
    ax3.set_ylim(-0.1, 1.1)
    ax3.set_yticks([0, 1])
    ax3.set_yticklabels(['No', 'Yes'])
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    return fig


def print_summary(results):
    """
    Print a summary of the detection results.
    
    Parameters:
    -----------
    results : dict
        Results from detect_075_multiplier function
    """
    
    print("=" * 60)
    print("DETECTION SUMMARY")
    print("=" * 60)
    
    stats = results['statistics']
    print(f"\nOverall Statistics:")
    print(f"  - Maximum weight observed: {stats['max_weight_observed']:.4f}")
    print(f"  - Percentage of time with 0.75 multiplier: {stats['pct_with_multiplier']:.1f}%")
    print(f"  - Number of regime changes: {stats['num_regime_changes']}")
    
    if stats['avg_weight_with_multiplier'] is not None:
        print(f"  - Avg weight WITH multiplier: {stats['avg_weight_with_multiplier']:.4f}")
    if stats['avg_weight_without_multiplier'] is not None:
        print(f"  - Avg weight WITHOUT multiplier: {stats['avg_weight_without_multiplier']:.4f}")
    
    print(f"\nDetected Periods:")
    print("-" * 60)
    
    for _, period in results['periods'].iterrows():
        status = "WITH 0.75 multiplier" if period['has_075_multiplier'] else "WITHOUT multiplier"
        print(f"{period['start_date']} to {period['end_date']}: {status}")
        print(f"  Avg weight: {period['avg_weight']:.4f}, Range: [{period['min_weight']:.4f}, {period['max_weight']:.4f}]")
    
    print("=" * 60)


# Example usage
def example_usage():
    """
    Example of how to use the detection functions.
    """
    
    # Load your dataframe
    # df = pd.read_csv('your_data.csv')
    # or
    # df = your_existing_dataframe
    
    # Run detection
    # results = detect_075_multiplier(df, 
    #                                 weight_col='sum_weight_exclu_USD_CASH',
    #                                 date_col='date')
    
    # Print summary
    # print_summary(results)
    
    # Visualize results
    # fig = visualize_detection(results)
    
    # Access specific results
    # periods_df = results['periods']  # DataFrame with all detected periods
    # has_multiplier = results['has_multiplier']  # Boolean array for each day
    # leverage = results['estimated_leverage']  # Estimated leverage factors
    
    # Export results
    # results['periods'].to_csv('detected_multiplier_periods.csv', index=False)
    
    pass


if __name__ == "__main__":
    print("0.75 Multiplier Detection Algorithm")
    print("Load your data and call: results = detect_075_multiplier(df)")
    example_usage()
