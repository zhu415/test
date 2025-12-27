import pandas as pd
from lxml import etree
import os

def extract_valuation_results(output_xml_path, index_name):
    """
    Extract IndexValuationResults from output XML and match with dates.
    
    Parameters:
    -----------
    output_xml_path : str
        Path to the output XML file (after running through C++ library)
    index_name : str
        Name of the index
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with columns: Index, Date, Value
    """
    
    # Parse the output XML
    parser = etree.XMLParser(remove_blank_text=False, strip_cdata=False)
    output_tree = etree.parse(output_xml_path, parser)
    output_root = output_tree.getroot()
    
    # Extract dates from IndexValuation section
    date_list = []
    index_valuation = output_root.find(".//IndexValuation")
    
    if index_valuation is None:
        raise ValueError(f"Could not find IndexValuation in {output_xml_path}")
    
    for date_elem in index_valuation.findall("Date"):
        if date_elem.text:
            date_list.append(date_elem.text.strip())
    
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
        print(f"WARNING in {output_xml_path}: Number of values ({len(values)}) doesn't match number of dates ({len(date_list)})")
    
    # Create DataFrame
    df = pd.DataFrame({
        'Index': [index_name] * len(date_list),
        'Date': date_list,
        'Value': values[:len(date_list)]  # Use only as many values as we have dates
    })
    
    return df


def process_all_output_files(output_dir, indices):
    """
    Process all output XML files and combine results into a single DataFrame.
    
    Parameters:
    -----------
    output_dir : str
        Directory containing the output XML files
    indices : list
        List of index names used
        
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
                df = extract_valuation_results(output_path, index_name)
                
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


def save_results_to_csv(output_dir, indices, csv_output_path):
    """
    Process all output files and save to CSV.
    
    Parameters:
    -----------
    output_dir : str
        Directory containing the output XML files
    indices : list
        List of index names used
    csv_output_path : str
        Path where the CSV file should be saved
    """
    
    # Process all files
    df = process_all_output_files(output_dir, indices)
    
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
        DataFrame from process_all_output_files
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
    # Define the indices you used
    indices = ["SPX500", "SPX500_Weekly"]
    
    # Process all output files and save to CSV
    df = save_results_to_csv(
        output_dir="./output",
        indices=indices,
        csv_output_path="./valuation_results.csv"
    )
    
    # Create pivot table
    pivot = create_pivot_table(df, output_path="./valuation_results_pivot.csv")
    print("\nPivot Table:")
    print(pivot.head())
