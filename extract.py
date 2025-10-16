import pandas as pd 
from pathlib import Path

def extract_data(filepath):
    df = pd.read_csv(filepath)
    print("Raw data:")
    print(df.head())
    return df

def list_incoming_files(incoming_dir='Incoming-data'):
    """List all CSV and JSON files in incoming directory"""
    p = Path(incoming_dir)
    files = []
    for f in p.iterdir():
        if f.is_file() and f.suffix.lower() in ['.csv', '.json']:
            files.append(f)
    return sorted(files)

def read_file(path):
    """Read CSV or JSON file and return DataFrame"""
    suffix = path.suffix.lower()
    
    if suffix == '.csv':
        return pd.read_csv(path)
    
    elif suffix == '.json':
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            # Array of objects
            return pd.DataFrame(data)
        elif isinstance(data, dict):
            # Check if it's a wrapped structure like {"data": [...]}
            if 'data' in data and isinstance(data['data'], list):
                return pd.DataFrame(data['data'])
            elif 'products' in data and isinstance(data['products'], list):
                return pd.DataFrame(data['products'])
            else:
                # Single object - convert to single-row DataFrame
                return pd.DataFrame([data])
        else:
            raise ValueError(f"Unsupported JSON structure in {path}")
    
    else:
        raise ValueError(f"Unsupported file type: {suffix}")





    