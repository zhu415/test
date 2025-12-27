import pandas as pd
from lxml import etree
import os
from datetime import datetime, timedelta

def extract_valuation_results(output_xml_path, original_input_path, index_name, date_step=1):
    """
    Extract IndexValuationResults from output XML and match with dates.
    
    Parameters:
    -----------
    output_xml_path : str
        Path to the output XML file (after running through C++ library)
    original_input_path : str
        Path to the original input XML file (to get BuildDate and ExpiryDate)
    index_name : str
        Name of the index
    date_step : int
        Step size used when generating dates
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with columns: Index, Date, Value
    """
    
    # Parse the original input to get BuildDate and ExpiryDate
    parser = etree.XMLParser(remove_blank_text=False, strip_cdata=False)
    original_tree = etree.parse(original_input_path, parser)
    original_root = original_tree.getroot()
    
    # Get BuildDate
    build_dates = {}
    for build_date_elem in original_root.iter("BuildDate"):
        if build_date_elem.text:
            date_value = build_date_elem.text.strip()
            build_dates[date_value] = True
    
    build_date_str = list(build_dates.keys())[0].strip()
    build_date = datetime.strptime(build_date_str, "%Y-%m-%d")
    
    # Get ExpiryDate
    expiry_date_str = None
    for calibrated_forward in original_root.iter("CalibratedForward"):
        for market_data in calibrated_forward.findall("MarketData"):
            data_source = market_data.find("DataSource")
            if data_source is not None and data_source.text:
                text = data_source.text.strip()
                try:
                    datetime.strptime(text, "%Y-%m-%d")
                    expiry_date_str = text
                    break
                except ValueError:
                    continue
        if expiry_date_str:
            break
    
    expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
    
    # Generate the same date list
    date_list = []
    current_date = build_date
    while current_date <= expiry_date:
        date_list.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=date_step)
    
    # Parse the output XML
    output_tree = etree.parse(output_xml_path, parser)
    output_root = output_tree.getroot()
    
    # Extract values from IndexValuationResults
    values = []
    index_valuation_results = output_root.find(".//IndexValuationResults")
    
    if index_valuation_results is None:
        raise ValueError(f"Could not find IndexValuationResults in {output_xml_path}")
    
    for value_elem in index_valuation_results.findall("Value"):
        if value_elem.text:
            values.append(float(value_elem.text.strip()))
    
    # Check if number of values matches number of dates
    if len(values) != len(date_list):
        print(f"WARNING: Number of values ({len(values)}) doesn't match number of dates ({len(date_list)})")
    
    # Create DataFrame
    df = pd.DataFrame({
        'Index': [index_name] * len(date_list),
        'Date': date_list,
        'Value': values[:len(date_list)]  # Use only as many values as we have dates
    })
    
    return df


def process_all_output_files(output_dir, original_input_path, indices, date_step=1):
    """
    Process all output XML files and combine results into a single DataFrame.
    
    Parameters:
    -----------
    output_dir : str
        Directory containing the output XML files
    original_input_path : str
        Path to the original input XML file
    indices : list
        List of index names used
    date_step : int
        Step size used when generating dates
        
    Returns:
    --------
    pd.DataFrame
        Combined DataFrame with columns: Index, DateToMatch_Type, Date, Value
    """
    
    date_to_match_types = ["BuildDate", "ExpiryDate", "Empty"]
    all_data = []
    
    for index_name in indices:
        for dtm_type in date_to_match_types:
            # Construct the output filename
            output_filename = f"{index_name}_{dtm_type}.xml"
            output_path = os.path.join(output_dir, output_filename)
            
            if not os.path.exists(output_path):
                print(f"WARNING: File not found: {output_path}")
                continue
            
            print(f"Processing: {output_filename}")
            
            try:
                # Extract data from this file
                df = extract_valuation_results(output_path, original_input_path, index_name, date_step)
                
                # Add DateToMatch_Type column
                df['DateToMatch_Type'] = dtm_type
                
                all_data.append(df)
                
            except Exception as e:
                print(f"ERROR processing {output_filename}: {str(e)}")
                continue
    
    # Combine all dataframes
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        # Reorder columns
        combined_df = combined_df[['Index', 'DateToMatch_Type', 'Date', 'Value']]
        return combined_df
    else:
        return pd.DataFrame(columns=['Index', 'DateToMatch_Type', 'Date', 'Value'])


def save_results_to_csv(output_dir, original_input_path, indices, csv_output_path, date_step=1):
    """
    Process all output files and save to CSV.
    
    Parameters:
    -----------
    output_dir : str
        Directory containing the output XML files
    original_input_path : str
        Path to the original input XML file
    indices : list
        List of index names used
    csv_output_path : str
        Path where the CSV file should be saved
    date_step : int
        Step size used when generating dates
    """
    
    # Process all files
    df = process_all_output_files(output_dir, original_input_path, indices, date_step)
    
    # Save to CSV
    df.to_csv(csv_output_path, index=False)
    print(f"\nResults saved to: {csv_output_path}")
    print(f"Total rows: {len(df)}")
    print(f"\nDataFrame preview:")
    print(df.head(10))
    
    # Print summary statistics
    print(f"\nSummary by Index and DateToMatch_Type:")
    summary = df.groupby(['Index', 'DateToMatch_Type']).agg({
        'Value': ['count', 'mean', 'min', 'max']
    })
    print(summary)
    
    return df


# Example usage:
if __name__ == "__main__":
    # Define the indices you used
    indices = ["SPX500", "SPX500_Weekly"]  # Adjust based on your actual indices
    
    # Process all output files and save to CSV
    df = save_results_to_csv(
        output_dir="./output",
        original_input_path="your_input_file.xml",
        indices=indices,
        csv_output_path="./valuation_results.csv",
        date_step=1  # Use the same date_step as when you created the files
    )
    
    # You can also access the dataframe directly
    print("\nFull DataFrame:")
    print(df)
