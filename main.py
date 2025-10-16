from pathlib import Path
from extract import list_incoming_files, read_file
from transform import transform_data
from load import load_data_to_db
from sqlalchemy import create_engine

from report import generate_report
import shutil
INCOMING = Path("Incoming-data")
ARCHIVE = Path("Archived-data")
TABLE = 'fashion_sales'
DB_URL = 'postgresql+psycopg2://postgres:12345678@localhost/fashion_db'
def process():
    

    
    engine = create_engine(DB_URL)

    ARCHIVE.mkdir(exist_ok=True)

    files = list_incoming_files(INCOMING)
    if not files:
        print("No files in Incoming-data")
        return

    for f in files:
        print("Processing", f.name)
        df_raw = read_file(f)
        df = transform_data(df_raw, source_file=f.name)
        load_data_to_db(df, TABLE, engine)
       
        dest = ARCHIVE / f.name
        shutil.move(str(f), str(dest))
        print("Moved", f.name, "to Archived-data")

    generate_report(engine)

if __name__ == "__main__":
    process()

    