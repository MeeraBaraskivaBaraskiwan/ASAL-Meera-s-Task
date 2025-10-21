import pandas as pd
import json
from pathlib import Path
from typing import Any, Dict, List, Union
from data_extract.base_extractor import BaseExtractor


class JsonExtractor(BaseExtractor):
    def __init__(self, encoding: str = 'utf-8') -> None:
        self._encoding: str = encoding
    
    def extract(self, filepath: Path) -> pd.DataFrame:
        if not filepath.exists():
            raise FileNotFoundError(f"JSON file not found: {filepath}")
        
        if not self.can_handle(filepath):
            raise ValueError(f"JsonExtractor cannot handle: {filepath}")
        
        print(f"[JSON] Extracting: {filepath.name}")
        
        with open(filepath, 'r', encoding=self._encoding) as f:
            data = json.load(f)
        
        df = self._convert_to_dataframe(data, filepath)
        print(f"[JSON] Loaded {len(df)} rows, {len(df.columns)} columns")
        return df
    
    def can_handle(self, filepath: Path) -> bool:
         return filepath.suffix.lower() in self.get_supported_extensions()
    
    def get_supported_extensions(self) -> List[str]:
      
        return ['.json']
    
    def _convert_to_dataframe(self, data: Any, filepath: Path) -> pd.DataFrame:
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict):
             for key in ['data', 'products', 'items', 'records']:
                if key in data and isinstance(data[key], list):
                    return pd.DataFrame(data[key])
             return pd.DataFrame([data])
        else:
            raise ValueError(f"Unsupported JSON structure in {filepath}")
        


        