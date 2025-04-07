import pandas as pd

def format_time(td):
    if isinstance(td, pd.Timedelta):
        total_hours = td.total_seconds() / 3600
    else:
        total_hours = td
    hours = int(total_hours)
    minutes = int((total_hours - hours) * 60)
    return f"{hours}h {minutes}min"

def process_dataframe(df, tipo):
    df = df[['properties']]
    df = pd.json_normalize(df['properties'])
    df = df[['Date.date.start', 'Date.date.end']]
    df.rename(columns={'Date.date.start': 'dt_start', 'Date.date.end': 'dt_end'}, inplace=True)
    
    df['dt_start'] = pd.to_datetime(df['dt_start'])
    df['dt_end'] = pd.to_datetime(df['dt_end'])
    df['duration'] = (df['dt_end'] - df['dt_start']).dt.total_seconds() / 3600
    
    df['type'] = tipo
    df['date'] = df['dt_start'].dt.strftime('%d/%m/%Y')
    df['year'] = df['dt_start'].dt.year
    df['month'] = df['dt_start'].dt.month
    df['week'] = df['dt_start'].dt.isocalendar().week
    df['weekday'] = df['dt_start'].dt.dayofweek + 1
    
    return df 