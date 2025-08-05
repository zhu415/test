
def extract_xml_data_to_dataframe(directory_path,
            xml_tags_to_extract,
            file_name_pattern="sorted_*.xml",
            index_name_pattern=r'sorted_([^_-]+',
            rolling_futures=None,
            require_matching_counts=True,
            save_to_csv=False,
            csv_save_directory=None,
            csv_filename=None):
    """
    Extract data from XML files and create a DataFrame
    Args:
        directory_path (str): Path to the directory containing XML files
        xml_tags_to_extract (list): List of XML tag names to extract (e.g., ['BenchmarkSource', 'SourceWeight'])
        file_name_pattern (str): Glob pattern for XML files
        index_name_pattern (str): Regex pattern to extract index name from filename
        rolling_futures (list): List of strings that are the rolling futures, or None to skip rolling futures check
            Assuming first tag contains the values to check
            ### TODO: need to specify that we are checking rolling futures for which tag
        require_matching_counts (bool): If True, all tags must have the same count (correspondence relationshio)
                    If False, extracts all data and create separate rows for each tag-value pair
        save_to_csv (bool): Whether to save the resulting DataFrame to CSV
        csv_save_directory (str): Directory to save CSV file (default: same as directory_path)
        csv_filename (str): Name of the CSV file (default: auto-generated based on extracted tags)
    Returns:
        pandas.DataFrame: DataFrame with columns ['index_name'] + xml_tags_to_extract + ['RollingFuture'] (if rolling_futures provided)
    Example:
        # Extract BenchmarkSource and SourceWeight from files matching pattern
        df = extract_xml_data_to_dataframe(
            directory_path="/path/to/xml/files",
            xml tags to extract=['BenchmarkSource'. 'SourceWeight' 1.
            file_name_pattern="sorted_*.xml",
            index_name_pattern=r'sorted_([^_-]+)',
            rolling_futures=["Name1", "Name2"],
            require_matching_counts=True,
            save_to_csv=True,
            csv_save_directory="/path/to/save",
            csv_filename="benchmark_data.csv")
    """
    
    # validate inputs
    if not xml_tags_to_extract:
        raise ValueError("xml_tags_to_extract cannot be empty")
    if save_to_csv and csv_save_directory and not os.path.exists(csv_save_directory):
        os.makedirs(csv_save_directory, exist_ok=True)
    # set default save directory if not provided
    if save_to_csv and csv_save_directory is None:
        csv_save_directory = directory_path
    # generate default CSV filename based on extracted tags if not provided
    if save_to_csv and csv_filename is None:
        tags_string = "_".join(xml_tags_to_extract)
        csv_filename = f"extracted_{tags_string}.csv"    

    # list to store all extracted data
    data_rows = []
    # get all XML files that match the pattern "sorted_{index_name}_*"
    xml_files = list(Path(directory_path).glob(file_name_pattern))
    if not xml_files:
        print(f"Warning: No XML files found matching patter '{file_name_pattern}' in {directory_path}")
        return pd.DataFrame()
    # sort files for consistet process order
    xml_files.sort()
    for file_path in xml_files:
        filename = file_path.name # extract index_name from filename
        print(f"Processing: {filename}")
        # extract index_name from filename using the provided pattern
        match = re.match(index_name_pattern, filename) # e.g., pattern:sorted_{index_name}-other_contents.xml
        if not match:
            print(f"Warning: Could not extract index name from {filename} using pattern '{index_name_pattern}'")
            continue
        index_name = match.group(1)
        # read the XML file
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
        # extract data for each specified XML tag
        extracted_data = {}
        min_length = float('inf')
        max_length = 0

        for tag in xml_tags_to_extract:
            pattern = f'<{tag}>(.*?)</{tag}>'
            values = re.findall(pattern, content, re.DOTALL)
            # clean up extracted values (strip whitespaces)
            values = [value.strip() for value in values]
            extracted_data[tag] = values
            min_length = min(min_length, len(values))
            max_length = max(max_length, len(values))
        # check if all tags have the same number of entries
        tag_lengths = [len(extracted_data[tag]) for tag in xml_tags_to_extract]
        if require_matching_counts:
            # strict mode: all tags must have the same count
            if len(set(tag_lengths)) > 1:
                error_msg = f"ERROR in {filename}: Tag count mismatch when require_matching_counts=True\n"
                error_msg += f"Tag lengths: {dict(zip(xml_tags_to_extratc, tag_lengths))}\n"
                error_msg += "All tags must have the same number of entries for correspondence relationship."
                print(error_msg)
                continue # skip this file
            # all counts match, proceed with correspondence approach
            data_count = min_length
            # get rolling futures flags (assuming first tag contains the values to check)
            if rolling_futures is not None and xml_tags_to_extract and data_count > 0:
                first_tag_values = extracted_data[xml_tags_to_extract[0]]
                rolling_future_flags = ['Yes' if value in rolling_futures else 'No' for value in first_tag_values]
            else:
                rolling_future_flags = None
            # create rows for DataFrame with correspondence
            for i in range(data_count):
                row_data = {'index_name': index_name}

                # add extracted tag data
                for tag in xml_tags_to_extract:
                    row_data[tag] = extracted_data[tag][i]
                # add rolling future flag on if rolling futures was provided
                if rolling_future_flags is not None:
                    row_data['RollingFuture'] = rolling_future_flags[i]
                data_rows.append(row_data)
        else:
            # flexible mode: extract all data regardless of count mismatches
            if len(set(tag_lengths)) > 1:
                print(f"Info: Different tag counts in {filename} - Tag lengths: {dict(zip(xml_tags_to_extract, tag_lengths))}")
                print("Extracting all data in separate rows (require_matching_counts=False)")
            # create separate rows for each tag-value pair
            for tag in xml_tags_to_extract:
                for value in extracted_data[tag]:
                    row_data = {
                        'index_name': index_name,
                        'tag_name': tag,
                        'tag_value': value
                    }
                    # add rolling future flag only if rolling_futures was provided
                    if rolling_futures is not None:
                        rolling_flag = 'Yes' if value in rolling_futures else 'No'
                        row_data['RollingFuture'] = rolling_flag
                    data_rows.append(row_data)
        

        else:
            # flexible mode: extract all data regardless of count mismatches
            if len(set(tag_lengths)) > 1:
                print(f"Info: Different tag counts in {filename} - Tag lengths: {dict(zip(xml_tags_to_extract, tag_lengths))}")
                print("Extracting all data in separate rows (require_matching_counts=False)")
            # create separate rows for each tag-value pair
            for tag in xml_tags_to_extract:
                for value in extracted_data[tag]:
                    row_data = {
                        'index_name': index_name,
                        'tag_name': tag,
                        'tag_value': value
                    }
                    # add rolling future flag only if rolling_futures was provided
                    if rolling_futures is not None:
                        rolling_flag = 'Yes' if value in rolling_futures else 'No'
                        row_data['RollingFuture'] = rolling_flag
                    data_rows.append(row_data)
    # create DataFrame
    df = pd.DataFrame(data_rows)
    if df.empty:
        print("Warning: No data was extracted. DataFrame is empty.")
        return df


    print(f"Successfully extratced {len(df)} rows from {len(xml_files)} files")
    print(f"DataFrame columns: {list(df.columns)}")
    # save to CSV if requested
    if save_to_csv:
        csv_path = Path(csv_save_directory) / csv_filename
        try:
            df.to_csv(csv_path, index=False)
            print(f"Data saved to CSV: {csv_path}")
        except Exception as e:
            print(f"Errpr saving to CSV: {e}")
    return df





def extract_DivRhoFlat_data(directory_path,
            xml_tags_to_extract,
            file_name_pattern="*_output.xml",
            index_name_pattern=r'(.+)_output\.xml$',
            save_to_csv=False,
            csv_save_directory=None,
            csv_filename=None):
    """

    Extract DivRhoFlat Data from XML files and create DataFrame
    Args:
        directory_path (str) : Path to directory with XML files
        xml_tags_to_extract (list): List of XML tag names to extract (e.g., ['DivRhoFlat', 'DivRhoFlatGamma'])
        file_name_pattern (str): Glob pattern for XML files
        index_name_pattern (str): Regex pattern to extract index name from filename
        save_to_csv (bool): Whether to save the resulting DataFrame to CSV
        csv_save_directory (str) : Directory to save CSV file (default: same as directory_path)
        csv_filename (str): Name of the CSV file (default: auto-generated based on extracted tags)
    Returns:
        pandas.DataFrame: DataFrame with [Index_Name, Asset_Name, GSRisk_Value]
    """
    data_rows = []
    # find all xml files in directory
    xml_files = list(Path(directory_path).glob(file_name_pattern))
    # sort files for consistet process order
    xml_files.sort()
    for file_path in xml_files:
        filename = file_path.name # extract index_name from filename
        print(f"Processing: {filename}")
        # extract index_name from filename using the provided pattern
        match = re.match(index_name_pattern, filename) # e.g., pattern:sorted_{index_name}-other_contents.xml


        if not match:
            print(f"Warning: Could not extract index name from {filename} using pattern '{index_name_pattern}'")
            continue
        index_name = match.group(1)
        # read the XML file
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
        # Process xml_tags_to_extract: each element represents the name of a tag corresponding to a section of interest.
        for tag in xml_tags_to_extract:
            pattern = f'<{tag}>(.*?)</{tag}>'
            sections = re.findall(pattern, content, re.DOTALL)
            print(f" Found {len(sections)} {tag} sections")
            # process each <tag> section
            for i, section in enumerate(sections):

                Id_pattern = r'<Id>DivRhoFlat_BumpYieldAsGrowthSpread_Annualized_([^<]+)</Id>'
                Id_match = re.search(Id_pattern, section)
                # extract value from value tag
                Value_pattern = r'<Value>([^<]+)</Value>'
                Value_match = re.search(Value_pattern, section)
                # check if both patterns were found
                if Id_match and Value_match:
                    asset_name = Id_match.group(1).strip()
                    value = Value_match.group(1).strip()
                    data_rows.append({
                        'Index_Name': index_name,
                        'Asset_Name': asset_name,
                        'GSRisk_Value': value
                    })
                    print(f" Section {i+1}: Found asset '{asset_name}' with value '{value}'")
                else:
                    print(f" Section {i+1}: Missing data")
                    if not Id_match:
                        print(f" - No Id tag found")
                    if not Value_match:
                        print(f" - No Value tag found")

    # create DataFrame
    df = pd.DataFrame(data_rows)
    if df.empty:
        print("Warning: No data was extracted. DataFrame is empty.")
        return df
    print(f"Successfully extratced {len(df)} rows from {len(xml_files)} files")
    print(f"DataFrame columns: {list(df.columns)}")
    # save to CSV if requested
    if save_to_csv:
        csv_path = Path(csv_save_directory) / csv_filename
        try:
            df.to_csv(csv_path, index=False)
            print(f"Data saved to CSV: {csv_path}")
        except Exception as e:
            print(f"Errpr saving to CSV: {e}")
    return df







#################################################
########## Comprehensive XML EXtractor ##########
#################################################


import os
import re
import pandas as pd
from pathlib import Path
from typing import List, Dict, Union, Optional, Any


def extract_xml_data_comprehensive(
    directory_path: str,
    extraction_config: List[Dict[str, Any]],
    file_name_pattern: str = "*.xml",
    index_name_pattern: str = r'(.+)\.xml$',
    rolling_futures: Optional[List[str]] = None,
    rolling_futures_tag: Optional[str] = None,
    correspondence_groups: Optional[List[Dict[str, Any]]] = None,
    filter_nonzero: bool = False,
    filter_nonzero_tags: Optional[List[str]] = None,
    save_to_csv: bool = False,
    csv_save_directory: Optional[str] = None,
    csv_filename: Optional[str] = None
) -> pd.DataFrame:
    """
    Comprehensive XML data extraction function that handles both simple and nested tags.
    
    Args:
        directory_path (str): Path to the directory containing XML files
        extraction_config (List[Dict]): List of extraction configurations. Each dict should contain:
            - 'type': 'simple' or 'nested'
            - 'tags': List of tag names to extract
            - For nested type, additional keys:
                - 'parent_tag': The parent tag containing nested elements
                - 'nested_tags': List of tag names to extract from within parent_tag
                - 'output_columns': List of column names for the DataFrame (must match nested_tags length)
                - 'id_pattern': (Optional) Regex pattern to extract identifier from Id tag
                - 'value_tag': (Optional) Tag name containing the value (default: 'Value')
                - 'id_tag': (Optional) Tag name containing the identifier (default: 'Id')
        file_name_pattern (str): Glob pattern for XML files
        index_name_pattern (str): Regex pattern to extract index name from filename
        rolling_futures (List[str], optional): List of rolling futures to check against
        rolling_futures_tag (str, optional): Which tag to check for rolling futures
        correspondence_groups (List[Dict], optional): List of correspondence group configurations:
            - 'type': 'simple' or 'nested'
            - 'tags': List of tags that must have matching counts
            - 'config_index': (for nested only) Index of the nested config to check
            - 'require_all_match': bool, if True all tags must match, if False allows partial matches
        filter_nonzero (bool): If True, filter out zero/empty values for specified tags
        filter_nonzero_tags (List[str], optional): Tags to apply non-zero filtering
        save_to_csv (bool): Whether to save the resulting DataFrame to CSV
        csv_save_directory (str, optional): Directory to save CSV file
        csv_filename (str, optional): Name of the CSV file
    
    Returns:
        pandas.DataFrame: DataFrame with extracted data
        
    Example:
        # Mixed extraction configuration
        config = [
            {
                'type': 'simple',
                'tags': ['BenchmarkSource', 'SourceWeight']
            },
            {
                'type': 'nested',
                'parent_tag': 'DivRhoFlat',
                'id_pattern': r'DivRhoFlat_BumpYieldAsGrowthSpread_Annualized_([^<]+)',
                'id_tag': 'Id',
                'value_tag': 'Value',
                'output_columns': ['Asset_Name', 'GSRisk_Value']  # DataFrame column names
            },
            {
                'type': 'nested',
                'parent_tag': 'SomeOtherTag',
                'nested_tags': ['SubTag1', 'SubTag2', 'SubTag3'],  # XML tags to extract
                'output_columns': ['Field1', 'Field2', 'Field3']   # DataFrame column names
            }
        ]
        
        df = extract_xml_data_comprehensive(
            directory_path="/path/to/xml/files",
            extraction_config=config,
            rolling_futures=["Name1", "Name2"],
            rolling_futures_tag="BenchmarkSource",
            filter_nonzero=True,
            filter_nonzero_tags=["GSRisk_Value"]
        )
    """
    
    # Validate inputs
    if not extraction_config:
        raise ValueError("extraction_config cannot be empty")
    
    # Set up CSV saving
    if save_to_csv:
        if csv_save_directory and not os.path.exists(csv_save_directory):
            os.makedirs(csv_save_directory, exist_ok=True)
        if csv_save_directory is None:
            csv_save_directory = directory_path
        if csv_filename is None:
            csv_filename = "extracted_xml_data.csv"
    
    # Get all XML files that match the pattern
    xml_files = list(Path(directory_path).glob(file_name_pattern))
    if not xml_files:
        print(f"Warning: No XML files found matching pattern '{file_name_pattern}' in {directory_path}")
        return pd.DataFrame()
    
    xml_files.sort()
    data_rows = []
    
    for file_path in xml_files:
        filename = file_path.name
        print(f"Processing: {filename}")
        
        # Extract index_name from filename
        match = re.match(index_name_pattern, filename)
        if not match:
            print(f"Warning: Could not extract index name from {filename} using pattern '{index_name_pattern}'")
            continue
        
        index_name = match.group(1)
        
        # Read the XML file
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
        
        file_data_rows = []
        
        # Process each extraction configuration
        for config_idx, config in enumerate(extraction_config):
            config_type = config.get('type', 'simple')
            
            if config_type == 'simple':
                simple_rows = _extract_simple_tags(
                    content, config, index_name, rolling_futures, 
                    rolling_futures_tag, correspondence_groups, config_idx
                )
                file_data_rows.extend(simple_rows)
                
            elif config_type == 'nested':
                nested_rows = _extract_nested_tags(
                    content, config, index_name, correspondence_groups, config_idx
                )
                file_data_rows.extend(nested_rows)
                
            else:
                print(f"Warning: Unknown extraction type '{config_type}' in config")
        
        # Apply non-zero filtering if requested
        if filter_nonzero and filter_nonzero_tags:
            file_data_rows = _filter_nonzero_values(file_data_rows, filter_nonzero_tags)
        
        data_rows.extend(file_data_rows)
    
    # Create DataFrame
    df = pd.DataFrame(data_rows)
    
    if df.empty:
        print("Warning: No data was extracted. DataFrame is empty.")
        return df
    
    print(f"Successfully extracted {len(df)} rows from {len(xml_files)} files")
    print(f"DataFrame columns: {list(df.columns)}")
    
    # Save to CSV if requested
    if save_to_csv:
        csv_path = Path(csv_save_directory) / csv_filename
        try:
            df.to_csv(csv_path, index=False)
            print(f"Data saved to CSV: {csv_path}")
        except Exception as e:
            print(f"Error saving to CSV: {e}")
    
    return df


def _extract_simple_tags(
    content: str, 
    config: Dict[str, Any], 
    index_name: str,
    rolling_futures: Optional[List[str]],
    rolling_futures_tag: Optional[str],
    correspondence_groups: Optional[List[Dict[str, Any]]],
    config_idx: int
) -> List[Dict[str, Any]]:
    """Extract data from simple XML tags."""
    tags = config['tags']
    extracted_data = {}
    
    # Extract data for each tag
    for tag in tags:
        pattern = f'<{tag}>(.*?)</{tag}>'
        values = re.findall(pattern, content, re.DOTALL)
        values = [value.strip() for value in values]
        extracted_data[tag] = values
    
    # Check if correspondence is required for this config
    correspondence_required = False
    correspondence_tags = []
    require_all_match = True
    
    if correspondence_groups:
        for group in correspondence_groups:
            if group.get('type') == 'simple':
                # For simple tags, we don't use config_index, just check if any of the tags match
                group_tags = group.get('tags', [])
                if any(tag in tags for tag in group_tags):
                    correspondence_required = True
                    correspondence_tags = [tag for tag in group_tags if tag in tags]
                    require_all_match = group.get('require_all_match', True)
                    break
    
    # Get tag lengths for correspondence check
    if correspondence_required and correspondence_tags:
        # Only check specified tags for correspondence
        correspondence_lengths = []
        for tag in correspondence_tags:
            if tag in extracted_data:
                correspondence_lengths.append(len(extracted_data[tag]))
        
        if correspondence_lengths and len(set(correspondence_lengths)) > 1:
            if require_all_match:
                print(f"ERROR: Correspondence tag count mismatch for tags {correspondence_tags}")
                print(f"Tag lengths: {dict(zip(correspondence_tags, correspondence_lengths))}")
                return []
            else:
                print(f"WARNING: Correspondence tag count mismatch for tags {correspondence_tags}")
                print(f"Tag lengths: {dict(zip(correspondence_tags, correspondence_lengths))}")
                print("Proceeding with flexible extraction (require_all_match=False)")
    
    rows = []
    tag_lengths = [len(extracted_data[tag]) for tag in tags]
    
    if correspondence_required and correspondence_tags and require_all_match:
        # Correspondence approach for specified tags
        correspondence_count = min([len(extracted_data[tag]) for tag in correspondence_tags 
                                   if tag in extracted_data])
        
        # Handle rolling futures
        rolling_future_flags = None
        if rolling_futures and rolling_futures_tag and rolling_futures_tag in extracted_data:
            tag_values = extracted_data[rolling_futures_tag]
            rolling_future_flags = ['Yes' if value in rolling_futures else 'No' 
                                  for value in tag_values[:correspondence_count]]
        
        for i in range(correspondence_count):
            row_data = {'index_name': index_name}
            
            for tag in tags:
                if i < len(extracted_data[tag]):
                    row_data[tag] = extracted_data[tag][i]
                else:
                    row_data[tag] = None
            
            if rolling_future_flags:
                row_data['RollingFuture'] = rolling_future_flags[i]
            
            rows.append(row_data)
    else:
        # Flexible approach - separate rows for each tag-value pair
        for tag in tags:
            for value in extracted_data[tag]:
                row_data = {
                    'index_name': index_name,
                    'tag_name': tag,
                    'tag_value': value
                }
                
                if rolling_futures and value in rolling_futures:
                    row_data['RollingFuture'] = 'Yes'
                elif rolling_futures:
                    row_data['RollingFuture'] = 'No'
                
                rows.append(row_data)
    
    return rows


def _extract_nested_tags(
    content: str, 
    config: Dict[str, Any], 
    index_name: str,
    correspondence_groups: Optional[List[Dict[str, Any]]],
    config_idx: int
) -> List[Dict[str, Any]]:
    """Extract data from nested XML tags."""
    parent_tag = config['parent_tag']
    output_columns = config.get('output_columns', [])
    
    # Check if this is pattern-based extraction or direct nested tag extraction
    use_pattern = 'id_pattern' in config and config['id_pattern']
    
    # Check if correspondence is required for this nested config
    correspondence_required = False
    correspondence_tags = []
    require_all_match = True
    
    if correspondence_groups:
        for group in correspondence_groups:
            if (group.get('type') == 'nested' and 
                group.get('config_index', 0) == config_idx):
                correspondence_required = True
                correspondence_tags = group.get('tags', [])
                require_all_match = group.get('require_all_match', True)
                break
    
    rows = []
    
    # Find all parent tag sections
    parent_pattern = f'<{parent_tag}>(.*?)</{parent_tag}>'
    sections = re.findall(parent_pattern, content, re.DOTALL)
    
    print(f" Found {len(sections)} {parent_tag} sections")
    
    if use_pattern:
        # Pattern-based extraction (original DivRhoFlat approach)
        id_pattern = config['id_pattern']
        id_tag = config.get('id_tag', 'Id')
        value_tag = config.get('value_tag', 'Value')
        
        for i, section in enumerate(sections):
            # Extract ID using the provided pattern
            id_match = re.search(id_pattern, section)
            
            # Extract value
            value_pattern = f'<{value_tag}>([^<]+)</{value_tag}>'
            value_match = re.search(value_pattern, section)
            
            if id_match and value_match:
                extracted_id = id_match.group(1).strip()
                extracted_value = value_match.group(1).strip()
                
                row_data = {'index_name': index_name}
                
                # Use specified output column names
                if len(output_columns) >= 2:
                    row_data[output_columns[0]] = extracted_id
                    row_data[output_columns[1]] = extracted_value
                elif len(output_columns) == 1:
                    row_data[output_columns[0]] = f"{extracted_id}:{extracted_value}"
                else:
                    # Fallback to generic names if no output_columns specified
                    row_data['extracted_id'] = extracted_id
                    row_data['extracted_value'] = extracted_value
                
                rows.append(row_data)
                print(f" Section {i+1}: Found '{extracted_id}' with value '{extracted_value}'")
            else:
                print(f" Section {i+1}: Missing data - Id match: {bool(id_match)}, Value match: {bool(value_match)}")
    
    else:
        # Direct nested tag extraction
        nested_tags = config.get('nested_tags', [])
        
        if not nested_tags:
            print(f"Warning: No 'nested_tags' specified for parent_tag '{parent_tag}'")
            return rows
        
        # For correspondence checking in nested tags
        if correspondence_required and correspondence_tags:
            # First pass: collect all extracted data to check correspondence
            all_section_data = []
            
            for i, section in enumerate(sections):
                section_data = {}
                for nested_tag in nested_tags:
                    tag_pattern = f'<{nested_tag}>([^<]*)</{nested_tag}>'
                    tag_matches = re.findall(tag_pattern, section)
                    section_data[nested_tag] = [match.strip() for match in tag_matches]
                all_section_data.append(section_data)
            
            # Check correspondence for specified tags
            correspondence_counts = []
            for section_data in all_section_data:
                section_counts = []
                for tag in correspondence_tags:
                    if tag in section_data:
                        section_counts.append(len(section_data[tag]))
                if section_counts:
                    correspondence_counts.append(section_counts)
            
            # Validate correspondence
            correspondence_valid = True
            for i, section_counts in enumerate(correspondence_counts):
                if len(set(section_counts)) > 1:
                    if require_all_match:
                        print(f"ERROR: Nested tag correspondence mismatch in section {i+1}")
                        print(f"Tag counts for {correspondence_tags}: {section_counts}")
                        correspondence_valid = False
                    else:
                        print(f"WARNING: Nested tag correspondence mismatch in section {i+1}")
                        print(f"Tag counts for {correspondence_tags}: {section_counts}")
            
            if not correspondence_valid and require_all_match:
                return rows
            
            # Extract with correspondence
            for i, (section, section_data) in enumerate(zip(sections, all_section_data)):
                if correspondence_tags and require_all_match:
                    # Use correspondence approach
                    correspondence_count = min([len(section_data[tag]) for tag in correspondence_tags 
                                              if tag in section_data])
                    
                    for j in range(correspondence_count):
                        row_data = {'index_name': index_name}
                        
                        # Map extracted values to specified output column names
                        if output_columns:
                            for k, output_col in enumerate(output_columns):
                                if k < len(nested_tags):
                                    nested_tag = nested_tags[k]
                                    if j < len(section_data.get(nested_tag, [])):
                                        row_data[output_col] = section_data[nested_tag][j]
                                    else:
                                        row_data[output_col] = None
                        else:
                            # Use nested_tags as column names
                            for nested_tag in nested_tags:
                                if j < len(section_data.get(nested_tag, [])):
                                    row_data[nested_tag] = section_data[nested_tag][j]
                                else:
                                    row_data[nested_tag] = None
                        
                        rows.append(row_data)
                else:
                    # Flexible approach - extract all data
                    for nested_tag in nested_tags:
                        for value in section_data.get(nested_tag, []):
                            row_data = {
                                'index_name': index_name,
                                'tag_name': nested_tag,
                                'tag_value': value
                            }
                            rows.append(row_data)
        else:
            # No correspondence checking - original flexible approach
            for i, section in enumerate(sections):
                row_data = {'index_name': index_name}
                extracted_values = {}
                
                # Extract each nested tag directly
                for nested_tag in nested_tags:
                    tag_pattern = f'<{nested_tag}>([^<]*)</{nested_tag}>'
                    tag_match = re.search(tag_pattern, section)
                    
                    if tag_match:
                        extracted_value = tag_match.group(1).strip()
                        extracted_values[nested_tag] = extracted_value
                    else:
                        extracted_values[nested_tag] = None
                        print(f" Section {i+1}: No {nested_tag} found")
                
                # Map extracted values to specified output column names
                if output_columns:
                    for j, output_col in enumerate(output_columns):
                        if j < len(nested_tags):
                            nested_tag = nested_tags[j]
                            row_data[output_col] = extracted_values.get(nested_tag)
                        else:
                            row_data[output_col] = None
                else:
                    # If no output_columns specified, use nested_tags as column names
                    for nested_tag in nested_tags:
                        row_data[nested_tag] = extracted_values.get(nested_tag)
                
                # Only add row if at least one value was found
                if any(v is not None for v in extracted_values.values()):
                    rows.append(row_data)
                    extracted_count = len([v for v in extracted_values.values() if v is not None])
                    print(f" Section {i+1}: Extracted {extracted_count} values")
                else:
                    print(f" Section {i+1}: No valid data found")
    
    return rows


def _filter_nonzero_values(data_rows: List[Dict[str, Any]], filter_tags: List[str]) -> List[Dict[str, Any]]:
    """Filter out rows where specified tags have zero or empty values."""
    filtered_rows = []
    
    for row in data_rows:
        keep_row = True
        
        for tag in filter_tags:
            if tag in row:
                value = row[tag]
                # Check if value is zero, empty, or None
                if value is None or value == '' or value == '0' or value == 0:
                    keep_row = False
                    break
                # Handle string representations of zero
                try:
                    if float(value) == 0:
                        keep_row = False
                        break
                except (ValueError, TypeError):
                    # If conversion fails, keep the row (non-numeric data)
                    pass
        
        if keep_row:
            filtered_rows.append(row)
    
    return filtered_rows


# Example usage and helper function for easy migration from old functions
def extract_xml_data_to_dataframe_legacy(**kwargs):
    """Legacy wrapper for backward compatibility."""
    # Convert old parameters to new format
    xml_tags = kwargs.get('xml_tags_to_extract', [])
    config = [{'type': 'simple', 'tags': xml_tags}]
    
    # Map old parameters to new ones
    new_kwargs = {
        'directory_path': kwargs.get('directory_path'),
        'extraction_config': config,
        'file_name_pattern': kwargs.get('file_name_pattern', 'sorted_*.xml'),
        'index_name_pattern': kwargs.get('index_name_pattern', r'sorted_([^_-]+)'),
        'rolling_futures': kwargs.get('rolling_futures'),
        'rolling_futures_tag': xml_tags[0] if xml_tags else None,
        'correspondence_groups': [{'type': 'simple', 'tags': xml_tags, 'require_all_match': kwargs.get('require_matching_counts', True)}] if kwargs.get('require_matching_counts', True) else None,
        'save_to_csv': kwargs.get('save_to_csv', False),
        'csv_save_directory': kwargs.get('csv_save_directory'),
        'csv_filename': kwargs.get('csv_filename')
    }
    
    return extract_xml_data_comprehensive(**new_kwargs)


def extract_DivRhoFlat_data_legacy(**kwargs):
    """Legacy wrapper for backward compatibility."""
    xml_tags = kwargs.get('xml_tags_to_extract', ['DivRhoFlat'])
    
    config = [{
        'type': 'nested',
        'parent_tag': xml_tags[0],
        'id_pattern': r'DivRhoFlat_BumpYieldAsGrowthSpread_Annualized_([^<]+)',
        'id_tag': 'Id',
        'value_tag': 'Value',
        'output_columns': ['Asset_Name', 'GSRisk_Value']
    }]
    
    new_kwargs = {
        'directory_path': kwargs.get('directory_path'),
        'extraction_config': config,
        'file_name_pattern': kwargs.get('file_name_pattern', '*_output.xml'),
        'index_name_pattern': kwargs.get('index_name_pattern', r'(.+)_output\.xml$'),
        'save_to_csv': kwargs.get('save_to_csv', False),
        'csv_save_directory': kwargs.get('csv_save_directory'),
        'csv_filename': kwargs.get('csv_filename')
    }
    
    return extract_xml_data_comprehensive(**new_kwargs)









#########################################
########## Extract Excel Infos ##########
#########################################

import pandas as pd
import os
from pathlib import Path
import numpy as np

# Check for required dependencies
try:
    import openpyxl
except ImportError:
    print("Warning: openpyxl not installed. Install with: pip install openpyxl")
    print("This is required for reading .xlsx and .xlsm files")

try:
    import xlrd
except ImportError:
    print("Info: xlrd not installed. Install with: pip install xlrd (for .xls files)")

try:
    import pyxlsb
except ImportError:
    print("Info: pyxlsb not installed. Install with: pip install pyxlsb (for .xlsb files)")

def extract_excel_data(directory_path, sheet_name, field_names, value_columns, field_column_name="Field"):
    """
    Extract data from Excel files in a directory based on field names and specified columns.
    Handles hierarchical Excel sheets with collapsed/grouped rows.
    
    Parameters:
    directory_path (str): Path to the directory containing Excel files
    sheet_name (str): Name of the sheet to search in
    field_names (list): List of field names to search for in the field column
    value_columns (dict): Dictionary mapping column labels to actual column names
                         e.g., {'gnu1': 'GNU 1 ($)', 'gnu2': 'GNU 2 ($)', 'gnu_diff': 'GNU diff ($)'}
    field_column_name (str): Name of the column containing field names (default: "Field")
    
    Returns:
    pandas.DataFrame: DataFrame with extracted data
    """
    
    # Initialize list to store results
    results = []
    
    # Get all Excel files in the directory
    directory = Path(directory_path)
    excel_files = list(directory.glob("*.xlsx")) + list(directory.glob("*.xlsm")) + list(directory.glob("*.csv"))
    
    if not excel_files:
        print(f"No Excel files found in {directory_path}")
        return pd.DataFrame()
    
    for file_path in excel_files:
        try:
            print(f"Processing file: {file_path.name}")
            
            # Get filename without extension
            filename = file_path.stem
            
            # Read the Excel file - read all data to handle hierarchical structure
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            else:
                # Read without header to get the raw structure
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            
            print(f"  Sheet shape: {df.shape}")
            
            # Find the header row that contains "Field" 
            field_header_row = None
            field_col_index = None
            
            for idx, row in df.iterrows():
                for col_idx, cell_value in enumerate(row):
                    if str(cell_value).strip() == "Field":
                        field_header_row = idx
                        field_col_index = col_idx
                        break
                if field_header_row is not None:
                    break
            
            if field_header_row is None:
                print(f"  Could not find 'Field' header in {filename}")
                continue
                
            print(f"  Found 'Field' header at row {field_header_row}, column {field_col_index}")
            
            # Set the header row and get column names
            df.columns = df.iloc[field_header_row]
            df = df.iloc[field_header_row + 1:].reset_index(drop=True)
            
            # Clean column names
            df.columns = [str(col).strip() if pd.notna(col) else f"Unnamed_{i}" for i, col in enumerate(df.columns)]
            
            print(f"  Available columns after processing: {list(df.columns)}")
            
            # Check if required columns exist
            required_cols = list(value_columns.values())
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                print(f"Warning: Missing columns in {filename}: {missing_cols}")
                print(f"Available columns: {list(df.columns)}")
                continue
            
            # Search for each field name - look for exact matches 
            for field_name in field_names:
                # Find rows where the Field column exactly matches the field name
                field_col = df.columns[field_col_index] if field_col_index < len(df.columns) else "Field"
                matching_rows = df[df[field_col].astype(str).str.strip() == field_name]
                
                if not matching_rows.empty:
                    for _, row in matching_rows.iterrows():
                        # Check if the row has actual values (not NaN/empty)
                        has_values = True
                        row_values = {}
                        
                        for col_key, col_name in value_columns.items():
                            if col_name in df.columns:
                                value = row[col_name]
                                if pd.isna(value) or str(value).strip() == '':
                                    has_values = False
                                    break
                                row_values[col_key] = value
                            else:
                                print(f"  Warning: Column '{col_name}' not found")
                                has_values = False
                                break
                        
                        if has_values:
                            result = {
                                'filename': filename,
                                'field_name': row[field_col],
                            }
                            
                            # Add values for each specified column
                            for col_key, value in row_values.items():
                                result[f'{col_key}_value'] = value
                            
                            results.append(result)
                            
                            # Print extracted values
                            value_str = ", ".join([f"{col_key}={value}" for col_key, value in row_values.items()])
                            print(f"  Found {field_name}: {value_str}")
                        else:
                            print(f"  Found {field_name} but no valid values in data columns")
                else:
                    print(f"  Field '{field_name}' not found in {filename}")
                    # Debug: show what field names are actually available
                    if field_col_index < len(df.columns):
                        available_fields = df[df.columns[field_col_index]].dropna().astype(str).str.strip()
                        available_fields = available_fields[available_fields != ''].unique()[:10]  # Show first 10
                        print(f"  Available field names (sample): {list(available_fields)}")
        
        except Exception as e:
            print(f"Error processing {file_path.name}: {str(e)}")
            continue
    
    # Create DataFrame from results
    if results:
        result_df = pd.DataFrame(results)
        return result_df
    else:
        print("No data extracted from any files")
        return pd.DataFrame()

def clean_numeric_values(df, numeric_columns=None):
    """
    Clean numeric values by removing commas and converting to float.
    
    Parameters:
    df (pandas.DataFrame): DataFrame to clean
    numeric_columns (list): List of column names to clean. If None, will clean all columns ending with '_value'
    
    Returns:
    pandas.DataFrame: DataFrame with cleaned numeric values
    """
    df_cleaned = df.copy()
    
    if numeric_columns is None:
        # Auto-detect value columns
        numeric_columns = [col for col in df_cleaned.columns if col.endswith('_value')]
    
    for col in numeric_columns:
        if col in df_cleaned.columns:
            # Convert to string, remove commas, then convert to float
            df_cleaned[col] = df_cleaned[col].astype(str).str.replace(',', '').astype(float)
    
    return df_cleaned

# Example usage
if __name__ == "__main__":
    # Configuration parameters based on your Excel screenshot
    DIRECTORY_PATH = "/path/to/your/excel/files"  # Update this path
    SHEET_NAME = "Sheet1"  # Update with your sheet name
    
    # Field names from your screenshot (these are the collapsed/parent rows)
    FIELD_NAMES = [
        "PosCcyDelta", 
        "PosCcyDelta_TPlusN", 
        "PosKappa", 
        "PosKappaSkewPlus", 
        "PosTV", 
        "PosRho", 
        "P&L"
    ]
    
    # Column mapping based on your Excel structure
    VALUE_COLUMNS = {
        'gnu1': 'GNU 1 ($)',      # Column D
        'gnu2': 'GNU 2 ($)',      # Column E  
        'gnu_diff': 'GNU diff ($)' # Column F
    }
    
    # Field column name from your screenshot  
    FIELD_COLUMN_NAME = "Field"  # This should be Column C based on your Excel structure
    
    # Extract data
    extracted_data = extract_excel_data(
        directory_path=DIRECTORY_PATH,
        sheet_name=SHEET_NAME,
        field_names=FIELD_NAMES,
        value_columns=VALUE_COLUMNS,
        field_column_name=FIELD_COLUMN_NAME
    )
    
    if not extracted_data.empty:
        # Clean numeric values
        cleaned_data = clean_numeric_values(extracted_data)
        
        # Display results
        print("\nExtracted Data:")
        print(cleaned_data)
        
        # Save to CSV if needed
        output_file = "extracted_data.csv"
        cleaned_data.to_csv(output_file, index=False)
        print(f"\nData saved to {output_file}")
        
        # Optional: Display summary statistics
        print("\nSummary Statistics:")
        numeric_cols = [col for col in cleaned_data.columns if col.endswith('_value')]
        for col in numeric_cols:
            if col in cleaned_data.columns:
                print(f"{col}:")
                print(f"  Mean: {cleaned_data[col].mean():.2f}")
                print(f"  Std:  {cleaned_data[col].std():.2f}")
                print(f"  Min:  {cleaned_data[col].min():.2f}")
                print(f"  Max:  {cleaned_data[col].max():.2f}")
    else:
        print("No data was extracted.")

# Alternative function for more flexible column matching
def extract_excel_data_flexible(directory_path, sheet_name, field_names, column_patterns=None):
    """
    More flexible version that can handle variations in column names.
    
    Parameters:
    directory_path (str): Path to the directory containing Excel files
    sheet_name (str): Name of the sheet to search in
    field_names (list): List of field names to search for
    column_patterns (dict): Dictionary mapping standard names to possible column name patterns
                           e.g., {'gnu1': ['GNU 1', 'GNU1', 'GNU 1 ($)'], 'gnu2': ['GNU 2', 'GNU2', 'GNU 2 ($)']}
    """
    
    if column_patterns is None:
        column_patterns = {
            'gnu1': ['GNU 1 ($)', 'GNU 1', 'GNU1'],
            'gnu2': ['GNU 2 ($)', 'GNU 2', 'GNU2'],
            'gnu_diff': ['GNU diff ($)', 'GNU diff', 'GNU_diff', 'Diff']
        }
    
    results = []
    directory = Path(directory_path)
    excel_files = list(directory.glob("*.xlsx")) + list(directory.glob("*.xlsm")) + list(directory.glob("*.csv"))
    
    for file_path in excel_files:
        try:
            filename = file_path.stem
            
            # Read file
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Find matching columns
            col_mapping = {}
            for standard_name, patterns in column_patterns.items():
                for pattern in patterns:
                    matching_cols = [col for col in df.columns if pattern in col]
                    if matching_cols:
                        col_mapping[standard_name] = matching_cols[0]
                        break
            
            if 'gnu1' not in col_mapping or 'gnu2' not in col_mapping:
                print(f"Required columns not found in {filename}")
                continue
            
            # Search for field names
            for field_name in field_names:
                matching_rows = df[df['Field'].str.contains(field_name, case=False, na=False)]
                
                for _, row in matching_rows.iterrows():
                    result = {
                        'filename': filename,
                        'field_name': row['Field'],
                        'gnu1_value': row[col_mapping['gnu1']],
                        'gnu2_value': row[col_mapping['gnu2']],
                    }
                    
                    if 'gnu_diff' in col_mapping:
                        result['gnu_diff_value'] = row[col_mapping['gnu_diff']]
                    
                    results.append(result)
        
        except Exception as e:
            print(f"Error processing {file_path.name}: {str(e)}")
    
    return pd.DataFrame(results) if results else pd.DataFrame()