from pathlib import Path
from data_extract.extract import list_incoming_files, read_file
from data_transform.transform import transform_data
from data_load.load import load_data_to_db
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from data_report.report import generate_report
import shutil
import pandas as pd  
from typing import List

INCOMING = Path("Incoming-data")
ARCHIVE = Path("Archived-data")
TABLE = 'fashion_sales'
DB_URL = 'postgresql+psycopg2://postgres:12345678@localhost/fashion_db'


def process() -> None:
    
    engine: Engine = create_engine(DB_URL)

    ARCHIVE.mkdir(exist_ok=True)

    files: List[Path] = list_incoming_files(INCOMING)
    if not files:
        print("No files in Incoming-data")
        return

    for f in files:
        print("Processing", f.name)
        df_raw: pd.DataFrame = read_file(f)
        df: pd.DataFrame =  transform_data(df_raw, source_file=f.name)
        load_data_to_db(df, TABLE, engine)
       
        dest = ARCHIVE / f.name
        shutil.move(str(f), str(dest))
        print("Moved", f.name, "to Archived-data")

    generate_report(engine)

if __name__ == "__main__":
    process()

    