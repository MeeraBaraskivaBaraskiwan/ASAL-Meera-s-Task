import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from data_generator.generated_csv import generate_csv
from data_generator.generated_json import generate_json
from queue_management.queue_manager import QueueManager
from config import config
from datetime import date, timedelta
import time


def main():
    print("=" * 60)
    print("Task 10: Continuous Consumer Test")
    print("=" * 60)
    
    print("\nBefore running this test:")
    print("1. Open another terminal")
    print("2. Run: python queue_management/consumer_enhanced.py --continuous")
    
    input("\nPress Enter when consumer is ready...")
    
    # Run producer 3 times
    num_runs = 3
    
    for run in range(1, num_runs + 1):
        print(f"\nProducer run {run}/{num_runs}")
        print("-" * 60)
        
        today = date.today()
        day = today - timedelta(days=run)
        
        generate_csv(day, rows=5)
        generate_json(day, rows=3)
        
        files = [
            config.INCOMING_DIR / f"data_{day.isoformat()}.csv",
            config.INCOMING_DIR / f"data_{day.isoformat()}.json",
        ]
        
        queue_mgr = QueueManager()
        
        try:
            queue_mgr.connect()
            
            for filepath in files:
                if filepath.exists():
                    queue_mgr.publish_file(filepath)
                    time.sleep(0.1)
            
            print(f"Published {len(files)} files")
            print(f"Queue size: {queue_mgr.get_queue_size()}")
            
        finally:
            queue_mgr.disconnect()
        
        if run < num_runs:
            print("Waiting 5 seconds before next run...")
            time.sleep(5)
    
    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)
    print(f"Sent {num_runs} batches of files")
    print("\nTo stop consumer: Press Ctrl+C in consumer terminal")


if __name__ == "__main__":
    main()