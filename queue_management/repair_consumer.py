# queue_management/repair_consumer.py - FIXED VERSION
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
import shutil
import sys
import time
import pika
import json
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_extract.extract import read_file
from data_transform.transform import transform_data
from data_load.load import load_data_to_db
from queue_management.error_solver import ErrorSolver
from queue_management.queue_manager import queue_manager as EnhancedQueueManager
from reporting.logger import ProcessingLogger, PerformanceTimer
from config import config


class RepairFileProcessor:

    def __init__(self, engine: Engine, queue_mgr: EnhancedQueueManager):
        self.engine = engine
        self.queue_mgr = queue_mgr
        self.error_solver = ErrorSolver()
        self.logger = ProcessingLogger(engine)
        self.repaired_count = 0
        self.still_broken_count = 0
    
    def repair_file_with_ack(self, filepath: Path, error_message: str, channel, method) -> bool:
     
        
        timer = PerformanceTimer()
        timer.start()
        
        print(f"\n{'='*60}")
        print(f"  REPAIRING: {filepath.name}")
        print(f"{'='*60}")
        print(f"Original error: {error_message}")
        
     
        broken_file = config.BROKEN_DIR / filepath.name
        
        if not broken_file.exists():
            if not filepath.exists():
                print(f" File not found in any location")
                
                
                self.logger.log_file_processing(
                    filename=filepath.name,
                    filepath=str(filepath),
                    status='failed',
                    error_message=f"File not found for repair: {error_message}",
                    processing_time=timer.stop(),
                    source_queue='broken'
                )
                
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                self.still_broken_count += 1
                return False
            broken_file = filepath
        
     
        print(f" Attempting automatic repair...")
        success, fixed_filepath, fix_message = self.error_solver.attempt_fix(
            broken_file, error_message
        )
        
        if not success or not fixed_filepath:
            print(f" AUTO-REPAIR FAILED: {fix_message}")
            print(f"   File REMAINS in Broken-data folder: {broken_file}")
            print(f"{'='*60}\n")
         
            self.logger.log_file_processing(
                filename=filepath.name,
                filepath=str(filepath),
                status='failed',
                error_message=f"Repair failed: {fix_message}",
                processing_time=timer.stop(),
                source_queue='broken'
            )
            
            # Requeue for retry or keep in broken queue
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            self.still_broken_count += 1
            return False
        
      
        print(f" AUTO-REPAIR SUCCESSFUL: {fix_message}")
        print(f"   Fixed file: {fixed_filepath}")
        
        try:
            
            print(f"\n EXTRACT (from fixed file)")
            df_raw = read_file(fixed_filepath)
            print(f"   Extracted {len(df_raw)} rows")
            
            
            print(f" TRANSFORM")
            df_clean = transform_data(df_raw, source_file=broken_file.name)
            print(f"   Transformed to {len(df_clean)} rows")
            rows_processed = len(df_clean)
            
           
            print(f" LOAD")
            load_data_to_db(df_clean, config.TABLE_NAME, self.engine)
            print(f"   Loaded to database: {config.TABLE_NAME}")
            
            
            print(f"ARCHIVE")
            config.ARCHIVE_DIR.mkdir(exist_ok=True)
            
           
            dest = config.ARCHIVE_DIR / fixed_filepath.name
            if dest.exists():
                dest = config.ARCHIVE_DIR / f"{fixed_filepath.stem}_{int(time.time())}{fixed_filepath.suffix}"
            shutil.move(str(fixed_filepath), str(dest))
            print(f"    Archived FIXED file: {dest.name}")
            
           
            print(f" Broken original KEPT in: {config.BROKEN_DIR / broken_file.name}")
            print(f"   Original file remains for audit/debugging purposes")
            
            print(f"\nSUCCESS: {broken_file.name} repaired and processed!")
            print(f"{'='*60}\n")
            
           
            processing_time = timer.stop()
            self.logger.log_file_processing(
                filename=filepath.name,
                filepath=str(filepath),
                status='repaired',
                processing_time=processing_time,
                rows_processed=rows_processed,
                source_queue='broken'
            )
            self.logger.update_daily_summary(
                files_received=1,
                repaired=1,
                processing_time=processing_time,
                rows_processed=rows_processed
            )
            
            self.repaired_count += 1
            
            # ACK the message
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return True
            
        except Exception as retry_error:
            error_msg = f"Failed even after repair: {str(retry_error)}"
            print(f"\n STILL FAILED after repair")
            print(f"   {error_msg}")
            print(f"   File REMAINS in Broken-data: {broken_file}")
            print(f"{'='*60}\n")
            
         
            if fixed_filepath and fixed_filepath.exists():
                try:
                    fixed_filepath.unlink()
                    print(f"  Cleaned up failed fixed file")
                except:
                    pass
            
         
            processing_time = timer.stop()
            self.logger.log_file_processing(
                filename=filepath.name,
                filepath=str(filepath),
                status='failed',
                error_message=error_msg,
                processing_time=processing_time,
                source_queue='broken'
            )
            
       
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            self.still_broken_count += 1
            return False


class RepairConsumer:
  
    
    def __init__(self):
        self.processor: Optional[RepairFileProcessor] = None
        self.engine: Optional[Engine] = None
        self.queue_mgr: Optional[EnhancedQueueManager] = None
        self.reconnect_delay = 5
    
    def initialize(self) -> bool:
     
        try:
            self.engine = create_engine(config.get_database_url())
            print(f"Connected to database: {config.DB_NAME}")
            
            self.queue_mgr = EnhancedQueueManager()
            self.queue_mgr.connect()
            
            self.processor = RepairFileProcessor(self.engine, self.queue_mgr)
            
            return True
        except Exception as e:
            print(f" Initialization failed: {e}")
            return False
    
    def start_continuous_mode(self):
   
        print("="*60)
        print("  REPAIR CONSUMER - CONTINUOUS MODE (TASK 11)")
        print("="*60)
        print(f"Database: {config.DB_NAME}")
        print(f"Listening to: {config.RABBITMQ_BROKEN_QUEUE}")
        print(f"Broken Files Folder: {config.BROKEN_DIR}")
        print(f"Archive: {config.ARCHIVE_DIR}")
        print("="*60)
        print("  IMPORTANT: Broken originals STAY in Broken-data/")
        print("   Only FIXED files are archived!")
        print("="*60)
        print("This consumer repairs broken files automatically!")
        print("Press Ctrl+C to stop")
        print("="*60)
        
        if not self.initialize():
            return
        
        reconnect_count = 0
        
        while True:
            try:
                if reconnect_count > 0:
                    print(f"\n Reconnecting... (attempt #{reconnect_count})")
                    self.queue_mgr.connect()
                    print(f" Reconnected successfully")
                
                reconnect_count = 0
                
            
                broken_size = self.queue_mgr.get_queue_size(self.queue_mgr.broken_queue)
                print(f"\n Broken Queue Status: {broken_size} messages waiting")
                
                
                broken_files_count = len(list(config.BROKEN_DIR.glob('*'))) if config.BROKEN_DIR.exists() else 0
                print(f" Files in Broken-data folder: {broken_files_count}")
             
                main_size = self.queue_mgr.get_queue_size(self.queue_mgr.main_queue)
                self.processor.logger.log_queue_statistics(
                    main_queue_size=main_size,
                    broken_queue_size=broken_size,
                    total_processed=0,
                    total_failed=self.processor.still_broken_count,
                    total_repaired=self.processor.repaired_count
                )
                
              
                def on_message_callback(ch, method, properties, body):
                 
                    try:
                        
                        if isinstance(body, bytes):
                            body = body.decode('utf-8')
                        message = json.loads(body)
                        
                        filepath = Path(message['filepath'])
                        error_msg = message.get('error_message', 'Unknown error')
                        
                        print(f"\n Received from broken queue: {filepath.name}")
                        self.processor.repair_file_with_ack(filepath, error_msg, ch, method)
                        
                    except Exception as e:
                        print(f" Error in message callback: {e}")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                
               
                self.queue_mgr.channel.basic_qos(prefetch_count=1)
                self.queue_mgr.channel.basic_consume(
                    queue=self.queue_mgr.broken_queue,
                    on_message_callback=on_message_callback,
                    auto_ack=False
                )
                
                print("\n" + "="*60)
                print(" LISTENING FOR BROKEN FILES...")
                print("   Waiting for messages in broken queue...")
                print("   (Press Ctrl+C to stop)")
                print("="*60)
                
                self.queue_mgr.channel.start_consuming()
                
            except KeyboardInterrupt:
                print("\n\n  Repair consumer stopped by user (Ctrl+C)")
                self._print_summary()
                if self.queue_mgr:
                    self.queue_mgr.disconnect()
                break
                
            except pika.exceptions.AMQPConnectionError as e:
                reconnect_count += 1
                print(f"\n Connection lost: {e}")
                print(f" Reconnecting in {self.reconnect_delay} seconds...")
                
                if self.queue_mgr:
                    try:
                        self.queue_mgr.disconnect()
                    except:
                        pass
                
                time.sleep(self.reconnect_delay)
                self.queue_mgr = EnhancedQueueManager()
                continue
                
            except Exception as e:
                print(f"\n Unexpected error: {e}")
                print(f"Restarting in {self.reconnect_delay} seconds...")
                time.sleep(self.reconnect_delay)
                continue
    
    def _print_summary(self):
        print("\n" + "="*60)
        print(" REPAIR CONSUMER SUMMARY")
        print("="*60)
        print(f" Successfully repaired: {self.processor.repaired_count} files")
        print(f" Still broken: {self.processor.still_broken_count} files")
        
        if self.queue_mgr:
            try:
                broken_remaining = self.queue_mgr.get_queue_size(self.queue_mgr.broken_queue)
                print(f" Remaining in broken queue: {broken_remaining} messages")
            except:
                pass
        
        
        if config.BROKEN_DIR.exists():
            broken_files = list(config.BROKEN_DIR.glob('*'))
            print(f"Files still in Broken-data folder: {len(broken_files)}")
        
        print("="*60)


if __name__ == "__main__":
    consumer = RepairConsumer()
    consumer.start_continuous_mode()




    