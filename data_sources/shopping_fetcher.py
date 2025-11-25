"""
Dataset: https://www.kaggle.com/datasets/bhadramohit/customer-shopping-latest-trends-dataset
"""

import pandas as pd
from pathlib import Path
from typing import Optional
import json


class ShoppingTrendsFetcher:

    def __init__(self, cache_dir: Path = Path("external_data_cache")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        self.dataset_name = "shopping_trends"
        
 
        self.expected_columns = [
            'Customer ID', 'Age', 'Gender', 'Item Purchased', 'Category',
            'Purchase Amount (USD)', 'Location', 'Size', 'Color', 'Season',
            'Review Rating', 'Subscription Status', 'Payment Method',
            'Shipping Type', 'Discount Applied', 'Promo Code Used',
            'Previous Purchases', 'Preferred Payment Method', 'Frequency of Purchases'
        ]
    
    def fetch_shopping_trends(self, force_refresh: bool = False) -> pd.DataFrame:
      
        cache_file = self.cache_dir / f"{self.dataset_name}.csv"
        
     
        if not force_refresh and cache_file.exists():
            print(f"Loading shopping trends from cache: {cache_file}")
            df = pd.read_csv(cache_file)
            
            if self._validate_data(df):
                return df
        
      
        possible_names = [
            "shopping_trends.csv",
            "shopping_trends_updated.csv",
            "customer_shopping_data.csv",
            "Customer Shopping Dataset.csv"
        ]
        
        for filename in possible_names:
            manual_file = self.cache_dir / filename
            if manual_file.exists():
                print(f" Found manually downloaded file: {filename}")
                df = pd.read_csv(manual_file)
                
                if self._validate_data(df):
                
                    df.to_csv(cache_file, index=False)
                    print(f" Cached to: {cache_file}")
                    return df
        
  
        raise FileNotFoundError(
            f"\n Please download the dataset manually:\n"
            f"1. Go to: https://www.kaggle.com/datasets/bhadramohit/customer-shopping-latest-trends-dataset\n"
            f"2. Place the CSV file in: {self.cache_dir}/\n"
           
        )
    
    def _validate_data(self, df: pd.DataFrame) -> bool:
     
        if df.empty:
            print(" Dataset is empty")
            return False
        
    
        essential_cols = ['Season', 'Purchase Amount (USD)', 'Discount Applied', 'Category']
        missing_cols = [col for col in essential_cols if col not in df.columns]
        
        if missing_cols:
            print(f" Missing columns: {missing_cols}")
            print(f"Available columns: {list(df.columns)}")
            return False
        
   
        if 'Season' in df.columns:
            seasons = df['Season'].unique()
            expected_seasons = ['Spring', 'Summer', 'Fall', 'Winter']
            if not all(s in expected_seasons for s in seasons):
                print(f"Unexpected season values: {seasons}")
        
        print(f" Data validation passed: {len(df)} shopping records")
        print(f"   Seasons: {df['Season'].unique()}")
        print(f"   Categories: {df['Category'].unique()}")
        return True
    
    def get_sample_data(self, n_rows: int = 100) -> pd.DataFrame:
        df = self.fetch_shopping_trends()
        return df.head(n_rows)


if __name__ == "__main__":
    print("="*60)
    print("TESTING SHOPPING TRENDS FETCHER")
    print("="*60)
    
    fetcher = ShoppingTrendsFetcher()
    
    try:
        df = fetcher.fetch_shopping_trends()
        print(f"\n Shopping Trends Dataset Loaded: {len(df)} rows")
        print(f"\nColumns: {list(df.columns)}")
        print(f"\n Dataset Summary:")
        print(f"   Unique Seasons: {df['Season'].nunique()}")
        print(f"   Seasons: {list(df['Season'].unique())}")
        print(f"   Discount Applied: {df['Discount Applied'].value_counts().to_dict()}")
        print(f"   Categories: {list(df['Category'].unique())}")
        print("\nSample:")
        print(df[['Item Purchased', 'Category', 'Purchase Amount (USD)', 'Season', 'Discount Applied']].head(5))
    except FileNotFoundError as e:
        print(f"\n{e}")




        