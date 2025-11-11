from sqlalchemy import text
from sqlalchemy.engine import Engine
from datetime import datetime
from pathlib import Path
from typing import Optional
import time


class ProcessingLogger:

    def __init__(self, engine: Engine):
        self.engine = engine
    
    def log_file_processing(
        self,
        filename: str,
        filepath: str,
        status: str,
        error_message: Optional[str] = None,
        processing_time: Optional[float] = None,
        rows_processed: Optional[int] = None,
        source_queue: str = 'main',
        file_size_mb: Optional[float] = None
    ) -> None:
    
        try:
            with self.engine.begin() as conn:
                query = text("""
                    INSERT INTO file_processing_log 
                    (filename, filepath, status, error_message, processing_time, 
                     rows_processed, source_queue, file_size_mb)
                    VALUES 
                    (:filename, :filepath, :status, :error_message, :processing_time,
                     :rows_processed, :source_queue, :file_size_mb)
                """)
                
                conn.execute(query, {
                    'filename': filename,
                    'filepath': filepath,
                    'status': status,
                    'error_message': error_message,
                    'processing_time': processing_time,
                    'rows_processed': rows_processed,
                    'source_queue': source_queue,
                    'file_size_mb': file_size_mb
                })
                
        except Exception as e:
            print(f" Failed to log processing: {e}")
    
    def log_error_type(
        self,
        error_category: str,
        sample_filename: str
    ) -> None:
   
        try:
            with self.engine.begin() as conn:
           
                check_query = text("""
                    SELECT id FROM error_types 
                    WHERE error_category = :category
                """)
                result = conn.execute(check_query, {'category': error_category})
                existing = result.fetchone()
                
                if existing:
                 
                    update_query = text("""
                        UPDATE error_types 
                        SET error_count = error_count + 1,
                            last_occurred = CURRENT_TIMESTAMP,
                            sample_filename = :filename
                        WHERE error_category = :category
                    """)
                    conn.execute(update_query, {
                        'category': error_category,
                        'filename': sample_filename
                    })
                else:
                  
                    insert_query = text("""
                        INSERT INTO error_types (error_category, sample_filename)
                        VALUES (:category, :filename)
                    """)
                    conn.execute(insert_query, {
                        'category': error_category,
                        'filename': sample_filename
                    })
                    
        except Exception as e:
            print(f"  Failed to log error type: {e}")
    
    def log_queue_statistics(
        self,
        main_queue_size: int,
        broken_queue_size: int,
        total_processed: int,
        total_failed: int,
        total_repaired: int
    ) -> None:
   
        
        try:
            with self.engine.begin() as conn:
                query = text("""
                    INSERT INTO queue_statistics 
                    (main_queue_size, broken_queue_size, total_processed, 
                     total_failed, total_repaired)
                    VALUES 
                    (:main_size, :broken_size, :processed, :failed, :repaired)
                """)
                
                conn.execute(query, {
                    'main_size': main_queue_size,
                    'broken_size': broken_queue_size,
                    'processed': total_processed,
                    'failed': total_failed,
                    'repaired': total_repaired
                })
                
        except Exception as e:
            print(f"  Failed to log queue stats: {e}")
    
    def update_daily_summary(
        self,
        files_received: int = 1,
        successful: int = 0,
        failed: int = 0,
        repaired: int = 0,
        processing_time: Optional[float] = None,
        rows_processed: int = 0
    ) -> None:
   
        
        try:
            with self.engine.begin() as conn:
              
                check_query = text("""
                    SELECT id FROM daily_summary 
                    WHERE processing_date = CURRENT_DATE
                """)
                result = conn.execute(check_query)
                existing = result.fetchone()
                
                if existing:
             
                    update_query = text("""
                        UPDATE daily_summary SET
                            total_files_received = total_files_received + :received,
                            successful_files = successful_files + :successful,
                            failed_files = failed_files + :failed,
                            repaired_files = repaired_files + :repaired,
                            avg_processing_time = 
                                CASE 
                                    WHEN :proc_time IS NOT NULL THEN 
                                        (COALESCE(avg_processing_time, 0) + :proc_time) / 2
                                    ELSE avg_processing_time
                                END,
                            total_rows_processed = total_rows_processed + :rows
                        WHERE processing_date = CURRENT_DATE
                    """)
                    conn.execute(update_query, {
                        'received': files_received,
                        'successful': successful,
                        'failed': failed,
                        'repaired': repaired,
                        'proc_time': processing_time,
                        'rows': rows_processed
                    })
                else:
                 
                    insert_query = text("""
                        INSERT INTO daily_summary 
                        (total_files_received, successful_files, failed_files, 
                         repaired_files, avg_processing_time, total_rows_processed)
                        VALUES 
                        (:received, :successful, :failed, :repaired, :proc_time, :rows)
                    """)
                    conn.execute(insert_query, {
                        'received': files_received,
                        'successful': successful,
                        'failed': failed,
                        'repaired': repaired,
                        'proc_time': processing_time or 0.0,
                        'rows': rows_processed
                    })
                    
        except Exception as e:
            print(f"  Failed to update daily summary: {e}")
    
    def categorize_error(self, error_message: str) -> str:
    
        
        error_lower = error_message.lower()
        
        if 'file not found' in error_lower or 'not found' in error_lower:
            return 'File Not Found'
        elif 'empty' in error_lower or 'no columns' in error_lower:
            return 'Empty File'
        elif 'delimiter' in error_lower or 'only 1 column' in error_lower:
            return 'Delimiter Issue'
        elif 'json' in error_lower or 'parse' in error_lower:
            return 'JSON Parse Error'
        elif 'invalid' in error_lower or 'could not convert' in error_lower:
            return 'Invalid Data'
        elif 'database' in error_lower or 'connection' in error_lower:
            return 'Database Error'
        elif 'too large' in error_lower:
            return 'File Too Large'
        elif 'missing' in error_lower:
            return 'Missing Columns'
        else:
            return 'Other Error'


class PerformanceTimer:
  
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
       
        self.start_time = time.time()
    
    def stop(self) -> float:
       
        self.end_time = time.time()
        if self.start_time:
            return round(self.end_time - self.start_time, 3)
        return 0.0
    
    def get_elapsed(self) -> float:
     
        if self.start_time:
            return round(time.time() - self.start_time, 3)
        return 0.0
    

    