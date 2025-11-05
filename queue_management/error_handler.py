from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import json


class ErrorHandler:
    def __init__(self, error_log_file: Path = Path("failed_files.json")):
        self.error_log_file = error_log_file
        self.failed_files: List[Dict[str, Any]] = []
        self._load_failed_files()
    
    def _load_failed_files(self) -> None:
        if self.error_log_file.exists():
            try:
                with open(self.error_log_file, 'r') as f:
                    self.failed_files = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load error log: {e}")
                self.failed_files = []
    
    def _save_failed_files(self) -> None:
        try:
            with open(self.error_log_file, 'w') as f:
                json.dump(self.failed_files, f, indent=2)
        except Exception as e:
            print(f"Error saving failed files log: {e}")
    
    def log_failure(self, filepath: Path, error_message: str, 
                    attempt_number: int = 1) -> None:
        failure_record = {
            'filepath': str(filepath),
            'filename': filepath.name,
            'error': error_message,
            'timestamp': datetime.now().isoformat(),
            'attempt_number': attempt_number,
            'status': 'failed'
        }
        existing_index = None
        for i, record in enumerate(self.failed_files):
            if record['filepath'] == str(filepath):
                existing_index = i
                break
        
        if existing_index is not None:
            self.failed_files[existing_index] = failure_record
        else:
            self.failed_files.append(failure_record)
        
        self._save_failed_files()
        print(f"FAILURE LOGGED: {filepath.name}")
        print(f" Error: {error_message}")
        print(f" Attempt: #{attempt_number}")
    
    def mark_as_successful(self, filepath: Path) -> None:
        self.failed_files = [
            f for f in self.failed_files 
            if f['filepath'] != str(filepath)
        ]
        self._save_failed_files()
        print(f"REMOVED FROM FAILED LIST: {filepath.name}")
    
    def get_failed_files(self) -> List[Dict[str, Any]]:
        return self.failed_files.copy()
    
    def has_failed_files(self) -> bool:
        return len(self.failed_files) > 0
    
    def clear_all(self) -> None:
        self.failed_files = []
        self._save_failed_files()
        print("Cleared all failed files from log")
    
    def print_summary(self) -> None:
        if not self.failed_files:
            print("\n No failed files!")
            return
        
        print("\n" + "="*60)
        print(" FAILED FILES SUMMARY")
        print("="*60)
        for i, record in enumerate(self.failed_files, 1):
            print(f"\n{i}. {record['filename']}")
            print(f"Error: {record['error']}")
            print(f"Attempts: {record['attempt_number']}")
            print(f"Last attempt: {record['timestamp']}")
        print("="*60)


