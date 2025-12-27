import pandas as pd
from lxml import etree
import os
import glob

def extract_valuation_results(input_xml_path, output_xml_path):
    """
    Extract IndexValuationResults from output XML and match with dates from input XML.
    
    Parameters:
    -----------
    input_xml_path : str
        Path to the input XML file (contains IndexValuation with dates)
    output_xml_path : str
        Path to the output XML file (contains IndexValuationResults with values)
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with columns: Date, Value
    """
    
    parser = etree.XMLParser(remove_blank_text=False, strip_cdata=False)
    
    # Parse the INPUT XML to get dates
    input_tree = etree.parse(input_xml_path, parser)
    input_root = input_tree.getroot()
    
    # Extract dates from IndexValuation section in INPUT file
    date_list = []
    index_valuation = input_root.find(".//IndexValuation")
    
    if index_valuation is None:
        raise ValueError(f"Could not find IndexValuation in {input_xml_path}")
    
    for date_elem in index_valuation.findall("Date"):
        if date_elem.text:
            date_list.append(date_elem.text.strip())
    
    # Parse the OUTPUT XML to get values
    output_tree = etree.parse(output_xml_path, parser)
    output_root = output_tree.getroot()
    
    # Extract values from IndexValuationResults in OUTPUT file
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
        print(f"  Input file: {input_xml_path}")
        print(f"  Output file: {output_xml_path}")
    
    # Create DataFrame
    df = pd.DataFrame({
        'Date': date_list,
        'Value': values[:len(date_list)]  # Use only as many values as we have dates
    })
    
    return df


def process_directory(directory):
    """
    Process all input and output XML files in a directory.
    
    Parameters:
    -----------
    directory : str
        Directory containing both input and output XML files
        Input files: {indexName}_{DateToMatch_Type}.xml
        Output files: OUT_{indexName}_{DateToMatch_Type}.xml
        
    Returns:
    --------
    pd.DataFrame
        Combined DataFrame with columns: Index, DateToMatch_Type, Date, Value
    """
    
    # Find all input XML files (non-OUT files)
    all_files = glob.glob(os.path.join(directory, "*.xml"))
    input_files = [f for f in all_files if not os.path.basename(f).startswith("OUT_")]
    
    all_data = []
    
    for input_path in input_files:
        input_filename = os.path.basename(input_path)
        
        # Construct corresponding output filename
        output_filename = "OUT_" + input_filename
        output_path = os.path.join(directory, output_filename)
        
        if not os.path.exists(output_path):
            print(f"WARNING: Output file not found for {input_filename}")
            print(f"  Expected: {output_filename}")
            continue
        
        print(f"Processing: {input_filename} -> {output_filename}")
        
        try:
            # Parse filename to extract index name and DateToMatch type
            # Expected format: {indexName}_{DateToMatch_Type}.xml
            base_name = input_filename.replace(".xml", "")
            parts = base_name.rsplit("_", 1)  # Split from the right, only once
            
            if len(parts) == 2:
                index_name = parts[0]
                dtm_type = parts[1]
            else:
                print(f"WARNING: Could not parse filename: {input_filename}")
                continue
            
            # Extract data from input and output files
            df = extract_valuation_results(input_path, output_path)
            
            # Add Index and DateToMatch_Type columns
            df['Index'] = index_name
            df['DateToMatch_Type'] = dtm_type
            
            all_data.append(df)
            
        except Exception as e:
            print(f"ERROR processing {input_filename}: {str(e)}")
            continue
    
    # Combine all dataframes
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        # Reorder columns
        combined_df = combined_df[['Index', 'DateToMatch_Type', 'Date', 'Value']]
        return combined_df
    else:
        return pd.DataFrame(columns=['Index', 'DateToMatch_Type', 'Date', 'Value'])


def save_results_to_csv(directory, csv_output_path):
    """
    Process all files in a directory and save to CSV.
    
    Parameters:
    -----------
    directory : str
        Directory containing both input and output XML files
    csv_output_path : str
        Path where the CSV file should be saved
        
    Returns:
    --------
    pd.DataFrame
        The combined DataFrame
    """
    
    # Process all files
    df = process_directory(directory)
    
    if len(df) == 0:
        print("No data extracted!")
        return df
    
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


def create_pivot_table(df, output_path=None):
    """
    Create a pivot table for easier comparison across DateToMatch types.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame from process_directory
    output_path : str, optional
        Path to save the pivot table CSV
        
    Returns:
    --------
    pd.DataFrame
        Pivot table with Date as index, and columns for each Index-DateToMatch combination
    """
    
    # Create a combined column name
    df['Index_DTM'] = df['Index'] + '_' + df['DateToMatch_Type']
    
    # Create pivot table
    pivot = df.pivot_table(
        values='Value',
        index='Date',
        columns='Index_DTM',
        aggfunc='first'
    )
    
    if output_path:
        pivot.to_csv(output_path)
        print(f"Pivot table saved to: {output_path}")
    
    return pivot


# Example usage:
if __name__ == "__main__":
    # Process all files in the directory
    df = save_results_to_csv(
        directory="./output",
        csv_output_path="./valuation_results.csv"
    )
    
    # Create pivot table if data was extracted
    if len(df) > 0:
        pivot = create_pivot_table(df, output_path="./valuation_results_pivot.csv")
        print("\nPivot Table Preview:")
        print(pivot.head())
