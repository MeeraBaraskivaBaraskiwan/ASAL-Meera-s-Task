import pandas as pd
from pathlib import Path
from typing import List
from data_extract.base_extractor import BaseExtractor

class CsvExtractor(BaseExtractor):
    
    def __init__(self, encoding: str = 'utf-8') -> None:
        self._encoding = encoding
    
    def extract(self, filepath: Path) -> pd.DataFrame:
        if not filepath.exists():
            raise FileNotFoundError(f"CSV file not found: {filepath}")
        
        if not self.can_handle(filepath):
            raise ValueError(f"CsvExtractor cannot handle: {filepath}")
        
        print(f"[CSV] Extracting: {filepath.name}")
        df: pd.DataFrame = pd.read_csv(filepath, encoding=self._encoding)
        print(f"[CSV] Loaded {len(df)} rows, {len(df.columns)} columns")
        return df
    
    def can_handle(self, filepath: Path) -> bool:
       return filepath.suffix.lower() in self.get_supported_extensions()
    
    def get_supported_extensions(self) -> List[str]:
           return ['.csv']