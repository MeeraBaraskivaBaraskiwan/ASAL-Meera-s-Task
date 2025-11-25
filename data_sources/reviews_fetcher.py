"""
Dataset: https://www.kaggle.com/datasets/nicapotato/womens-ecommerce-clothing-reviews
"""

import pandas as pd
from pathlib import Path
from typing import Optional
import hashlib
import json


class ReviewsFetcher:
    
    def __init__(self, cache_dir: Path = Path("external_data_cache")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        
        self.dataset_name = "womens_ecommerce_reviews"
        self.expected_columns = [
            'Clothing ID', 'Age', 'Title', 'Review Text', 
            'Rating', 'Recommended IND', 'Division Name', 
            'Department Name', 'Class Name'
        ]
    
    def fetch_reviews(self, force_refresh: bool = False) -> pd.DataFrame:

        cache_file = self.cache_dir / f"{self.dataset_name}.csv"
        metadata_file = self.cache_dir / f"{self.dataset_name}_metadata.json"
        
        if not force_refresh and cache_file.exists():
            print(f"Loading reviews from cache: {cache_file}")
            df = pd.read_csv(cache_file)
            
            if self._validate_data(df):
                return df
            else:
                print("Cached data invalid, checking manual file...")
        
        manual_file = self.cache_dir / "Womens Clothing E-Commerce Reviews.csv"
        if manual_file.exists():
            print(f"Found manually downloaded file")
            df = pd.read_csv(manual_file)
            
   
            if self._validate_data(df):
                df.to_csv(cache_file, index=False)
                self._save_metadata(metadata_file, df)
                print(f"Cached to: {cache_file}")
                return df
        
    
        raise FileNotFoundError(
            f"\n Please download the dataset manually:\n"
            f"1. Go to: https://www.kaggle.com/datasets/nicapotato/womens-ecommerce-clothing-reviews\n"
            f"2. Place the CSV file in: {self.cache_dir}/\n"
            f"4. Expected filename: 'Womens Clothing E-Commerce Reviews.csv'"
        )
    
    def _validate_data(self, df: pd.DataFrame) -> bool:
        if df.empty:
            print("Dataset is empty")
            return False
        
        essential_cols = ['Review Text', 'Rating', 'Recommended IND']
        missing_cols = [col for col in essential_cols if col not in df.columns]
        
        if missing_cols:
            print(f" Missing columns: {missing_cols}")
            return False
        

        if not pd.api.types.is_numeric_dtype(df['Rating']):
            print(" Rating column is not numeric")
            return False
        
        print(f" Data validation passed: {len(df)} reviews")
        return True
    
    def _save_metadata(self, filepath: Path, df: pd.DataFrame):

        metadata = {
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': list(df.columns),
            'downloaded_at': pd.Timestamp.now().isoformat(),
            'data_hash': hashlib.md5(str(df.head()).encode()).hexdigest()
        }
        
        with open(filepath, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def get_sample_data(self, n_rows: int = 100) -> pd.DataFrame:
    
        df = self.fetch_reviews()
        return df.head(n_rows)


if __name__ == "__main__":
    print("="*60)
    print("TESTING REVIEWS FETCHER")
    print("="*60)
    
    fetcher = ReviewsFetcher()
    
    try:
        df = fetcher.fetch_reviews()
        print(f"\nReviews Dataset Loaded: {len(df)} rows")
        print(f"Columns: {list(df.columns)}")
        print("\nSample:")
        print(df[['Review Text', 'Rating', 'Recommended IND']].head(3))
    except FileNotFoundError as e:
        print(f"\n{e}")



        