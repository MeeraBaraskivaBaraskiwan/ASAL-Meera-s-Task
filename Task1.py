import pandas as pd
from sqlalchemy import create_engine
#this file doesnt follow cohesion and coupling it  has  low cohesion and
#  high coupling since it does multiple tasks and it is dependent on multiple modules
# if  we do it  like this it will be hard to maintain and debug

df =pd.read_csv('fashion_products.csv')

print("Raw data:")
print(df.head())

data_clean = df.dropna(subset=['Brand', 'Product Name'])
data_clean['Quantity_Sold'] = 1


data_clean.rename(columns={
    'Product Name': 'product_name',
    'Brand': 'brand',
    'Quantity_Sold': 'quantity_sold'
    ,'Price': 'price',
    'Rating': 'rating',
    'Color': 'color',
    'Size': 'size'
}, inplace=True)



engine = create_engine('postgresql+psycopg2://postgres:12345678@localhost/fashion_db')
data_clean.to_sql('fashion_sales', engine, if_exists='replace', index=False)

query = """
SELECT brand, product_name, total_quantity
FROM (
    SELECT brand, product_name, SUM(quantity_sold) AS total_quantity
    FROM fashion_sales
    GROUP BY brand, product_name
) AS summed
WHERE (brand, total_quantity) IN (
    SELECT brand, MAX(total_quantity)
    FROM (
        SELECT brand, product_name, SUM(quantity_sold) AS total_quantity
        FROM fashion_sales
        GROUP BY brand, product_name
    ) AS inner_sum
    GROUP BY brand
)
ORDER BY brand;

"""

report = pd.read_sql_query(query, engine)
print("\nMost Sold Product per Brand:")
print(report)

report.to_sql('most_sold_products', engine, if_exists='replace', index=False)











