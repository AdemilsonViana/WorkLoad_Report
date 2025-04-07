import pandas as pd

def format_time(td):
    if isinstance(td, pd.Timedelta):
        total_hours = td.total_seconds() / 3600
    else:
        total_hours = td
    hours = int(total_hours)
    minutes = int((total_hours - hours) * 60)
    return f"{hours}h {minutes}min"