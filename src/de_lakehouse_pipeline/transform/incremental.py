def filter_new_rows(rows, last_watermark):
    if last_watermark:
        new_rows = [row for row in rows if row[0] > last_watermark]
    else:
        new_rows  = rows
        
    return new_rows
    
    
def get_max_timestamp(rows):
    if not rows:
        return None
    return max(row[0] for row in rows)

