import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from data_generator.generated_csv import generate_csv
from data_generator.generated_json import generate_json
from data_generator.create_corrupted_file import create_all_corrupted_files
from queue_management.queue_manager import QueueManager
from config import config
from datetime import date
import time


def main():
    print("=" * 60)
    print("Task 9: Fault Tolerance Test")
    print("=" * 60)
    
    # Generate good files
    today = date.today()
    generate_csv(today, rows=10)
    generate_json(today, rows=5)
    
    good_files = [
        config.INCOMING_DIR / f"data_{today.isoformat()}.csv",
        config.INCOMING_DIR / f"data_{today.isoformat()}.json",
    ]
    
    # Generate corrupted files
    corrupted_files = create_all_corrupted_files()
    all_files = good_files + corrupted_files
    
    # Publish to queue
    queue_mgr = QueueManager()
    
    try:
        queue_mgr.connect()
        
        for filepath in all_files:
            if filepath.exists():
                queue_mgr.publish_file(filepath)
                time.sleep(0.1)
        
        print(f"\nPublished {len(all_files)} files to queue")
        print(f"Good files: {len(good_files)}")
        print(f"Corrupted files: {len(corrupted_files)}")
        print(f"Queue size: {queue_mgr.get_queue_size()}")
        
    finally:
        queue_mgr.disconnect()
    
    print("\n" + "=" * 60)
    print("Next step: Run the consumer")
    print("=" * 60)
    print("\nCommand: python queue_management/consumer_enhanced.py")



if __name__ == "__main__":
    main()