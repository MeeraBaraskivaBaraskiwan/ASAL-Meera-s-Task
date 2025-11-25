import pandas as pd
from typing import Optional, Dict


def detect_file_type(df: pd.DataFrame) -> str:

    columns = [col.lower() for col in df.columns]
    
    if 'sentiment_score' in columns or 'sentiment_category' in columns:
        return 'reviews'
    
    if 'revenue' in columns and 'discount_percent' in columns:
        return 'shopping'

    if 'season' in columns and 'final_price' in columns and 'base_price' in columns:
        return 'shopping'
    
    return 'fashion_sales'


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    column_mapping: Dict[str, str] = {}
    
    for col in df.columns:
        col_lower: str = col.lower().replace('_', ' ').replace('-', ' ')
        
        if 'user' in col_lower and 'id' in col_lower:
            column_mapping[col] = 'User ID'
        elif 'product' in col_lower and 'id' in col_lower:
            column_mapping[col] = 'Product ID'
        elif col_lower in ['id', 'productid', 'clothing id']:
            column_mapping[col] = 'Product ID'
        elif 'product' in col_lower and ('name' in col_lower or 'title' in col_lower):
            column_mapping[col] = 'Product Name'
        elif col_lower in ['name', 'title', 'description', 'item purchased']:
            column_mapping[col] = 'Product Name'
        elif col_lower in ['brand', 'brandname', 'brand name']:
            column_mapping[col] = 'Brand'
        elif col_lower in ['category', 'product category']:
            column_mapping[col] = 'Category'
        elif col_lower in ['price', 'product price']:
            column_mapping[col] = 'Price'
        elif col_lower in ['rating', 'product rating', 'review rating']:
            column_mapping[col] = 'Rating'
        elif col_lower in ['color', 'colour']:
            column_mapping[col] = 'Color'
        elif col_lower in ['size', 'product size']:
            column_mapping[col] = 'Size'
    
    if column_mapping:
        df.rename(columns=column_mapping, inplace=True)
    
    return df


def transform_data(df: pd.DataFrame, source_file: Optional[str] = None) -> pd.DataFrame:


    file_type = detect_file_type(df)
    
    print(f"   Detected file type: {file_type}")
    

    if file_type == 'reviews':
        print(" Reviews data (already includes sentiment)")
        
        
        required = ['product_id', 'product_name', 'brand', 'review_text', 
                   'sentiment_score', 'sentiment_category']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Reviews file missing columns: {missing}")
        
      
        if 'department' not in df.columns:
            df['department'] = 'Fashion'
        
       
        df = df.dropna(subset=['product_id', 'review_text'])
        
        
        df['product_id'] = df['product_id'].astype(int)
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(3).astype(int).clip(1, 5)
        df['sentiment_score'] = pd.to_numeric(df['sentiment_score'], errors='coerce').fillna(0)
        
        if source_file:
            df['source_file'] = source_file
        
        print(f"Validated {len(df)} reviews")
        return df
    

    elif file_type == 'shopping':
        print(" Shopping analytics (includes revenue/discounts)")
        
    
        required = ['product_id', 'product_name', 'base_price', 'final_price',
                   'revenue', 'season', 'discount_percent']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Shopping file missing columns: {missing}")
        
      
        df = df.dropna(subset=['product_id', 'product_name'])
        
      
        df['product_id'] = df['product_id'].astype(int)
        df['base_price'] = pd.to_numeric(df['base_price'], errors='coerce').fillna(0)
        df['final_price'] = pd.to_numeric(df['final_price'], errors='coerce').fillna(0)
        df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce').fillna(0)
        df['discount_percent'] = pd.to_numeric(df['discount_percent'], errors='coerce').fillna(0)
        df['quantity_sold'] = pd.to_numeric(df.get('quantity_sold', 1), errors='coerce').fillna(1).astype(int)
        
   
        valid_seasons = ['Spring', 'Summer', 'Fall', 'Winter']
        df['season'] = df['season'].apply(lambda x: x if x in valid_seasons else 'Spring')
        
     
        if 'brand' not in df.columns:
            df['brand'] = 'Fashion Brand'
        if 'category' not in df.columns:
            df['category'] = "Men's Fashion"
        if 'sale_year' not in df.columns:
            df['sale_year'] = 2024
        if 'sale_month' not in df.columns:
            df['sale_month'] = 6
        if 'is_promotional_period' not in df.columns:
            df['is_promotional_period'] = df['discount_percent'] > 15
        
        if source_file:
            df['source_file'] = source_file
        
        print(f"Validated {len(df)} shopping records")
        return df
    

    else:
        print("Fashion sales data (applying normalization)")
        df = normalize_columns(df)
        
    
        missing_critical = []
        if 'Brand' not in df.columns:
            missing_critical.append('Brand')
        if 'Product Name' not in df.columns:
            missing_critical.append('Product Name')
        
        if missing_critical:
            raise ValueError(f"Missing required columns: {missing_critical}")
        
   
        if 'User ID' not in df.columns:
            df['User ID'] = 9999
        if 'Category' not in df.columns:
            df['Category'] = "Men's Fashion"
        if 'Color' not in df.columns:
            df['Color'] = 'Various'
        if 'Size' not in df.columns:
            df['Size'] = 'Standard'
        
       
        if 'Price' in df.columns:
            df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
            df['Price'] = df['Price'].fillna(50).astype(int)
        else:
            df['Price'] = 50
        

        if 'Rating' in df.columns:
            df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
            df['Rating'] = df['Rating'].fillna(4.0).clip(1.0, 5.0)
        else:
            df['Rating'] = 4.0
        

        df['User ID'] = pd.to_numeric(df['User ID'], errors='coerce').fillna(9999).astype(int)
        
        if 'Product ID' not in df.columns or df['Product ID'].isna().all():
            df['Product ID'] = range(90000, 90000 + len(df))
        else:
            df['Product ID'] = pd.to_numeric(df['Product ID'], errors='coerce')
            mask = df['Product ID'].isna()
            if mask.any():
                df.loc[mask, 'Product ID'] = range(90000, 90000 + mask.sum())
        df['Product ID'] = df['Product ID'].astype(int)
        
       
        df = df.dropna(subset=['Brand', 'Product Name'])
        
        if len(df) == 0:
            raise ValueError("No valid data rows after cleaning")
        

        df['Quantity_Sold'] = 1
        
    
        df.rename(columns={
            'Product Name': 'product_name',
            'Brand': 'brand',
            'Quantity_Sold': 'quantity_sold',
            'Product ID': 'Product ID',
            'User ID': 'User ID',
            'Category': 'Category',
            'Price': 'price',
            'Rating': 'rating',
            'Color': 'color',
            'Size': 'size'
        }, inplace=True)
        
        if source_file:
            df['source_file'] = source_file
        
   
        df.drop_duplicates(subset=['Product ID'], keep='last', inplace=True)
        
        print(f"Transformed {len(df)} rows")
        return df