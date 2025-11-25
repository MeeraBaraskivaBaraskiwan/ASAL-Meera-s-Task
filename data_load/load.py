from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from typing import Union
import pandas as pd


def detect_target_table(df: pd.DataFrame) -> str:

    columns = [col.lower() for col in df.columns]
    
    if 'sentiment_score' in columns or 'sentiment_category' in columns:
        return 'product_reviews'
    
    if 'revenue' in columns and 'discount_percent' in columns:
        return 'product_analytics'
    
    return 'fashion_sales'


def load_data_to_db(df: pd.DataFrame,  table_name: str,   engine_or_url: Union[str, Engine] = 'postgresql+psycopg2://postgres:12345678@localhost/fashion_db'
) -> Engine:
  
 
    engine: Engine
    if hasattr(engine_or_url, 'connect'):
        engine = engine_or_url
    else:
        engine = create_engine(engine_or_url)
    
 
    actual_table = detect_target_table(df)
    
    print(f"   Target table: {actual_table}")
    
 
    if actual_table == 'product_reviews':
        print(f"   Loading {len(df)} reviews with sentiment...")
        
      
        required_cols = ['product_id', 'product_name', 'brand', 'department',
                        'review_text', 'rating', 'sentiment_score', 'sentiment_category']
        
   
        if 'recommended' not in df.columns:
            df['recommended'] = True
        if 'review_date' not in df.columns:
            df['review_date'] = pd.Timestamp.now().date()
        
      
        df.to_sql('product_reviews', engine, if_exists='append', index=False)
        
        print(f"Loaded {len(df)} reviews to product_reviews")
        
    
        try:
            with engine.begin() as conn:
                conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_sentiment_products"))
            print("Refreshed sentiment view")
        except Exception as e:
            print(f" Could not refresh view: {e}")
    

    elif actual_table == 'product_analytics':
        print(f"   Loading {len(df)} analytics records with revenue...")
        
  
        required_cols = ['product_id', 'product_name', 'base_price', 'final_price',
                        'revenue', 'season', 'discount_percent']
        
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Shopping analytics file missing columns: {missing}")
        
 
        print("   Validating data types...")
        df['product_id'] = pd.to_numeric(df['product_id'], errors='coerce').fillna(0).astype(int)
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
        if 'is_promotional' not in df.columns:
            df['is_promotional'] = df.get('is_promotional_period', df['discount_percent'] > 15)
        
       
        df = df[df['product_id'] > 0]
        
        print(f"   Validated {len(df)} records")
        
     
        df.to_sql('product_analytics', engine, if_exists='append', index=False)
        
        print(f" Loaded {len(df)} records to product_analytics")
        
      
        try:
            with engine.begin() as conn:
                conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_seasonal_profitability"))
            print("  Refreshed seasonal profitability view")
        except Exception as e:
            print(f" Could not refresh view: {e}")

    else:
        print(f"   Loading {len(df)} rows to fashion_sales (UPSERT)...")
     
        df.rename(columns={
            'Price': 'price',
            'Rating': 'rating',
            'Color': 'color',
            'Size': 'size'
        }, inplace=True)
        
      
        temp_table: str = f"{table_name}_temp"
        df.to_sql(temp_table, engine, if_exists='replace', index=False)
        
     
        with engine.begin() as conn:
            upsert_query = text(f"""
                INSERT INTO {table_name} (
                    "User ID", "Product ID", product_name, brand, "Category", 
                    price, rating, color, size, quantity_sold, source_file
                )
                SELECT 
                    "User ID", "Product ID", product_name, brand, "Category",
                    price, rating, color, size, quantity_sold, source_file
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
            
            conn.execute(upsert_query)
            conn.execute(text(f"DROP TABLE IF EXISTS {temp_table};"))
        
        print(f"  Upserted {len(df)} rows to {table_name}")
    
    return engine


def compute_profitability(engine: Engine) -> None:

    print("\n Computing Product Profitability...")
    

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM product_profitability"))
    
 
    query = text("""
        INSERT INTO product_profitability (
            product_id, product_name, brand, category,
            total_units_sold, avg_base_price, avg_discount_percent,
            total_revenue, avg_sentiment_score, review_count, best_season
        )
        SELECT 
            a.product_id,
            MAX(a.product_name) as product_name,
            MAX(a.brand) as brand,
            MAX(a.category) as category,
            SUM(a.quantity_sold) as total_units_sold,
            AVG(a.base_price) as avg_base_price,
            AVG(a.discount_percent) as avg_discount_percent,
            SUM(a.revenue) as total_revenue,
            COALESCE(AVG(r.sentiment_score), 0) as avg_sentiment_score,
            COUNT(DISTINCT r.review_id) as review_count,
            (
                SELECT season 
                FROM product_analytics a2 
                WHERE a2.product_id = a.product_id
                GROUP BY season
                ORDER BY SUM(a2.revenue) DESC
                LIMIT 1
            ) as best_season
        FROM product_analytics a
        LEFT JOIN product_reviews r ON a.product_id = r.product_id
        GROUP BY a.product_id
    """)
    
    with engine.begin() as conn:
        result = conn.execute(query)
        rows = result.rowcount
    
 
    rank_query = text("""
        UPDATE product_profitability
        SET profitability_rank = subq.rank
        FROM (
            SELECT 
                product_id,
                ROW_NUMBER() OVER (ORDER BY total_revenue DESC) as rank
            FROM product_profitability
        ) subq
        WHERE product_profitability.product_id = subq.product_id
    """)
    
    with engine.begin() as conn:
        conn.execute(rank_query)
    
    print(f" Computed profitability for {rows} products")
    
   
    try:
        with engine.begin() as conn:
            conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_brand_performance"))
        print(" Refreshed brand performance view")
    except Exception as e:
        print(f"  Could not refresh view: {e}")


