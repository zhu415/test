import pandas as pd
import numpy as np
from typing import Dict, Optional, Union, List, Tuple
from datetime import datetime

def compare_index_data(
    wesByIndex: Dict[str, Dict[str, pd.DataFrame]],
    mapping_csv_path: str,
    reference_data: Optional[Union[pd.DataFrame, str, pd.Series]] = None,
    reference_date: Optional[str] = None,
    bm_key: str = 'continuous bm',
    indices_to_benchmark: Optional[List[str]] = None,
    output_file: Optional[str] = None,
    threshold_rf: float = 0.10,  # 10% for RF
    threshold_asset: float = 0.10,  # 10% for asset class
    threshold_gs_bps: float = 0.001  # 10bps = 0.1% = 0.001 in decimal
) -> Dict:
    """
    Compare index benchmark data across dates.
    
    Parameters:
    -----------
    wesByIndex : Dict
        Nested dictionary with structure {bm_key: {index_name: DataFrame}}
    mapping_csv_path : str
        Path to CSV file containing asset class mappings
    reference_data : Optional
        Reference data for comparison (DataFrame, Series, or file path)
    reference_date : Optional[str]
        Specific date column to use as reference
    bm_key : str
        Key for benchmark data (default: 'continuous bm')
    indices_to_benchmark : Optional[List[str]]
        List of index names to process (if None, processes all)
    output_file : Optional[str]
        Path to save comparison results
    threshold_rf : float
        Threshold for Rolling Futures differences (default: 0.10)
    threshold_asset : float
        Threshold for asset class differences (default: 0.10)
    threshold_gs_bps : float
        Threshold for Full GS differences in decimal (default: 0.001)
    
    Returns:
    --------
    Dict containing comparison results
    """
    
    # Load mapping CSV
    mapping_df = pd.read_csv(mapping_csv_path)
    
    # Initialize results dictionary
    results = {
        'rf_breaches': [],
        'asset_class_breaches': [],
        'full_gs_breaches': [],
        'borrow_shift_breaches': []
    }
    
    # Get indices to process
    if indices_to_benchmark is None:
        indices_to_benchmark = list(wesByIndex[bm_key].keys())
    
    # Process each index
    for index_name in indices_to_benchmark:
        if index_name not in wesByIndex[bm_key]:
            print(f"Warning: {index_name} not found in data")
            continue
            
        df = wesByIndex[bm_key][index_name]
        
        # Determine reference column
        if reference_data is not None:
            # Handle external reference data
            if isinstance(reference_data, str):
                # Load from file
                ref_series = load_reference_data(reference_data, index_name)
            elif isinstance(reference_data, pd.DataFrame):
                # Extract relevant column for this index
                ref_series = extract_reference_series(reference_data, index_name)
            else:
                ref_series = reference_data
        elif reference_date is not None:
            # Use specific date column
            if reference_date in df.columns:
                ref_series = df[reference_date]
            else:
                print(f"Warning: Date {reference_date} not found in {index_name}")
                continue
        else:
            # Use latest date (rightmost column)
            ref_series = df.iloc[:, -1]
            reference_date = df.columns[-1]
        
        # Get asset class mapping for this index
        index_mapping = mapping_df[mapping_df['index'] == index_name]
        
        # Compare with other dates
        for date_col in df.columns:
            if date_col == reference_date:
                continue
                
            comparison_series = df[date_col]
            
            # 1. Check Rolling Futures differences
            check_rolling_futures(
                ref_series, comparison_series, 
                index_name, reference_date, date_col,
                threshold_rf, results
            )
            
            # 2. Check Asset Class differences
            check_asset_classes(
                ref_series, comparison_series,
                index_name, reference_date, date_col,
                index_mapping, threshold_asset, results
            )
            
            # 3. Check Full GS differences
            check_full_gs(
                ref_series, comparison_series,
                index_name, reference_date, date_col,
                threshold_gs_bps, results
            )
            
            # 4. Check Borrow Shift differences (if needed)
            check_borrow_shift(
                ref_series, comparison_series,
                index_name, reference_date, date_col,
                threshold_gs_bps, results
            )
    
    # Print and/or save results
    print_results(results)
    
    if output_file:
        save_results(results, output_file)
    
    return results


def check_rolling_futures(ref_series, comp_series, index_name, ref_date, comp_date, 
                         threshold, results):
    """Check Rolling Futures differences."""
    rf_rows = [(idx, val) for idx, val in ref_series.items() 
               if isinstance(idx, tuple) and idx[0] == 'isRollingFutures']
    
    for idx, ref_val in rf_rows:
        if idx in comp_series.index:
            comp_val = comp_series[idx]
            if ref_val != 0:  # Avoid division by zero
                diff = abs((comp_val - ref_val) / ref_val)
                if diff > threshold:
                    results['rf_breaches'].append({
                        'index': index_name,
                        'rf_type': idx[1],
                        'ref_date': ref_date,
                        'comp_date': comp_date,
                        'ref_value': ref_val,
                        'comp_value': comp_val,
                        'difference_pct': diff * 100
                    })


def check_asset_classes(ref_series, comp_series, index_name, ref_date, comp_date,
                        mapping_df, threshold, results):
    """Check Asset Class differences."""
    # Get asset class rows
    asset_rows = [(idx, val) for idx, val in ref_series.items() 
                  if isinstance(idx, tuple) and idx[0] == 'assetClass']
    
    for idx, ref_val in asset_rows:
        asset_type = idx[1]  # 'Equity', 'Rate', or 'Other'
        
        if idx in comp_series.index:
            comp_val = comp_series[idx]
            if ref_val != 0:  # Avoid division by zero
                diff = abs((comp_val - ref_val) / ref_val)
                if diff > threshold:
                    results['asset_class_breaches'].append({
                        'index': index_name,
                        'asset_class': asset_type,
                        'ref_date': ref_date,
                        'comp_date': comp_date,
                        'ref_value': ref_val,
                        'comp_value': comp_val,
                        'difference_pct': diff * 100
                    })


def check_full_gs(ref_series, comp_series, index_name, ref_date, comp_date,
                  threshold_bps, results):
    """Check Full GS differences for each tenor."""
    tenors = ['6m', '1y', '2y']
    
    for tenor in tenors:
        idx = ('Full GSs', tenor)
        if idx in ref_series.index and idx in comp_series.index:
            ref_val = ref_series[idx]
            comp_val = comp_series[idx]
            diff = abs(comp_val - ref_val)
            
            if diff > threshold_bps:
                results['full_gs_breaches'].append({
                    'index': index_name,
                    'tenor': tenor,
                    'ref_date': ref_date,
                    'comp_date': comp_date,
                    'ref_value': ref_val,
                    'comp_value': comp_val,
                    'difference_bps': diff * 10000  # Convert to bps
                })


def check_borrow_shift(ref_series, comp_series, index_name, ref_date, comp_date,
                       threshold_bps, results):
    """Check Borrow Shift differences for each tenor."""
    tenors = ['6m', '1y', '2y']
    
    for tenor in tenors:
        idx = ('Borrow Shift', tenor)
        if idx in ref_series.index and idx in comp_series.index:
            ref_val = ref_series[idx]
            comp_val = comp_series[idx]
            diff = abs(comp_val - ref_val)
            
            if diff > threshold_bps:
                results['borrow_shift_breaches'].append({
                    'index': index_name,
                    'tenor': tenor,
                    'ref_date': ref_date,
                    'comp_date': comp_date,
                    'ref_value': ref_val,
                    'comp_value': comp_val,
                    'difference_bps': diff * 10000  # Convert to bps
                })


def load_reference_data(filepath: str, index_name: str) -> pd.Series:
    """Load reference data from file."""
    # Implementation depends on file format
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath, index_col=0)
        return df[index_name] if index_name in df.columns else df.iloc[:, 0]
    elif filepath.endswith('.txt'):
        # Parse text file - implementation depends on format
        pass
    return pd.Series()


def extract_reference_series(df: pd.DataFrame, index_name: str) -> pd.Series:
    """Extract reference series from DataFrame."""
    if index_name in df.columns:
        return df[index_name]
    # If index_name not in columns, might need different extraction logic
    return df.iloc[:, 0]


def print_results(results: Dict):
    """Print comparison results in a formatted way."""
    print("\n" + "="*80)
    print("COMPARISON RESULTS")
    print("="*80)
    
    # Rolling Futures breaches
    if results['rf_breaches']:
        print("\n📊 ROLLING FUTURES BREACHES (>10% difference):")
        print("-" * 60)
        for breach in results['rf_breaches']:
            print(f"  Index: {breach['index']} | RF Type: {breach['rf_type']}")
            print(f"  Dates: {breach['ref_date']} vs {breach['comp_date']}")
            print(f"  Values: {breach['ref_value']:.4f} vs {breach['comp_value']:.4f}")
            print(f"  Difference: {breach['difference_pct']:.2f}%\n")
    
    # Asset Class breaches
    if results['asset_class_breaches']:
        print("\n💼 ASSET CLASS BREACHES (>10% difference):")
        print("-" * 60)
        for breach in results['asset_class_breaches']:
            print(f"  Index: {breach['index']} | Asset Class: {breach['asset_class']}")
            print(f"  Dates: {breach['ref_date']} vs {breach['comp_date']}")
            print(f"  Values: {breach['ref_value']:.4f} vs {breach['comp_value']:.4f}")
            print(f"  Difference: {breach['difference_pct']:.2f}%\n")
    
    # Full GS breaches
    if results['full_gs_breaches']:
        print("\n📈 FULL GS BREACHES (>10bps difference):")
        print("-" * 60)
        for breach in results['full_gs_breaches']:
            print(f"  Index: {breach['index']} | Tenor: {breach['tenor']}")
            print(f"  Dates: {breach['ref_date']} vs {breach['comp_date']}")
            print(f"  Values: {breach['ref_value']:.4f} vs {breach['comp_value']:.4f}")
            print(f"  Difference: {breach['difference_bps']:.2f} bps\n")
    
    # Borrow Shift breaches
    if results['borrow_shift_breaches']:
        print("\n🔄 BORROW SHIFT BREACHES (>10bps difference):")
        print("-" * 60)
        for breach in results['borrow_shift_breaches']:
            print(f"  Index: {breach['index']} | Tenor: {breach['tenor']}")
            print(f"  Dates: {breach['ref_date']} vs {breach['comp_date']}")
            print(f"  Values: {breach['ref_value']:.4f} vs {breach['comp_value']:.4f}")
            print(f"  Difference: {breach['difference_bps']:.2f} bps\n")
    
    if not any([results['rf_breaches'], results['asset_class_breaches'], 
                results['full_gs_breaches'], results['borrow_shift_breaches']]):
        print("\n✅ No breaches found - all differences within thresholds.")


def save_results(results: Dict, filepath: str):
    """Save results to file."""
    # Convert results to DataFrame for easier saving
    all_breaches = []
    
    for breach_type, breaches in results.items():
        for breach in breaches:
            breach['breach_type'] = breach_type
            all_breaches.append(breach)
    
    if all_breaches:
        df = pd.DataFrame(all_breaches)
        df.to_csv(filepath, index=False)
        print(f"\n💾 Results saved to: {filepath}")
    else:
        with open(filepath, 'w') as f:
            f.write("No breaches found - all differences within thresholds.\n")
        print(f"\n💾 No breaches found - summary saved to: {filepath}")


# Example usage:
if __name__ == "__main__":
    # Example call
    # results = compare_index_data(
    #     wesByIndex=your_data_dict,
    #     mapping_csv_path="mapping.csv",
    #     reference_data=None,  # Will use latest date
    #     indices_to_benchmark=['INDEX1', 'INDEX2'],
    #     output_file="comparison_results.csv"
    # )
