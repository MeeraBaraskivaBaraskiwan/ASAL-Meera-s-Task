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
from queue_management.queue_manager import queue_manager as EnhancedQueueManager
from reporting.logger import ProcessingLogger, PerformanceTimer
from config import config


class MainFileProcessor:
    def __init__(self, engine: Engine, queue_mgr: EnhancedQueueManager):
        self.engine = engine
        self.queue_mgr = queue_mgr
        self.logger = ProcessingLogger(engine)
        self.successful_count = 0
        self.failed_count = 0
    
    def process_file_with_ack(self, filepath: Path, channel, method) -> bool:

        timer = PerformanceTimer()
        timer.start()
        
        try:
            if not filepath.exists():
                error_msg = f"File not found: {filepath}"
                print(f" {error_msg}")
                
         
                self.logger.log_file_processing(
                    filename=filepath.name,
                    filepath=str(filepath),
                    status='failed',
                    error_message=error_msg,
                    processing_time=timer.stop(),
                    source_queue='main'
                )
                self.logger.log_error_type('File Not Found', filepath.name)
                self.logger.update_daily_summary(files_received=1, failed=1)
                
                # NACK the message from main queue
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                self.failed_count += 1
                return False
            
            file_size_mb = filepath.stat().st_size / (1024 * 1024)
            if file_size_mb > 100:
                error_msg = f"File too large: {file_size_mb:.2f}MB"
                print(f" {error_msg}")
                
              
                self.logger.log_file_processing(
                    filename=filepath.name,
                    filepath=str(filepath),
                    status='failed',
                    error_message=error_msg,
                    processing_time=timer.stop(),
                    source_queue='main',
                    file_size_mb=file_size_mb
                )
                self.logger.log_error_type('File Too Large', filepath.name)
                self.logger.update_daily_summary(files_received=1, failed=1)
                
   
                broken_dest = self._move_to_broken(filepath)
                self.queue_mgr.publish_to_broken_queue(broken_dest if broken_dest else filepath, error_msg)
                self.failed_count += 1
                
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return False
            
          
            print(f"\n{'='*60}")
            print(f" Processing: {filepath.name}")
            print(f"{'='*60}")
            
           
            print(" EXTRACT")
            df_raw = read_file(filepath)
            print(f"   Extracted {len(df_raw)} rows")
            
           
            print(" TRANSFORM")
            df_clean = transform_data(df_raw, source_file=filepath.name)
            print(f"   Transformed to {len(df_clean)} rows")
            rows_processed = len(df_clean)
            
            
            print(" LOAD")
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
            
     
            processing_time = timer.stop()
            self.logger.log_file_processing(
                filename=filepath.name,
                filepath=str(filepath),
                status='success',
                processing_time=processing_time,
                rows_processed=rows_processed,
                source_queue='main',
                file_size_mb=file_size_mb
            )
            self.logger.update_daily_summary(
                files_received=1,
                successful=1,
                processing_time=processing_time,
                rows_processed=rows_processed
            )
            
            self.successful_count += 1
            
            # ACK the message
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return True
            
        except ValueError as e:
            
            error_msg = f"Invalid data: {str(e)}"
            print(f"\n ERROR in {filepath.name}")
            print(f"   {error_msg}")
            
          
            processing_time = timer.stop()
            self.logger.log_file_processing(
                filename=filepath.name,
                filepath=str(filepath),
                status='failed',
                error_message=error_msg,
                processing_time=processing_time,
                source_queue='main'
            )
            error_category = self.logger.categorize_error(error_msg)
            self.logger.log_error_type(error_category, filepath.name)
            self.logger.update_daily_summary(files_received=1, failed=1)
            
          
            broken_dest = self._move_to_broken(filepath)
            
            
            self.queue_mgr.publish_to_broken_queue(broken_dest if broken_dest else filepath, error_msg)
            self.failed_count += 1
            
            # NACK without requeue
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return False
            
        except Exception as e:
         
            error_msg = f"Unexpected error: {str(e)}"
            print(f"\n ERROR in {filepath.name}")
            print(f"   {error_msg}")
            print(f"{'='*60}\n")
            
          
            processing_time = timer.stop()
            self.logger.log_file_processing(
                filename=filepath.name,
                filepath=str(filepath),
                status='failed',
                error_message=error_msg,
                processing_time=processing_time,
                source_queue='main'
            )
            error_category = self.logger.categorize_error(error_msg)
            self.logger.log_error_type(error_category, filepath.name)
            self.logger.update_daily_summary(files_received=1, failed=1)
            
            broken_dest = self._move_to_broken(filepath)
            self.queue_mgr.publish_to_broken_queue(broken_dest if broken_dest else filepath, error_msg)
            self.failed_count += 1
            
            
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return False
    
    def _move_to_broken(self, filepath: Path) -> Optional[Path]:
        try:
            if filepath.exists():
                config.BROKEN_DIR.mkdir(exist_ok=True)
                dest = config.BROKEN_DIR / filepath.name
                
                
                if dest.exists():
                    dest = config.BROKEN_DIR / f"{filepath.stem}_{int(time.time())}{filepath.suffix}"
                
                shutil.move(str(filepath), str(dest))
                print(f" Moved to Broken-data: {dest.name}")
                return dest
        except Exception as e:
            print(f" Could not move to Broken-data: {e}")
        return None


class MainConsumer:
  
    
    def __init__(self):
        self.processor: Optional[MainFileProcessor] = None
        self.engine: Optional[Engine] = None
        self.queue_mgr: Optional[EnhancedQueueManager] = None
        self.reconnect_delay = 5
    
    def initialize(self) -> bool:
   
        try:
            self.engine = create_engine(config.get_database_url())
            print(f" Connected to database: {config.DB_NAME}")
            
            self.queue_mgr = EnhancedQueueManager()
            self.queue_mgr.connect()
            
            self.processor = MainFileProcessor(self.engine, self.queue_mgr)
            
            return True
        except Exception as e:
            print(f" Initialization failed: {e}")
            return False
    
    def start_continuous_mode(self):
       
        print("="*60)
        print(" MAIN CONSUMER - CONTINUOUS MODE (TASK 11)")
        print("="*60)
        print(f"Database: {config.DB_NAME}")
        print(f"Main Queue: {config.RABBITMQ_QUEUE}")
        print(f"Broken Queue: {config.RABBITMQ_BROKEN_QUEUE}")
        print(f"Archive: {config.ARCHIVE_DIR}")
        print(f"Broken Files: {config.BROKEN_DIR}")
        print("="*60)
        print("The consumer will run forever!")
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
                
            
                main_size = self.queue_mgr.get_queue_size(self.queue_mgr.main_queue)
                broken_size = self.queue_mgr.get_queue_size(self.queue_mgr.broken_queue)
                print(f"\n Queue Status:")
                print(f"   Main Queue: {main_size} messages")
                print(f"   Broken Queue: {broken_size} messages")
                
             
                self.processor.logger.log_queue_statistics(
                    main_queue_size=main_size,
                    broken_queue_size=broken_size,
                    total_processed=self.processor.successful_count,
                    total_failed=self.processor.failed_count,
                    total_repaired=0
                )
                
              
                def on_message_callback(ch, method, properties, body):
                    
                    try:
                     
                        if isinstance(body, bytes):
                            body = body.decode('utf-8')
                        message = json.loads(body)
                        
                        filepath = Path(message['filepath'])
                        print(f"\n Received from main queue: {filepath.name}")
                        self.processor.process_file_with_ack(filepath, ch, method)
                        
                    except Exception as e:
                        print(f"Error in message callback: {e}")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                
          
                self.queue_mgr.channel.basic_qos(prefetch_count=1)
                self.queue_mgr.channel.basic_consume(
                    queue=self.queue_mgr.main_queue,
                    on_message_callback=on_message_callback,
                    auto_ack=False
                )
                
                print("\n" + "="*60)
                print(" LISTENING FOR NEW FILES...")
                print("   Waiting for messages in main queue...")
                print("   (Press Ctrl+C to stop)")
                print("="*60)
                
                self.queue_mgr.channel.start_consuming()
                
            except KeyboardInterrupt:
                print("\n\n Consumer stopped by user (Ctrl+C)")
                self._print_summary()
                if self.queue_mgr:
                    self.queue_mgr.disconnect()
                break
                
            except pika.exceptions.AMQPConnectionError as e:
                reconnect_count += 1
                print(f"\n Connection lost: {e}")
                print(f"Reconnecting in {self.reconnect_delay} seconds...")
                
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
        print(" MAIN CONSUMER SUMMARY")
        print("="*60)
        print(f" Successful: {self.processor.successful_count} files")
        print(f" Failed: {self.processor.failed_count} files")
        
        if self.queue_mgr:
            try:
                main_remaining = self.queue_mgr.get_queue_size(self.queue_mgr.main_queue)
                broken_waiting = self.queue_mgr.get_queue_size(self.queue_mgr.broken_queue)
                print(f" Remaining in main queue: {main_remaining} messages")
                print(f" Waiting in broken queue: {broken_waiting} messages")
            except:
                pass
        
        print("="*60)


if __name__ == "__main__":
    consumer = MainConsumer()
    consumer.start_continuous_mode()




    