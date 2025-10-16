def transform_data(df, source_file=None):
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












    