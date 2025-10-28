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
from config import config



def process() -> None:
    
    engine: Engine = create_engine(config.get_database_url())

    config.ARCHIVE_DIR.mkdir(exist_ok=True)

    files: List[Path] = list_incoming_files(config.INCOMING_DIR)
    if not files:
        print(f"No files in{config.INCOMING_DIR}")
        return

    for f in files:
        print("Processing", f.name)
        df_raw: pd.DataFrame = read_file(f)
        df: pd.DataFrame =  transform_data(df_raw, source_file=f.name)
        load_data_to_db(df,config.TABLE_NAME, engine)
       
        dest = config.ARCHIVE_DIR / f.name
        shutil.move(str(f), str(dest))
        print(f"Moved {f.name} to {config.ARCHIVE_DIR}")

    generate_report(engine)

if __name__ == "__main__":
    process()

    