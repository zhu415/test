 print(f"  df2 dates in interval:")
            print(f"    - {left_date} (ratio: {current_ratio:.3f}) [LEFT ENDPOINT]")
            
            if len(dates_in_interval) > 0:
                for date in dates_in_interval:
                    ratio_value = df2_sorted.loc[df2_sorted[date_col] == date, ratio_col].iloc[0]
                    print(f"    - {date} (ratio: {ratio_value:.3f}) [INTERMEDIATE]")
            else:
                print(f"    (No intermediate df2 dates)")
            
            print(f"    - {right_date} (ratio: {df2_sorted.loc[next_idx, ratio_col]:.3f}) [RIGHT ENDPOINT]")
