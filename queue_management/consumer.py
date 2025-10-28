from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
import shutil
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from data_extract.extract import read_file
from data_transform.transform import transform_data
from data_load.load import load_data_to_db
from data_report.report import generate_report
from queue_management.queue_manager import QueueManager
from config import config


def process_file(filepath: Path, engine: Engine) -> None:
    try:
        if not filepath.exists():
            print(f"File not found: {filepath}")
            return
        
        print(f"\n{'='*60}")
        print(f"Processing: {filepath.name}")
        print(f"{'='*60}")
        
        print("\nEXTRACT")
        df_raw = read_file(filepath)
        print(f"Extracted {len(df_raw)} rows")
        
        print("\nTRANSFORM")
        df_clean = transform_data(df_raw, source_file=filepath.name)
        print(f"Transformed to {len(df_clean)} rows")
        
        print("\n LOAD")
        load_data_to_db(df_clean,config.TABLE_NAME, engine)
        print(f"Loaded to database table: {config.TABLE_NAME}")
   
        print("\n ARCHIVE")
        config.ARCHIVE_DIR.mkdir(exist_ok=True)
        dest = config.ARCHIVE_DIR / filepath.name
        shutil.move(str(filepath), str(dest))
        print(f"Moved to: {dest}")
        
        print(f"\nSuccessfully processed: {filepath.name}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\nError processing {filepath.name}: {e}")
        print(f"{'='*60}\n")
        raise


def start_consumer(
    generate_report_after: bool = True,  max_messages: int = None) -> None:

    print("="*60)
    print("CONSUMER: Starting File Processor")
    print("="*60)
    print(f"Database: {config.DB_NAME}")
    print(f"Archive: {config.ARCHIVE_DIR}")
    print(f"Table: {config.TABLE_NAME}")
    print(f"Queue: {config.RABBITMQ_QUEUE}")
    try:
        engine = create_engine(config.get_database_url())
        print(f" Connected to: {config.DB_NAME}")
    except Exception as e:
        print(f" Database connection failed: {e}")
        return
    
    queue_mgr = QueueManager()
    
    try:
        queue_mgr.connect()
        
        queue_size = queue_mgr.get_queue_size()
        print(f"Queue size: {queue_size} messages waiting")
        
        if queue_size == 0:
            print("\n Queue is empty!")
            return
        

        processed_count = [0] 
        
        def callback(filepath: Path):
            process_file(filepath, engine)
            processed_count[0] += 1
            
            if max_messages and processed_count[0] >= max_messages:
                print(f"\nReached maximum messages ({max_messages})")
                queue_mgr.channel.stop_consuming()

        print("\n" + "="*60)
        queue_mgr.consume_files(callback)
        
   
    except Exception as e:
        print(f"\n Consumer error: {e}")
    finally:
      
        if generate_report_after and processed_count[0] > 0:
            print("\n" + "="*60)
            print(" GENERATING REPORT")
            print("="*60)
            try:
                generate_report(engine)
            except Exception as e:
                print(f" Report generation failed: {e}")
        
      
        print("\n" + "="*60)
        print(f" CONSUMER SUMMARY")
        print("="*60)
        print(f" Processed {processed_count[0]} files")
        print(f"Remaining in queue: {queue_mgr.get_queue_size()} messages")
        print("="*60)
        
        queue_mgr.disconnect()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Consume and process files from queue')
    parser.add_argument('--no-report', action='store_true', help='Skip report generation')
    parser.add_argument('--max', type=int, help='Maximum number of files to process')
    
    args = parser.parse_args()
    
    start_consumer(
        generate_report_after=not args.no_report,
        max_messages=args.max
    )


    