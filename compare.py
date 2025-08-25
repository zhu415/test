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
        External reference data for comparison (DataFrame, Series, or file path)
    reference_date : Optional[str]
        Specific date column to use as reference from the DataFrame
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
    
    Reference Data Priority:
    1. If reference_data is provided (external data), use it
    2. If reference_date is provided and exists in DataFrame, use that date
    3. Otherwise, use the latest date (rightmost column) in DataFrame
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
        
        # Determine reference column based on priority
        ref_series = None
        actual_ref_date = None
        
        # Priority 1: External reference data provided
        if reference_data is not None:
            if isinstance(reference_data, str):
                # Load from file
                ref_series = load_reference_data(reference_data, index_name)
                actual_ref_date = 'external'
            elif isinstance(reference_data, pd.DataFrame):
                # Extract relevant column for this index
                ref_series = extract_reference_series(reference_data, index_name)
                actual_ref_date = 'external'
            else:
                ref_series = reference_data
                actual_ref_date = 'external'
        
        # Priority 2: Specific date provided and exists in DataFrame
        elif reference_date is not None:
            if reference_date in df.columns:
                ref_series = df[reference_date]
                actual_ref_date = reference_date
            else:
                print(f"Warning: Date {reference_date} not found in {index_name}, using latest date instead")
                ref_series = df.iloc[:, -1]
                actual_ref_date = df.columns[-1]
        
        # Priority 3: Use latest date (rightmost column)
        else:
            ref_series = df.iloc[:, -1]
            actual_ref_date = df.columns[-1]
        
        # Get asset class mapping for this index
        index_mapping = mapping_df[mapping_df['index'] == index_name]
        
        # Compare with other dates
        for date_col in df.columns:
            # Skip if this is the reference date (unless external reference)
            if actual_ref_date != 'external' and date_col == actual_ref_date:
                continue
                
            comparison_series = df[date_col]
            
            # 1. Check Rolling Futures differences
            check_rolling_futures(
                ref_series, comparison_series, 
                index_name, actual_ref_date, date_col,
                threshold_rf, results
            )
            
            # 2. Check Asset Class differences
            check_asset_classes(
                ref_series, comparison_series,
                index_name, actual_ref_date, date_col,
                index_mapping, threshold_asset, results
            )
            
            # 3. Check Full GS differences
            check_full_gs(
                ref_series, comparison_series,
                index_name, actual_ref_date, date_col,
                threshold_gs_bps, results
            )
            
            # 4. Check Borrow Shift differences (if needed)
            check_borrow_shift(
                ref_series, comparison_series,
                index_name, actual_ref_date, date_col,
                threshold_gs_bps, results
            )
    
    # Print and/or save results
    print_results(results)
    
    if output_file:
        save_results(results, output_file)
    
    return results
