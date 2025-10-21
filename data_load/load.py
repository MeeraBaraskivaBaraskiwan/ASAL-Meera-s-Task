from sqlalchemy import create_engine,text
from sqlalchemy.engine import Engine
from typing import Union
import pandas as pd

def load_data_to_db(df: pd.DataFrame,  table_name: str,
 engine_or_url: Union[str, Engine] = 'postgresql+psycopg2://postgres:12345678@localhost/fashion_db') -> Engine:
    

    engine: Engine 
    if hasattr(engine_or_url, 'connect'):
        engine = engine_or_url
    else:
        engine = create_engine(engine_or_url)

    df.rename(columns={
        'Price': 'price',
        'Rating': 'rating',
        'Color': 'color',
        'Size': 'size'
    }, inplace=True)

    temp_table: str =f"{table_name}_temp"
    df.to_sql(temp_table, engine, if_exists='replace', index=False)
   

    with engine.begin() as conn:
        upsert_query = text(f"""
            INSERT INTO {table_name} ("User ID", "Product ID", product_name, brand, "Category", price, rating, color, size, quantity_sold, source_file)
            SELECT "User ID", "Product ID", product_name, brand, "Category", price, rating, color, size, quantity_sold, source_file
            FROM {temp_table}
            ON CONFLICT ("Product ID")
            DO UPDATE SET
                "User ID" = EXCLUDED."User ID",
                product_name = EXCLUDED.product_name,
                brand = EXCLUDED.brand,
                "Category" = EXCLUDED."Category",
                price = EXCLUDED.price,
                rating = EXCLUDED.rating,
                color = EXCLUDED.color,
                size = EXCLUDED.size,
                quantity_sold = EXCLUDED.quantity_sold,
                source_file = EXCLUDED.source_file;
        """)
        print("Running UPSERT query...")
        conn.execute(upsert_query)

        print(f"Dropping temporary table: {temp_table}")
        conn.execute(text(f"DROP TABLE IF EXISTS {temp_table};"))

    print(f" Upserted data into {table_name}.")
    return engine











    