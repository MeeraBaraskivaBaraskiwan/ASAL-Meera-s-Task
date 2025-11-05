from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
import shutil
import sys
import time
import pika
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_extract.extract import read_file
from data_transform.transform import transform_data
from data_load.load import load_data_to_db
from data_report.report import generate_report
from queue_management.queue_manager import QueueManager
from queue_management.error_handler import ErrorHandler
from queue_management.error_solver import ErrorSolver
from config import config


class EnhancedFileProcessor:

    def __init__(self, engine: Engine):
        self.engine = engine
        self.error_handler = ErrorHandler()
        self.error_solver = ErrorSolver()
        self.successful_count = 0
        self.failed_count = 0
        self.fixed_count = 0
        
    def process_file_with_ack(self, filepath: Path, channel, method) -> bool:

        try:
            if not filepath.exists():
                error_msg = f"File not found: {filepath}"
                print(f"{error_msg}")
                self.error_handler.log_failure(filepath, error_msg, 1)
                self.failed_count += 1
                
               
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return False
            
     
            file_size_mb = filepath.stat().st_size / (1024 * 1024)
            if file_size_mb > 100:
                error_msg = f"File too large: {file_size_mb:.2f}MB"
                print(f"{error_msg}")
                self.error_handler.log_failure(filepath, error_msg, 1)
                self.failed_count += 1
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return False
            
           
            print(f"\n{'='*60}")
            print(f"Processing: {filepath.name}")
            print(f"{'='*60}")
            
          
            print("EXTRACT")
            df_raw = read_file(filepath)
            print(f"   Extracted {len(df_raw)} rows")
            
           
            print(" TRANSFORM")
            df_clean = transform_data(df_raw, source_file=filepath.name)
            print(f"   Transformed to {len(df_clean)} rows")
            
          
            print("LOAD")
            load_data_to_db(df_clean, config.TABLE_NAME, self.engine)
            print(f"   Loaded to database: {config.TABLE_NAME}")
            
        
            print(" ARCHIVE")
            config.ARCHIVE_DIR.mkdir(exist_ok=True)
            dest = config.ARCHIVE_DIR / filepath.name
            
            if dest.exists():
                timestamp = int(time.time())
                dest = config.ARCHIVE_DIR / f"{filepath.stem}_{timestamp}{filepath.suffix}"
            
            shutil.move(str(filepath), str(dest))
            print(f"   Moved to: {dest}")
            
        
            print(f" SUCCESS: {filepath.name}")
            print(f"{'='*60}\n")
            
       
            self.error_handler.mark_as_successful(filepath)
            self.successful_count += 1
            
            # CRITICAL: ACK the message
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return True
            
        except ValueError as e:
  
            error_msg = f"Invalid data: {str(e)}"
            print(f"\n ERROR in {filepath.name}")
            print(f"   {error_msg}")
            
      
            success = self._try_auto_fix(filepath, error_msg, channel, method)
            
            if not success:
                # Auto-fix failed - NACK without requeue
                self.error_handler.log_failure(filepath, error_msg, 1)
                self.failed_count += 1
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            
            return success
            
        except Exception as e:
      
            error_msg = f"Unexpected error: {str(e)}"
            print(f"\n ERROR in {filepath.name}")
            print(f"   {error_msg}")
            print(f"{'='*60}\n")
            
            self.error_handler.log_failure(filepath, error_msg, 1)
            self.failed_count += 1
            
            # CRITICAL: NACK without requeue
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return False
    
    def _try_auto_fix(self, filepath: Path, error_msg: str, channel, method) -> bool:

        print(f"\nAUTO-FIX ATTEMPT for {filepath.name}")
        print("="*60)
        
        success, fixed_filepath, fix_message = self.error_solver.attempt_fix(filepath, error_msg)
        
        if success and fixed_filepath:
            print(f" FIX SUCCESSFUL: {fix_message}")
            print(f"   Fixed file: {fixed_filepath}")
            
            try:
         
                print(f"\nRe-processing with fixed file...")
                
                df_raw = read_file(fixed_filepath)
                df_clean = transform_data(df_raw, source_file=filepath.name)
                load_data_to_db(df_clean, config.TABLE_NAME, self.engine)
                
             
                config.ARCHIVE_DIR.mkdir(exist_ok=True)
                
           
                dest = config.ARCHIVE_DIR / fixed_filepath.name
                if dest.exists():
                    dest = config.ARCHIVE_DIR / f"{fixed_filepath.stem}_{int(time.time())}{fixed_filepath.suffix}"
                shutil.move(str(fixed_filepath), str(dest))
                
   
                if filepath.exists():
                    broken_dest = config.ARCHIVE_DIR / f"BROKEN_{filepath.name}"
                    if broken_dest.exists():
                        broken_dest = config.ARCHIVE_DIR / f"BROKEN_{filepath.stem}_{int(time.time())}{filepath.suffix}"
                    shutil.move(str(filepath), str(broken_dest))
                
                print(f" SUCCESS AFTER AUTO-FIX: {filepath.name}")
                print(f"{'='*60}\n")
                
                self.error_handler.mark_as_successful(filepath)
                self.successful_count += 1
                self.fixed_count += 1
                
         
                channel.basic_ack(delivery_tag=method.delivery_tag)
                return True
                
            except Exception as retry_error:
                error_msg = f"Failed even after fix: {str(retry_error)}"
                print(f"STILL FAILED after auto-fix")
                print(f"   {error_msg}")
                print(f"{'='*60}\n")
                return False
        else:
            print(f" AUTO-FIX FAILED: {fix_message}")
            print(f"{'='*60}\n")
            return False
    
    def retry_failed_files(self, queue_mgr: QueueManager) -> None:
  
        failed_files = self.error_handler.get_failed_files()
        
        if not failed_files:
            print("\n No failed files to retry!")
            return
        
        print("\n" + "="*60)
        print("RETRYING FAILED FILES")
        print("="*60)
        print(f"Found {len(failed_files)} failed file(s)")
        
        for record in failed_files:
            filepath = Path(record['filepath'])
            
            if filepath.exists():
                print(f"\n Re-publishing: {filepath.name}")
                queue_mgr.publish_file(filepath)
                time.sleep(0.1)
            else:
                print(f"Cannot retry - file missing: {filepath.name}")


class ContinuousConsumer:

    
    def __init__(self):
        self.processor: Optional[EnhancedFileProcessor] = None
        self.engine: Optional[Engine] = None
        self.reconnect_delay = 5  
        self.max_reconnect_attempts = None 
        
    def initialize_database(self) -> bool:
    
        try:
            self.engine = create_engine(config.get_database_url())
            self.processor = EnhancedFileProcessor(self.engine)
            print(f"Connected to database: {config.DB_NAME}")
            return True
        except Exception as e:
            print(f" Database connection failed: {e}")
            return False
    
    def start_continuous_mode(self, generate_report_after: bool = True):

        print("="*60)
        print("CONTINUOUS CONSUMER MODE (TASK 10)")
        print("="*60)
        print(f"Database: {config.DB_NAME}")
        print(f"Queue: {config.RABBITMQ_QUEUE}")
        print(f"Archive: {config.ARCHIVE_DIR}")
        print("="*60)
        print("The consumer will run forever!")
        print("Press Ctrl+C to stop")
        print("="*60)
        
     
        if not self.initialize_database():
            return
        
        reconnect_count = 0
        

        while True:
            queue_mgr = None
            
            try:
         
                queue_mgr = QueueManager()
                queue_mgr.connect()
                
                if reconnect_count > 0:
                    print(f"\nReconnected successfully (attempt #{reconnect_count})")
                
                reconnect_count = 0 
        
                queue_size = queue_mgr.get_queue_size()
                print(f"\n Queue size: {queue_size} messages waiting")
                
             
                def on_message_callback(ch, method, properties, body):
                    """Process each message with proper Ack/Nack"""
                    import json
                    
                    try:
                        message = json.loads(body)
                        filepath = Path(message['filepath'])
                        
                        print(f"\ Received from queue: {filepath.name}")
                        
                        # Process with Ack/Nack handling
                        self.processor.process_file_with_ack(filepath, ch, method)
                        
                    except Exception as e:
                        print(f" Error in message callback: {e}")
                        # NACK on callback errors
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                
              
                queue_mgr.channel.basic_qos(prefetch_count=1)
                queue_mgr.channel.basic_consume(
                    queue=queue_mgr.queue_name,
                    on_message_callback=on_message_callback,
                    auto_ack=False 
                )
                
                print("\n" + "="*60)
                print(" LISTENING FOR NEW FILES...")
                print("   Waiting for messages in queue...")
                print("   (Press Ctrl+C to stop)")
                print("="*60)
                
               
                queue_mgr.channel.start_consuming()
                
            except KeyboardInterrupt:
                print("\n\nConsumer stopped by user (Ctrl+C)")
                
      
                self._print_summary(queue_mgr)
                
                if queue_mgr:
                    queue_mgr.disconnect()
                
                break  
                
            except pika.exceptions.AMQPConnectionError as e:
          
                reconnect_count += 1
                print(f"\nConnection lost: {e}")
                print(f" Reconnecting in {self.reconnect_delay} seconds... (attempt #{reconnect_count})")
                
                if queue_mgr:
                    try:
                        queue_mgr.disconnect()
                    except:
                        pass
                
                time.sleep(self.reconnect_delay)
                continue 
                
            except Exception as e:
                print(f"\n Unexpected error: {e}")
                print(f"Restarting in {self.reconnect_delay} seconds...")
                
                if queue_mgr:
                    try:
                        queue_mgr.disconnect()
                    except:
                        pass
                
                time.sleep(self.reconnect_delay)
                continue
    
    def start_batch_mode(self, generate_report_after: bool = True, retry_failed: bool = True):
 
        print("="*60)
        print(" BATCH CONSUMER MODE")
        print("="*60)
        
        if not self.initialize_database():
            return
        
        queue_mgr = QueueManager()
        
        try:
            queue_mgr.connect()
            
            queue_size = queue_mgr.get_queue_size()
            print(f" Queue size: {queue_size} messages waiting")
            
            if queue_size == 0:
                print("\n Queue is empty!")
                return
            
          
            def on_message_callback(ch, method, properties, body):
                import json
                message = json.loads(body)
                filepath = Path(message['filepath'])
                print(f"\n Received: {filepath.name}")
                self.processor.process_file_with_ack(filepath, ch, method)
            
      
            queue_mgr.channel.basic_qos(prefetch_count=1)
            queue_mgr.channel.basic_consume(
                queue=queue_mgr.queue_name,
                on_message_callback=on_message_callback,
                auto_ack=False  
            )
            
            print("\nProcessing current queue...")
            
       
            while queue_mgr.get_queue_size() > 0:
                queue_mgr.connection.process_data_events(time_limit=1)
            
            print("\nQueue processing complete!")
        
            if retry_failed and self.processor.error_handler.has_failed_files():
                print("\n" + "="*60)
                print(" RETRY PHASE")
                print("="*60)
                self.processor.retry_failed_files(queue_mgr)
            
    
            if generate_report_after:
                print("\n" + "="*60)
                print("GENERATING REPORT")
                print("="*60)
                try:
                    generate_report(self.engine)
                except Exception as e:
                    print(f" Report generation failed: {e}")
          
            self._print_summary(queue_mgr)
            
        except KeyboardInterrupt:
            print("\n\n Consumer stopped by user")
            self._print_summary(queue_mgr)
            
        finally:
            queue_mgr.disconnect()
    
    def _print_summary(self, queue_mgr: Optional[QueueManager]):
     
        print("\n" + "="*60)
        print(" CONSUMER SUMMARY")
        print("="*60)
        print(f" Successful: {self.processor.successful_count} files")
        print(f" Auto-fixed: {self.processor.fixed_count} files")
        print(f" Failed: {self.processor.failed_count} files")
        
        if queue_mgr:
            try:
                remaining = queue_mgr.get_queue_size()
                print(f"Remaining in queue: {remaining} messages")
            except:
                pass
        
        print("="*60)
        
        if self.processor:
            self.processor.error_handler.print_summary()



if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Enhanced Consumer with Fault Tolerance (Tasks 9 & 10)'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='TASK 10: Run in continuous mode (always listening)'
    )
    parser.add_argument(
        '--no-report',
        action='store_true',
        help='Skip report generation'
    )
    parser.add_argument(
        '--no-retry',
        action='store_true',
        help='Skip retrying failed files'
    )
    
    args = parser.parse_args()
    
    consumer = ContinuousConsumer()
    
    if args.continuous:
       
        consumer.start_continuous_mode(
            generate_report_after=not args.no_report
        )
    else:
    
        consumer.start_batch_mode(
            generate_report_after=not args.no_report,
            retry_failed=not args.no_retry
        )