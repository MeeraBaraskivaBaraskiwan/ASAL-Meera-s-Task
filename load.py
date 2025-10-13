from sqlalchemy import create_engine

def load_data_to_db(df, table_name, db_url='postgresql+psycopg2://postgres:12345678@localhost/fashion_db'):
    engine = create_engine(db_url)
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    return engine











    