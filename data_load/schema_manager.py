import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from typing import Union, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config


class SchemaManager:

    def __init__(self, engine_or_url: Union[str, Engine] = None):
        if engine_or_url is None:
            self.engine = create_engine(config.get_database_url())
        elif hasattr(engine_or_url, 'connect'):
            self.engine = engine_or_url
        else:
            self.engine = create_engine(engine_or_url)
    
    def load_reviews(self, df: pd.DataFrame, mode: str = 'append') -> int:
       
        print(f"\n LOADING REVIEWS TO DATABASE")
        print(f"   Mode: {mode}")
        print(f"   Rows to insert: {len(df)}")
        
     
        required_cols = [
            'product_id', 'product_name', 'brand', 'department',
            'review_text', 'rating', 'sentiment_score', 'sentiment_category'
        ]
        
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
  
        df.to_sql(
            'product_reviews',
            self.engine,
            if_exists=mode,
            index=False,
            method='multi',  
            chunksize=1000
        )
        
        print(f"  Loaded {len(df)} reviews")
        
   
        self._refresh_view('mv_top_sentiment_products')
        
        return len(df)
    
    def load_analytics(self, df: pd.DataFrame, mode: str = 'append') -> int:
       
        print(f"\n LOADING ANALYTICS TO DATABASE")
        print(f"   Mode: {mode}")
        print(f"   Rows to insert: {len(df)}")
        
     
        required_cols = [
            'product_id', 'product_name', 'base_price', 'final_price',
            'revenue', 'season', 'sale_year'
        ]
        
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
      
        df.to_sql(
            'product_analytics',
            self.engine,
            if_exists=mode,
            index=False,
            method='multi',
            chunksize=1000
        )
        
        print(f" Loaded {len(df)} analytics records")
        
     
        self._refresh_view('mv_seasonal_profitability')
        
        return len(df)
    
    def compute_profitability(self) -> int:
       
        print(f"\n COMPUTING PRODUCT PROFITABILITY")
        
       
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM product_profitability"))
        
      
        query = text("""
            INSERT INTO product_profitability (
                product_id, product_name, brand, category,
                total_units_sold, avg_base_price, avg_discount_percent,
                total_revenue, avg_sentiment_score, review_count, best_season
            )
            SELECT 
                a.product_id,
                MAX(a.product_name) as product_name,  -- Use MAX to pick one
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
        
        with self.engine.begin() as conn:
            result = conn.execute(query)
            rows_affected = result.rowcount
        
     
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
        
        with self.engine.begin() as conn:
            conn.execute(rank_query)
        
        print(f" Computed profitability for products")
        
     
        self._refresh_view('mv_brand_performance')
        
        return rows_affected
    
    def _refresh_view(self, view_name: str):
       
        try:
            with self.engine.begin() as conn:
                conn.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}"))
            print(f"  Refreshed view: {view_name}")
        except Exception as e:
            print(f"Could not refresh {view_name}: {e}")
    
    def get_table_stats(self) -> dict:
        """Get row counts for all analytics tables"""
        tables = [
            'product_reviews',
            'product_analytics',
            'product_profitability',
            'fashion_sales'
        ]
        
        stats = {}
        for table in tables:
            try:
                query = text(f"SELECT COUNT(*) FROM {table}")
                with self.engine.connect() as conn:
                    result = conn.execute(query)
                    stats[table] = result.scalar()
            except:
                stats[table] = 0
        
        return stats


if __name__ == "__main__":
    print("="*60)
    print("TESTING SCHEMA MANAGER")
    print("="*60)
    
    manager = SchemaManager()

    stats = manager.get_table_stats()
    print("\nCurrent Table Stats:")
    for table, count in stats.items():
        print(f"   {table}: {count:,} rows")
    
    print("\n Schema Manager ready")
    print("\nTo load data:")
    print("1. manager.load_reviews(reviews_df)")
    print("2. manager.load_analytics(analytics_df)")
    print("3. manager.compute_profitability()")


    