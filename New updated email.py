import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import io

def process_and_email_breaches(
    results: Dict,
    wesByIndex: Dict[str, Dict[str, pd.DataFrame]],
    mapping_csv_path: str,
    email_config: Dict,
    bm_key: str = 'continuous bm',
    save_excel: bool = True,
    excel_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Process breach results to find most recent breaches per index and send email notification.
    
    Parameters:
    -----------
    results : Dict
        Results from compare_index_data function
    wesByIndex : Dict
        Original data dictionary
    mapping_csv_path : str
        Path to CSV file containing asset class mappings
    email_config : Dict
        Email configuration with keys: 'smtp_server', 'smtp_port', 'sender', 'password', 'recipients'
    bm_key : str
        Key for benchmark data
    save_excel : bool
        Whether to save and attach Excel file
    excel_path : Optional[str]
        Path to save Excel file
    
    Returns:
    --------
    pd.DataFrame: Summary table of most recent breaches
    """
    
    # Load mapping data
    mapping_df = pd.read_csv(mapping_csv_path)
    
    # Process breaches to find most recent per index
    breach_summary = find_most_recent_breaches(results)
    
    # Build detailed breach table
    detailed_table = build_detailed_breach_table(
        breach_summary, wesByIndex, mapping_df, bm_key
    )
    
    # Send email
    send_breach_email(
        detailed_table, 
        email_config, 
        save_excel, 
        excel_path
    )
    
    return detailed_table


def find_most_recent_breaches(results: Dict) -> Dict[str, Dict]:
    """
    Find all breaches on the most recent breach date for each index.
    """
    index_breaches = {}
    
    # First pass: find the most recent breach date for each index
    for breach_type, breaches in results.items():
        for breach in breaches:
            index_name = breach['index']
            comp_date = breach['comp_date']
            
            if index_name not in index_breaches:
                index_breaches[index_name] = {
                    'most_recent_date': comp_date,
                    'breaches': []
                }
            else:
                # Update most recent date if this is more recent
                if comp_date > index_breaches[index_name]['most_recent_date']:
                    index_breaches[index_name]['most_recent_date'] = comp_date
                    index_breaches[index_name]['breaches'] = []
    
    # Second pass: collect all breaches that match the most recent date for each index
    for breach_type, breaches in results.items():
        for breach in breaches:
            index_name = breach['index']
            comp_date = breach['comp_date']
            
            if index_name in index_breaches:
                if comp_date == index_breaches[index_name]['most_recent_date']:
                    index_breaches[index_name]['breaches'].append({
                        'breach': breach,
                        'breach_type': breach_type
                    })
    
    return index_breaches


def build_detailed_breach_table(
    breach_summary: Dict[str, Dict],
    wesByIndex: Dict,
    mapping_df: pd.DataFrame,
    bm_key: str
) -> pd.DataFrame:
    """
    Build detailed table with constituent weights and asset types.
    Include all breaches on the most recent date for each index.
    """
    detailed_records = []
    
    for index_name, breach_data in breach_summary.items():
        breaches_list = breach_data['breaches']
        
        if not breaches_list:
            continue
            
        # Get the DataFrame for this index
        df = wesByIndex[bm_key][index_name]
        
        # Use the first breach to get common information (dates will be the same)
        first_breach = breaches_list[0]['breach']
        ref_date = first_breach['ref_date']
        comp_date = first_breach['comp_date']
        
        # Get constituent information (same for all breaches on this date)
        constituent_info = extract_constituent_info(
            df, ref_date, comp_date, index_name, mapping_df
        )
        
        # Get borrow shift values (same for all breaches on this date)
        borrow_shift_info = extract_borrow_shift(df, ref_date, comp_date)
        
        # Combine all breach types and details
        breach_types = []
        breach_details = []
        
        for breach_item in breaches_list:
            breach = breach_item['breach']
            breach_type = breach_item['breach_type']
            
            breach_types.append(format_breach_type(breach_type))
            breach_details.append(format_breach_details(breach, breach_type))
        
        # Create record with all breaches
        record = {
            'Index': index_name,
            'Reference Date': ref_date,
            'Comparison Date': comp_date,
            'Breach Types': ' | '.join(breach_types),
            'Breach Details': ' | '.join(breach_details),
            **constituent_info,
            **borrow_shift_info
        }
        
        detailed_records.append(record)
    
    return pd.DataFrame(detailed_records)


def extract_constituent_info(
    df: pd.DataFrame, 
    ref_date: str, 
    comp_date: str,
    index_name: str,
    mapping_df: pd.DataFrame
) -> Dict:
    """
    Extract constituent weights and asset types for both dates.
    """
    result = {}
    
    # Get constituent rows
    constituent_rows = [idx for idx in df.index 
                       if isinstance(idx, tuple) and idx[0] == 'constituentId']
    
    # Get mapping for this index
    index_mapping = mapping_df[mapping_df['index'] == index_name]
    
    # Build constituent details
    constituents_ref = []
    constituents_comp = []
    
    for const_idx in constituent_rows:
        sub_index = const_idx[1]
        
        # Get asset class from mapping
        asset_class = 'Unknown'
        if not index_mapping.empty:
            underlier_match = index_mapping[index_mapping['underlier'] == sub_index]
            if not underlier_match.empty:
                asset_class = underlier_match.iloc[0]['asset class']
        
        # Get weights
        if ref_date in df.columns:
            ref_weight = df.loc[const_idx, ref_date]
            constituents_ref.append(f"{sub_index} ({asset_class}): {ref_weight:.4f}")
        
        if comp_date in df.columns:
            comp_weight = df.loc[const_idx, comp_date]
            constituents_comp.append(f"{sub_index} ({asset_class}): {comp_weight:.4f}")
    
    result['Constituents (Ref Date)'] = '; '.join(constituents_ref)
    result['Constituents (Comp Date)'] = '; '.join(constituents_comp)
    
    return result


def extract_borrow_shift(df: pd.DataFrame, ref_date: str, comp_date: str) -> Dict:
    """
    Extract borrow shift values for all tenors.
    """
    result = {}
    tenors = ['6m', '1y', '2y']
    
    for tenor in tenors:
        idx = ('Borrow Shift', tenor)
        
        ref_val = 'N/A'
        comp_val = 'N/A'
        
        if idx in df.index:
            if ref_date in df.columns:
                ref_val = f"{df.loc[idx, ref_date]:.4f}"
            if comp_date in df.columns:
                comp_val = f"{df.loc[idx, comp_date]:.4f}"
        
        result[f'Borrow Shift {tenor} (Ref)'] = ref_val
        result[f'Borrow Shift {tenor} (Comp)'] = comp_val
    
    return result


def format_breach_type(breach_type: str) -> str:
    """
    Format breach type for display.
    """
    type_mapping = {
        'rf_breaches': 'Rolling Futures',
        'asset_class_breaches': 'Asset Class',
        'full_gs_breaches': 'Full GS',
        'borrow_shift_breaches': 'Borrow Shift'
    }
    return type_mapping.get(breach_type, breach_type)


def format_breach_details(breach: Dict, breach_type: str) -> str:
    """
    Format breach details for display.
    """
    if breach_type == 'rf_breaches':
        return f"RF Type: {breach.get('rf_type', 'N/A')}, Diff: {breach.get('difference_pct', 0):.2f}%"
    elif breach_type == 'asset_class_breaches':
        return f"Asset: {breach.get('asset_class', 'N/A')}, Diff: {breach.get('difference_pct', 0):.2f}%"
    elif breach_type == 'full_gs_breaches':
        return f"Tenor: {breach.get('tenor', 'N/A')}, Diff: {breach.get('difference_bps', 0):.2f} bps"
    elif breach_type == 'borrow_shift_breaches':
        return f"Tenor: {breach.get('tenor', 'N/A')}, Diff: {breach.get('difference_bps', 0):.2f} bps"
    return "N/A"


def send_breach_email(
    detailed_table: pd.DataFrame,
    email_config: Dict,
    save_excel: bool = True,
    excel_path: Optional[str] = None
):
    """
    Send email with breach summary table using company SMTP server.
    
    email_config should contain:
    - smtp_server: SMTP server address (default: 'meta-hub')
    - smtp_port: SMTP port (default: 25)
    - sender: Sender email address
    - recipients: List of recipient email addresses
    - use_auth: Whether to use authentication (default: False for internal servers)
    - password: Sender password (only needed if use_auth=True)
    """
    
    # Set defaults for company configuration
    smtp_server = email_config.get('smtp_server', 'meta-hub')
    smtp_port = email_config.get('smtp_port', 25)
    use_auth = email_config.get('use_auth', False)
    
    # Create message
    msg = MIMEMultipart()
    msg['Subject'] = f"Index Breach Alert - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
    msg['From'] = email_config['sender']
    msg['To'] = ', '.join(email_config['recipients'])
    
    # Add CC if provided
    if 'cc' in email_config:
        msg['Cc'] = ', '.join(email_config['cc'])
    
    # Create HTML content
    html_content = create_html_email_content(detailed_table)
    
    # Attach HTML
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)
    
    # Attach Excel file if requested
    if save_excel:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            detailed_table.to_excel(writer, sheet_name='Breach Summary', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Breach Summary']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Save to file if path provided
        if excel_path:
            with open(excel_path, 'wb') as f:
                f.write(excel_buffer.getvalue())
        
        # Attach to email
        excel_buffer.seek(0)
        excel_part = MIMEBase('application', 'octet-stream')
        excel_part.set_payload(excel_buffer.read())
        encoders.encode_base64(excel_part)
        excel_part.add_header(
            'Content-Disposition',
            f'attachment; filename="breach_summary_{datetime.datetime.now().strftime("%Y%m%d")}.xlsx"'
        )
        msg.attach(excel_part)
    
    # Send email using company SMTP configuration
    try:
        smtp = smtplib.SMTP()
        smtp.connect(smtp_server, smtp_port)
        
        # Only use authentication if specified
        if use_auth and 'password' in email_config:
            smtp.starttls()
            smtp.login(email_config['sender'], email_config['password'])
        
        # Get all recipients (To + Cc)
        all_recipients = email_config['recipients'].copy()
        if 'cc' in email_config:
            all_recipients.extend(email_config['cc'])
        
        # Send email
        smtp.sendmail(msg['From'], all_recipients, msg.as_string())
        smtp.quit()
        
        print(f"✅ Email sent successfully to {', '.join(all_recipients)}")
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        raise


def create_html_email_content(df: pd.DataFrame) -> str:
    """
    Create HTML content for email.
    """
    # Count total breaches (some indices may have multiple breaches)
    total_breaches = df['Breach Types'].str.count('\|').sum() + len(df)
    
    # Convert DataFrame to HTML with simple styling
    table_html = df.to_html(index=False, escape=False)
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            h2 {{ color: #2c3e50; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th {{ background-color: #3498db; color: white; padding: 12px; text-align: left; }}
            td {{ padding: 10px; border-bottom: 1px solid #ddd; font-size: 12px; }}
            tr:hover {{ background-color: #f5f5f5; }}
            .alert {{ color: #e74c3c; font-weight: bold; }}
            .summary {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            .breach-types {{ color: #e74c3c; font-weight: bold; }}
            .multiple-breaches {{ background-color: #fff3cd; }}
        </style>
    </head>
    <body>
        <h2>Index Breach Alert Report</h2>
        <div class="summary">
            <p><strong>Report Generated:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Total Indices with Breaches:</strong> {len(df)}</p>
            <p><strong>Total Breaches Detected:</strong> {total_breaches}</p>
        </div>
        
        <h3>Breach Details (Most Recent Date per Index)</h3>
        <p><em>Note: Indices may have multiple breaches on the same date, all shown with "|" separator</em></p>
        {table_html}
        
        <div style="margin-top: 30px; padding: 10px; background-color: #f8f9fa; border-left: 4px solid #3498db;">
            <p><small>This is an automated alert. Multiple breaches on the same date are shown together for each index.</small></p>
            <p><small>For questions, please contact the Risk Management team.</small></p>
        </div>
    </body>
    </html>
    """
    
    return html


# Example usage
if __name__ == "__main__":
    # Example email configuration for company internal SMTP
    email_config = {
        'smtp_server': 'meta-hub',  # Company's internal SMTP server
        'smtp_port': 25,  # Standard SMTP port
        'sender': 'risk.alerts@yourcompany.com',
        'recipients': ['analyst1@yourcompany.com', 'risk.team@yourcompany.com'],
        'cc': ['manager@yourcompany.com'],  # Optional CC recipients
        'use_auth': False  # No authentication needed for internal server
    }
    
    # For external SMTP servers (Gmail, Outlook) that require authentication:
    # email_config = {
    #     'smtp_server': 'smtp.gmail.com',
    #     'smtp_port': 587,
    #     'sender': 'alerts@gmail.com',
    #     'password': 'app_password',
    #     'recipients': ['recipient@example.com'],
    #     'use_auth': True
    # }
    
    # Process and send email
    # detailed_table = process_and_email_breaches(
    #     results=results_from_compare_function,
    #     wesByIndex=your_data,
    #     mapping_csv_path="mapping.csv",
    #     email_config=email_config,
    #     save_excel=True,
    #     excel_path="breach_summary.xlsx"
    # )
