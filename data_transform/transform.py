
import pandas as pd
from typing import Optional, Dict


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
   
    column_mapping: Dict[str, str] = {}
    
    for col in df.columns:
        col_lower: str = col.lower().replace('_', ' ').replace('-', ' ')
        
        if 'user' in col_lower and 'id' in col_lower:
            column_mapping[col] = 'User ID'
        elif 'product' in col_lower and 'id' in col_lower:
            column_mapping[col] = 'Product ID'
        elif col_lower in ['id', 'productid']:
            column_mapping[col] = 'Product ID'
        elif 'product' in col_lower and ('name' in col_lower or 'title' in col_lower):
            column_mapping[col] = 'Product Name'
        elif col_lower in ['name', 'title', 'description']:
            column_mapping[col] = 'Product Name'
        elif col_lower in ['brand', 'brandname', 'brand name']:
            column_mapping[col] = 'Brand'
        elif col_lower in ['category', 'product category']:
            column_mapping[col] = 'Category'
        elif col_lower in ['price', 'product price']:
            column_mapping[col] = 'Price'
        elif col_lower in ['rating', 'product rating']:
            column_mapping[col] = 'Rating'
        elif col_lower in ['color', 'colour']:
            column_mapping[col] = 'Color'
        elif col_lower in ['size', 'product size']:
            column_mapping[col] = 'Size'
    
    if column_mapping:
        df.rename(columns=column_mapping, inplace=True)
    
    return df


def transform_data(df: pd.DataFrame, source_file: Optional[str] = None) -> pd.DataFrame:

    df = normalize_columns(df)

    missing_critical = []
    if 'Brand' not in df.columns:
        missing_critical.append('Brand')
    if 'Product Name' not in df.columns:
        missing_critical.append('Product Name')
    
    
    if missing_critical:
        raise ValueError(missing_critical)
    
    if len(df.columns) <= 2:
        print(f"Warning: Only {len(df.columns)} columns detected")
        print(f"Available columns: {list(df.columns)}")
        if len(df.columns) == 1:
            raise ValueError("Possible delimiter issue - only 1 column detected")

    if 'User ID' not in df.columns:
        df['User ID'] = 9999
    if 'Category' not in df.columns:
        df['Category'] = "Men's Fashion"
    if 'Color' not in df.columns:
        df['Color'] = 'Various'
    if 'Size' not in df.columns:
        df['Size'] = 'Standard'
    if 'Product Name' not in df.columns:
        df['Product Name'] = 'Unknown Product'
    if 'Brand' not in df.columns:
        df['Brand'] = 'Unknown Brand'

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


    data_clean = df.dropna(subset=['Brand', 'Product Name'])

    if len(data_clean) == 0:
        raise ValueError("No valid data rows after cleaning")
    data_clean['Quantity_Sold'] = 1

    data_clean.rename(columns={
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
        data_clean['source_file'] = source_file

    data_clean.drop_duplicates(subset=['Product ID'], keep='last', inplace=True)
    print("\nTransformed Data:")
    print(data_clean.head())
    return data_clean



