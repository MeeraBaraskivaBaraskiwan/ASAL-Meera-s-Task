
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

    if 'User ID' not in df.columns:
        df['User ID'] = 9999
    if 'Category' not in df.columns:
        df['Category'] = "Men's Fashion"
    if 'Color' not in df.columns:
        df['Color'] = 'Various'
    if 'Size' not in df.columns:
        df['Size'] = 'Standard'

    data_clean = df.dropna(subset=['Brand', 'Product Name'])
    data_clean['Quantity_Sold'] = 1

    data_clean.rename(columns={
        'Product Name': 'product_name',
        'Brand': 'brand',
        'Quantity_Sold': 'quantity_sold',
        'Product ID': 'Product ID', 
        'User ID': 'User ID',
        'Category': 'Category'
    }, inplace=True)

    if source_file:
        data_clean['source_file'] = source_file

    data_clean.drop_duplicates(subset=['Product ID'], keep='last', inplace=True)
    print("\nTransformed Data:")
    print(data_clean.head())
    return data_clean



