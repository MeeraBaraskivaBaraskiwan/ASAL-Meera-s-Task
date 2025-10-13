def transform_data(df):
    data_clean = df.dropna(subset=['Brand', 'Product Name'])
    data_clean['Quantity_Sold'] = 1

    data_clean.rename(columns={
        'Product Name': 'product_name',
        'Brand': 'brand',
        'Quantity_Sold': 'quantity_sold'
    }, inplace=True)

    print("\nTransformed Data:")
    print(data_clean.head())
    return data_clean












    