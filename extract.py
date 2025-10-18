import pandas as pd 
from pathlib import Path

def extract_data(filepath):
    df = pd.read_csv(filepath)
    print("Raw data:")
    print(df.head())
    return df

def list_incoming_files(incoming_dir='Incoming-data'):
    p = Path(incoming_dir)
    return sorted([f for f in Path(incoming_dir).iterdir() if f.is_file() and f.suffix.lower() == '.csv'])

def read_file(path):
    return pd.read_csv(path)

