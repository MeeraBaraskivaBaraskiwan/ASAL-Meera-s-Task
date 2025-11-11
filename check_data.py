from sqlalchemy import create_engine, text
from config import config

engine = create_engine(config.get_database_url())

with engine.connect() as conn:
   
    result = conn.execute(text("SELECT COUNT(*) FROM file_processing_log"))
    files = result.fetchone()[0]
    print(f"Files in database: {files}")
    
   
    result = conn.execute(text("SELECT COUNT(*) FROM fashion_sales"))
    sales = result.fetchone()[0]
    print(f"Sales records: {sales}")
    
  
    result = conn.execute(text("""
        SELECT status, COUNT(*) 
        FROM file_processing_log 
        GROUP BY status
    """))
    print("\nStatus breakdown:")
    for row in result:
        print(f"  {row[0]}: {row[1]}")