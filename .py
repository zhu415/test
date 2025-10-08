def format_number_k(value):
    """
    Format number to k/M notation with sign.
    Examples: 35531.56 -> +35k, -74206.05 -> -74k, 1500000 -> +1.5M
    """
    if pd.isna(value):
        return ''
    
    # Convert to float if it's a string with commas
    if isinstance(value, str):
        value = float(value.replace(',', ''))
    
    sign = '+' if value >= 0 else ''
    abs_value = abs(value)
    
    if abs_value >= 1_000_000:
        formatted = f"{sign}{value/1_000_000:.0f}M"
    elif abs_value >= 1_000:
        formatted = f"{sign}{value/1_000:.0f}k"
    else:
        formatted = f"{sign}{value:.0f}"
    
    return formatted
