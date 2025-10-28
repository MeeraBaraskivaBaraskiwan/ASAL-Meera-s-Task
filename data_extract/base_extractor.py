from abc import ABC, abstractmethod
import pandas as pd
from pathlib import Path
from typing import List

class BaseExtractor(ABC):
    
    @abstractmethod
    def extract(self, filepath: Path) -> pd.DataFrame:
         raise NotImplementedError("extract() must be implemented by subclasses of BaseExtractor")
    
    @abstractmethod
    def can_handle(self, filepath: Path) -> bool:
         raise NotImplementedError("can_handle() must be implemented by subclasses of BaseExtractor")

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
         raise NotImplementedError("get_supported_extensions() must be implemented by subclasses of BaseExtractor")