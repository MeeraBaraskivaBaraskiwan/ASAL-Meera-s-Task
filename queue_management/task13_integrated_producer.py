from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_sources.reviews_fetcher import ReviewsFetcher
from data_sources.shopping_fetcher import ShoppingTrendsFetcher
from data_transform.reviews_transformer import ReviewsTransformer
from data_transform.shopping_transformer import ShoppingTransformer
from queue_management.queue_manager import queue_manager as QueueManager
from config import config
import pandas as pd
import time
from datetime import date


class Task13IntegratedProducer:

    def __init__(self):
        self.queue_mgr = QueueManager()
        self.reviews_fetcher = ReviewsFetcher()
        self.shopping_fetcher = ShoppingTrendsFetcher()
        self.reviews_transformer = ReviewsTransformer()
        self.shopping_transformer = ShoppingTransformer()
    
    def generate_and_publish(
        self,
        num_review_batches: int = 3,
        batch_size: int = 1000,
        include_shopping: bool = True
    ):

        print("="*80)
        print("TASK 13: INTEGRATED PRODUCER (Using Existing Queues)")
        print("="*80)
        print(f"Target Queue: {config.RABBITMQ_QUEUE}")
        print(f"Broken Queue: {config.RABBITMQ_BROKEN_QUEUE}")
        print("="*80)
        
        try:
            self.queue_mgr.connect()
            generated_files = []
            

            print("\n PART 1: Review Files")
            print("─"*80)
            
          
            print("1. Downloading reviews dataset from Kaggle...")
            reviews_raw = self.reviews_fetcher.fetch_reviews()
            print(f"Downloaded {len(reviews_raw)} reviews")
            
       
            print("2. Computing sentiment scores (takes time)...")
            reviews_transformed = self.reviews_transformer.transform(
                reviews_raw,
                source_file="kaggle_reviews"
            )
            print(f"Transformed {len(reviews_transformed)} reviews")
            
           
            print(f"3. Creating {num_review_batches} review files...")
            for i in range(num_review_batches):
                start_idx = i * batch_size
                end_idx = start_idx + batch_size
                batch_df = reviews_transformed.iloc[start_idx:end_idx]
                
                if len(batch_df) == 0:
                    break
                
             
                filename = f"reviews_batch_{i+1}_{date.today().isoformat()}.csv"
                filepath = config.INCOMING_DIR / filename
                
                batch_df.to_csv(filepath, index=False)
                print(f"Created: {filename} ({len(batch_df)} rows)")
                
                
                self.queue_mgr.publish_to_main_queue(filepath)
                generated_files.append(filepath)
                time.sleep(0.2)
            
         
            if include_shopping:
                print("\nPART 2:Shopping Analytics Files")
                print("─"*80)
                
              
                print("1. Downloading shopping trends from Kaggle...")
                shopping_raw = self.shopping_fetcher.fetch_shopping_trends()
                print(f" Downloaded {len(shopping_raw)} records")
                
               
                print("2. Calculating discounts and revenue...")
                shopping_transformed = self.shopping_transformer.transform(
                    shopping_raw,
                    source_file="kaggle_shopping"
                )
                print(f" Transformed {len(shopping_transformed)} records")
                
            
                filename = f"shopping_analytics_{date.today().isoformat()}.csv"
                filepath = config.INCOMING_DIR / filename
                
                shopping_transformed.to_csv(filepath, index=False)
                print(f"  Created: {filename} ({len(shopping_transformed)} rows)")
                
            
                self.queue_mgr.publish_to_main_queue(filepath)
                generated_files.append(filepath)
            
         
            print("\n" + "="*80)
            print("PRODUCER SUMMARY")
            print("="*80)
            print(f"Generated: {len(generated_files)} files")
            print(f"Published: {len(generated_files)} messages to main queue")
            print("="*80)
            print("\n the consumers should now automatically process these files!")
            print("   Check Terminal 1 (main_consumer) and Terminal 2 (repair_consumer)")
            
        except FileNotFoundError as e:
            print(f"\n DATASET NOT FOUND")
            print(f"{e}")
            print("\n DOWNLOAD INSTRUCTIONS:")
            print("1. Go to Kaggle.com")
            print("2. Download these datasets:")
            print(" Women's E-Commerce Clothing Reviews")
            print("Customer Shopping Latest Trends")
            print(f"3. Place CSV files in: {Path('external_data_cache').absolute()}/")
            
        except Exception as e:
            print(f"\n ERROR: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            self.queue_mgr.disconnect()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Task 13: Generate analytics files and publish to queue'
    )
    parser.add_argument(
        '--batches',
        type=int,
        default=3,
        help='Number of review file batches to create'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Reviews per batch file'
    )
    parser.add_argument(
        '--no-shopping',
        action='store_true',
        help='Skip shopping analytics file'
    )
    
    args = parser.parse_args()
    
    producer = Task13IntegratedProducer()
    producer.generate_and_publish(
        num_review_batches=args.batches,
        batch_size=args.batch_size,
        include_shopping=not args.no_shopping
    )


    