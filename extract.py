import pandas as pd 
def extract_data(filepath):
    df = pd.read_csv(filepath)
    print("Raw data:")
    print(df.head())
    return df









    