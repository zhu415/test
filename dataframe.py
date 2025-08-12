 validation_results = []
    
    for date in df['date'].unique():
        date_data = df[df['date'] == date].copy()
        
        # Calculate price_per_share * number_of_shares for each row
        date_data['calculated_value'] = date_data['price_per_share'] * date_data['number_of_shares']
        
        # Sum the calculated values (excluding NaN)
        calculated_sum = date_data['calculated_value'].sum()
        
        # Get the fee_price (should be the same for all rows in this date)
        fee_price = date_data['fee_price'].iloc[0] if not date_data['fee_price'].isna().all() else np.nan
        
        # Check if they are equal within tolerance
        if pd.isna(calculated_sum) or pd.isna(fee_price):
            is_equal = False
            difference = np.nan
        else:
            difference = abs(calculated_sum - fee_price)
            is_equal = difference <= tolerance
        
        validation_results.append({
            'date': date,
            'calculated_sum': calculated_sum,
            'fee_price': fee_price,
            'difference': difference,
            'is_equal_within_tolerance': is_equal,
            'tolerance_used': tolerance
        })
    
    validation_df = pd.DataFrame(validation_results)
