import pandas as pd
import numpy as np
from typing import Optional


class ShoppingTransformer:

    def __init__(self):
        self.category_mapping = {
            'Clothing': "Men's Fashion",
            'Footwear': 'Footwear',
            'Accessories': 'Accessories',
            'Outerwear': "Women's Fashion"
        }
        
        self.brand_mapping = {
            'Clothing': ['Zara', 'H&M', 'Uniqlo', 'Gap', 'Forever 21'],
            'Footwear': ['Nike', 'Adidas', 'Puma', 'New Balance', 'Converse'],
            'Accessories': ['Michael Kors', 'Kate Spade', 'Coach', 'Fossil'],
            'Outerwear': ['North Face', 'Patagonia', 'Columbia', 'Canada Goose']
        }
    
    def transform(self, df: pd.DataFrame, source_file: str = "kaggle_shopping_trends") -> pd.DataFrame:
      
        print(f"\n TRANSFORMING SHOPPING TRENDS DATA")
        print(f"   Input rows: {len(df)}")
        print(f"   Columns available: {list(df.columns)}")
        
    
        if 'Customer ID' in df.columns:
            
            df['product_id'] = (df['Customer ID'].astype(str).str[-4:].astype(int) * 100 + 
                               df.index % 100 + 10000)
        else:
            df['product_id'] = range(50000, 50000 + len(df))
        
       
        if 'Item Purchased' in df.columns:
            df['product_name'] = df['Item Purchased']
        else:
            df['product_name'] = 'Fashion Item ' + df['product_id'].astype(str)
        
      
        if 'Category' in df.columns:
            df['category'] = df['Category'].map(self.category_mapping).fillna(df['Category'])
        else:
            df['category'] = "Men's Fashion"
        
        
        df['brand'] = self._assign_brand(df)
        
       
        if 'Purchase Amount (USD)' in df.columns:
            df['base_price'] = df['Purchase Amount (USD)'].fillna(50).astype(float)
        else:
            raise ValueError("Missing 'Purchase Amount (USD)' column")
        
       
        if 'Discount Applied' in df.columns:
            df['discount_percent'] = df['Discount Applied'].apply(self._convert_discount)
        else:
            print("No discount column found, setting to 0%")
            df['discount_percent'] = 0
        
        df['final_price'] = df['base_price'] * (1 - df['discount_percent'] / 100)
        
    
        df['quantity_sold'] = 1
        
      
        df['revenue'] = df['final_price'] * df['quantity_sold']
        
        if 'Season' not in df.columns:
            print(" Warning: Season column not found")
            df['season'] = 'Unknown'
        else:
            df['season'] = df['Season']
        
       
        df['sale_year'] = 2024
        df['sale_month'] = df['season'].map({
            'Spring': np.random.choice([3, 4, 5]),
            'Summer': np.random.choice([6, 7, 8]),
            'Fall': np.random.choice([9, 10, 11]),
            'Winter': np.random.choice([12, 1, 2])
        }).fillna(6)
        
   
        df['is_promotional_period'] = df['discount_percent'] > 15
        
       
        df['source_file'] = source_file
        
       
        final_columns = [
            'product_id', 'product_name', 'brand', 'category',
            'base_price', 'discount_percent', 'final_price',
            'quantity_sold', 'revenue', 'season', 'sale_year', 'sale_month',
            'is_promotional_period', 'source_file'
        ]
        
        df_final = df[final_columns].copy()
        
       
        df_final = df_final[df_final['base_price'] > 0]
        df_final = df_final[df_final['final_price'] >= 0]
        df_final = df_final.dropna(subset=['product_id', 'product_name', 'season'])
        
        print(f"   Output rows: {len(df_final)}")
        print(f"   Average discount: {df_final['discount_percent'].mean():.1f}%")
        print(f"   Total revenue: ${df_final['revenue'].sum():,.2f}")
        print(f"   Seasons: {df_final['season'].unique()}")
        print(f"   Promotional items: {df_final['is_promotional_period'].sum()} ({df_final['is_promotional_period'].mean()*100:.1f}%)")
        
        return df_final
    
    def _convert_discount(self, discount_applied: str) -> float:
 
        if isinstance(discount_applied, str):
            if discount_applied.lower() == 'yes':
               
                return np.random.uniform(15, 30)
            else:
                return 0.0
        return 0.0
    
    def _assign_brand(self, df: pd.DataFrame) -> pd.Series:
     
        def get_brand(category):
            if category in self.brand_mapping:
                return np.random.choice(self.brand_mapping[category])
            return 'Fashion Brand'
        
        if 'Category' in df.columns:
            return df['Category'].apply(get_brand)
        return 'Fashion Brand'
    
    def get_summary_stats(self, df: pd.DataFrame) -> dict:
    
        return {
            'total_transactions': len(df),
            'unique_products': df['product_id'].nunique(),
            'total_revenue': df['revenue'].sum(),
            'avg_discount': df['discount_percent'].mean(),
            'promotional_sales_pct': (df['is_promotional_period'].sum() / len(df)) * 100,
            'best_season': df.groupby('season')['revenue'].sum().idxmax(),
            'avg_price': df['base_price'].mean(),
            'categories': df['category'].nunique()
        }


if __name__ == "__main__":
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from data_sources.shopping_fetcher import ShoppingTrendsFetcher
    
    print("="*60)
    print("TESTING SHOPPING TRANSFORMER")
    print("="*60)
    
    fetcher = ShoppingTrendsFetcher()
    
    try:
        raw_df = fetcher.get_sample_data(n_rows=100)
        print(f" Fetched {len(raw_df)} sample records")
        
        transformer = ShoppingTransformer()
        transformed_df = transformer.transform(raw_df)
        
        print("\n TRANSFORMATION COMPLETE")
        print(f"\nSample transformed data:")
        print(transformed_df[['product_name', 'base_price', 'discount_percent', 'revenue', 'season']].head())
        
        stats = transformer.get_summary_stats(transformed_df)
        print(f"\nSummary Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
    except Exception as e:
        print(f" Error: {e}")
        print("\nMake sure to download the shopping trends dataset!")



        