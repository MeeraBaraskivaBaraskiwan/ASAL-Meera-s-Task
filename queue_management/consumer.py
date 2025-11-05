from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
import shutil
import sys
import time
sys.path.insert(0, str(Path(__file__).parent.parent))
from data_extract.extract import read_file
from data_transform.transform import transform_data
from data_load.load import load_data_to_db
from data_report.report import generate_report
from queue_management.queue_manager import QueueManager
from queue_management.error_handler import ErrorHandler
from queue_management.error_solver import ErrorSolver
from config import config


class FileProcessor:
    def __init__(self, engine: Engine, error_handler: ErrorHandler):
        self.engine = engine
        self.error_handler = error_handler
        self.error_solver = ErrorSolver()
        self.successful_count = 0
        self.failed_count = 0
        self.fixed_count = 0

    def process_file(self,filepath: Path, retry_attempt: int = 1) -> bool:
        try:
            if not filepath.exists():
                print(f"File not found: {filepath}")
                print(f"{filepath.name}: {error_msg}")
                self.error_handler.log_failure(filepath, error_msg, retry_attempt)
                self.failed_count += 1
                return False
            
            file_size_mb = filepath.stat().st_size / (1024 * 1024)
            if file_size_mb > 100:
                error_msg = f"File too large: {file_size_mb:.2f}MB (max 100MB)"
                print(f"{error_msg}")
                self.error_handler.log_failure(filepath, error_msg, retry_attempt)
                self.failed_count += 1
                return False
        
            print(f"\n{'='*60}")
            print(f"Processing: {filepath.name}")
            if retry_attempt > 1:
                print(f"Retry attempt #{retry_attempt}")
            print(f"{'='*60}")
        
            print("\nEXTRACT")
            df_raw = read_file(filepath)
            print(f"Extracted {len(df_raw)} rows")
        
            print("\nTRANSFORM")
            df_clean = transform_data(df_raw, source_file=filepath.name)
            print(f"Transformed to {len(df_clean)} rows")
        
            print("\n LOAD")
            load_data_to_db(df_clean,config.TABLE_NAME, self.engine)
            print(f"Loaded to database table: {config.TABLE_NAME}")
   
            print("\n ARCHIVE")
            config.ARCHIVE_DIR.mkdir(exist_ok=True)
            dest = config.ARCHIVE_DIR / filepath.name

            if dest.exists():
                timestamp = int(time.time())
                dest = config.ARCHIVE_DIR / f"{filepath.stem}_{timestamp}{filepath.suffix}"
            
            shutil.move(str(filepath), str(dest))
            print(f"Moved to: {dest}")
        
            print(f"\nSuccessfully processed: {filepath.name}")
            print(f"{'='*60}\n")

            self.error_handler.mark_as_successful(filepath)
            self.successful_count += 1
            
            return True
            
        
        except FileNotFoundError as e:
            error_msg = f"File not found: {str(e)}"
            print(f"\n ERROR in {filepath.name}")
            print(f"   {error_msg}")
            print(f"{'='*60}\n")
            self.error_handler.log_failure(filepath, error_msg, retry_attempt)
            self.failed_count += 1
            return False
            
        except ValueError as e:
            error_msg = f"Invalid data: {str(e)}"
            print(f"\n ERROR in {filepath.name}")
            print(f"   {error_msg}")
            return self._try_fix_and_retry(filepath, error_msg, retry_attempt)
        
        except Exception as e:
            if "database" in str(e).lower() or "connection" in str(e).lower():
                error_msg = f"Database error: {str(e)}"
                print(f"\nDATABASE ERROR in {filepath.name}")
                print(f"   {error_msg}")
                print(f"   Retrying in 5 seconds...")
                time.sleep(5)
            
  
                try:
                    self.engine = create_engine(config.get_database_url())
                    print(" Database reconnected!")
                    return self.process_file(filepath, retry_attempt)
                except:
                    print(" Database still unreachable")
                    self.error_handler.log_failure(filepath, error_msg, retry_attempt)
                    self.failed_count += 1
                    return False
        
     
            elif isinstance(e, ValueError):
                error_msg = f"Invalid data: {str(e)}"
                print(f"\nERROR in {filepath.name}")
                print(f"   {error_msg}")
                return self._try_fix_and_retry(filepath, error_msg, retry_attempt)
        
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"\nERROR in {filepath.name}")
            print(f"   {error_msg}")
            return self._try_fix_and_retry(filepath, error_msg, retry_attempt)
    
    def _try_fix_and_retry(self, filepath: Path, error_msg: str, retry_attempt: int) -> bool:
        print(f"\n AUTO-FIX ATTEMPT for {filepath.name}")
        print("="*60)
        
        success, fixed_filepath, fix_message = self.error_solver.attempt_fix(filepath, error_msg)
        
        if success and fixed_filepath:
            print(f"FIX SUCCESSFUL: {fix_message}")
            print(f"Fixed file: {fixed_filepath}")
            
            print(f"\nRe-processing with fixed file...")
            
            try:
                print("\nEXTRACT (from fixed file)")
                df_raw = read_file(fixed_filepath)
                print(f"   Extracted {len(df_raw)} rows")
                
                print("\nTRANSFORM")
                df_clean = transform_data(df_raw, source_file=filepath.name)
                print(f"   Transformed to {len(df_clean)} rows")
                
                print("\nLOAD")
                load_data_to_db(df_clean, config.TABLE_NAME, self.engine)
                print(f"   Loaded to database: {config.TABLE_NAME}")
                
                print("\nARCHIVE")
                config.ARCHIVE_DIR.mkdir(exist_ok=True)
                dest = config.ARCHIVE_DIR / fixed_filepath.name
                
                if dest.exists():
                    timestamp = int(time.time())
                    dest = config.ARCHIVE_DIR / f"{fixed_filepath.stem}_{timestamp}{fixed_filepath.suffix}"
                
                shutil.move(str(fixed_filepath), str(dest))
                print(f"   Moved fixed file to: {dest}")
                
                if filepath.exists():
                    broken_dest = config.ARCHIVE_DIR / f"BROKEN_{filepath.name}"
                    if broken_dest.exists():
                        broken_dest = config.ARCHIVE_DIR / f"BROKEN_{filepath.stem}_{int(time.time())}{filepath.suffix}"
                    
                    shutil.move(str(filepath), str(broken_dest))
                    print(f"   Moved broken file to: {broken_dest}")
                
                print(f"\nSUCCESS AFTER AUTO-FIX: {filepath.name}")
                print(f"{'='*60}\n")
                
                self.error_handler.mark_as_successful(filepath)
                self.successful_count += 1
                self.fixed_count += 1
                
                return True
                
            except Exception as retry_error:
                error_msg = f"Failed even after fix: {str(retry_error)}"
                print(f"\nSTILL FAILED after auto-fix")
                print(f"   {error_msg}")
                print(f"{'='*60}\n")
                self.error_handler.log_failure(filepath, error_msg, retry_attempt)
                self.failed_count += 1
                return False
        else:
            print(f"AUTO-FIX FAILED: {fix_message}")
            print(f"{'='*60}\n")
            self.error_handler.log_failure(filepath, error_msg, retry_attempt)
            self.failed_count += 1
            return False
    
    def retry_failed_files(self, max_retries: int = 3) -> None:
  
        failed_files = self.error_handler.get_failed_files()
        
        if not failed_files:
            print("\nNo failed files to retry!")
            return
        
        print("\n" + "="*60)
        print("RETRYING FAILED FILES (with auto-fix)")
        print("="*60)
        print(f"Found {len(failed_files)} failed file(s)")
        
        for record in failed_files:
            filepath = Path(record['filepath'])
            attempt_number = record.get('attempt_number', 1) + 1
            
            if attempt_number > max_retries:
                print(f"\nSkipping {filepath.name} (max retries reached)")
                continue
            
            print(f"\nRetrying: {filepath.name} (Attempt #{attempt_number})")
            self.process_file(filepath, retry_attempt=attempt_number)
            time.sleep(0.5)




def start_consumer(
     continuous_mode: bool = False,generate_report_after: bool = True,  max_messages: int = None, retry_failed: bool = True) -> None:

    print("="*60)
    if continuous_mode:
        print("CONSUMER: CONTINUOUS MODE (TASK 10)")
        print("The consumer will run forever!")

    else:
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
    error_handler = ErrorHandler()
    processor = FileProcessor(engine, error_handler)
    
    queue_mgr = QueueManager()
    
    try:
        queue_mgr.connect()
        
        queue_size = queue_mgr.get_queue_size()
        print(f"Queue size: {queue_size} messages waiting")

        if not continuous_mode and queue_size == 0:
            print("\nQueue is empty!")
            if retry_failed and error_handler.has_failed_files():
                print("But we have failed files to retry...")
            else:
                return
        
        processed_count = [0]
        
        def callback(filepath: Path):
            processor.process_file(filepath)
            processed_count[0] += 1
            
            if max_messages and processed_count[0] >= max_messages:
                print(f"\nReached maximum messages ({max_messages})")
                if not continuous_mode:
                    queue_mgr.channel.stop_consuming()
        
        if continuous_mode:
            print("\n" + "="*60)
            print("LISTENING FOR NEW FILES...")
            print("   Waiting for messages in queue...")
            print("="*60)
            
            queue_mgr.consume_files(callback)
            
        else:
           if queue_size > 0:
             print("\n" + "="*60)
             print("PROCESSING CURRENT QUEUE")
             print("="*60)
             queue_mgr.consume_files(callback)
        
    except KeyboardInterrupt:
        print("\n\nConsumer stopped by user (Ctrl+C)")
        
    except Exception as e:
        print(f"\nConsumer error: {e}")
        
    finally:
        if retry_failed and not continuous_mode:
            if error_handler.has_failed_files():
                print("\n" + "="*60)
                print("RETRY PHASE (with auto-fix)")
                print("="*60)
                processor.retry_failed_files()
      
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
        print(f"Successful: {processor.successful_count} files")
        print(f"Auto-fixed: {processor.fixed_count} files")
        print(f"Failed: {processor.failed_count} files")
        print(f"Remaining in queue: {queue_mgr.get_queue_size()} messages")
        print("="*60)
        error_handler.print_summary()
        queue_mgr.disconnect()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Consume and process files from queue')
    parser.add_argument('--continuous', action='store_true', 
                        help='TASK 10: Run in continuous mode')
    parser.add_argument('--no-report', action='store_true', help='Skip report generation')
    parser.add_argument('--max', type=int, help='Maximum number of files to process')
    parser.add_argument('--no-retry', action='store_true',
                        help='Skip retrying failed files')
    
    args = parser.parse_args()
    
    start_consumer(
        continuous_mode=args.continuous,
        generate_report_after=not args.no_report,
        max_messages=args.max,
        retry_failed=not args.no_retry
    )

    