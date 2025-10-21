import pandas as pd
from pathlib import Path
from typing import List
from data_extract.base_extractor import BaseExtractor


class TxtExtractor(BaseExtractor):

    def __init__(self, encoding: str = 'utf-8', delimiter: str = ',') -> None:
        self._encoding = encoding
        self._delimiter = delimiter
    
    def extract(self, filepath: Path) -> pd.DataFrame:
        if not filepath.exists():
            raise FileNotFoundError(f"TXT file not found: {filepath}")
        
        if not self.can_handle(filepath):
            raise ValueError(f"TxtExtractor cannot handle: {filepath}")
        
        print(f"[TXT] Extracting: {filepath.name}")
   
        try:
            df: pd.DataFrame =  pd.read_csv(filepath,sep=self._delimiter, encoding=self._encoding)
        except Exception:
            print(f"[TXT] Tab delimiter failed, trying  TAB as delimiter")
            df = pd.read_csv(filepath, sep='\t', encoding=self._encoding)
        
        print(f"[TXT] Loaded {len(df)} rows, {len(df.columns)} columns")
        return df
    
    def can_handle(self, filepath: Path) -> bool:
         return filepath.suffix.lower() in self.get_supported_extensions()
    
    def get_supported_extensions(self) -> List[str]:
        return ['.txt']