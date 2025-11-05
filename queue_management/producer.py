from pathlib import Path
from datetime import date, timedelta
import sys
import time
from typing import Optional
sys.path.insert(0, str(Path(__file__).parent.parent))
from data_generator.create_corrupted_file import create_all_corrupted_files
from data_generator.generated_csv import generate_csv
from data_generator.generated_json import generate_json
from data_generator.generated_txt import generate_txt
from data_generator.fetch_external_json import fetch_dummyjson
from queue_management.queue_manager import QueueManager

from config import config

def generate_and_publish_files(
    num_csv: int = 2,
    num_json: int = 1,
    num_txt: int = 1,
    fetch_external: bool = True,
     include_corrupted: bool = False 
) -> None:
   
    print("="*60)
    print(" Generating Files and Publishing to Queue")
    print("="*60)
    
    queue_mgr = QueueManager()
    
    try:
        queue_mgr.connect()
    except Exception as e:
        print(f"\n Cannot connect to RabbitMQ: {e}")
        return
    
    generated_files = []
    
    try:
 
        print(f"\n Generating {num_csv} CSV files...")
        today = date.today()
        for i in range(num_csv):
            day = today - timedelta(days=i)
            generate_csv(day, rows=30)
            filepath = config.INCOMING_DIR  / f"data_{day.isoformat()}.csv"
            if filepath.exists():
                generated_files.append(filepath)
                queue_mgr.publish_file(filepath)
                time.sleep(0.1)  
       
        print(f"\n Generating {num_json} JSON files...")
        for i in range(num_json):
            day = today - timedelta(days=i)
            generate_json(day, rows=10)
            filepath =  config.INCOMING_DIR  / f"data_{day.isoformat()}.json"
            if filepath.exists():
                generated_files.append(filepath)
                queue_mgr.publish_file(filepath)
                time.sleep(0.1)
        
  
        print(f"\n Generating {num_txt} TXT files...")
        for i in range(num_txt):
            day = today - timedelta(days=i)
            generate_txt(day, rows=20)
            filepath =  config.INCOMING_DIR  / f"data_{day.isoformat()}.txt"
            if filepath.exists():
                generated_files.append(filepath)
                queue_mgr.publish_file(filepath)
                time.sleep(0.1)
        
      
        if fetch_external:
            print(f"\n Fetching external API data...")
            filepath = fetch_dummyjson()
            if filepath:
                generated_files.append(filepath)
                queue_mgr.publish_file(filepath)


        if include_corrupted:
            print(f"\nGenerating CORRUPTED files...")
            corrupted_files = create_all_corrupted_files()
            for filepath in corrupted_files:
                if filepath.exists():
                    generated_files.append(filepath)
                    queue_mgr.publish_file(filepath)
                    time.sleep(0.1)
            
        
  
        print("\n" + "="*60)
        print(f" PRODUCER SUMMARY")
        print("="*60)
        print(f" Generated {len(generated_files)} files")
        print(f" Published {len(generated_files)} messages to queue")
        print(f" Queue: {queue_mgr.queue_name}")
        print(f" Current queue size: {queue_mgr.get_queue_size()} messages")
        print("="*60)
        
    except Exception as e:
        print(f"\n Error during generation: {e}")
        raise
    
    finally:
        queue_mgr.disconnect()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate files and publish to queue')
    parser.add_argument('--csv', type=int, default=2, help='Number of CSV files')
    parser.add_argument('--json', type=int, default=1, help='Number of JSON files')
    parser.add_argument('--txt', type=int, default=1, help='Number of TXT files')
    parser.add_argument('--no-external', action='store_true', help='Skip external API fetch')
    parser.add_argument('--with-errors', action='store_true',  help='Include corrupted files to test error handling')
    
    
    args = parser.parse_args()
    
    generate_and_publish_files(
        num_csv=args.csv,
        num_json=args.json,
        num_txt=args.txt,
        fetch_external=not args.no_external,
        include_corrupted=args.with_errors  
    )


    