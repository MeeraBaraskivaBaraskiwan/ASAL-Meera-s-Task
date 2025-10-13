import pandas as pd

def generate_report(engine):
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




    
 