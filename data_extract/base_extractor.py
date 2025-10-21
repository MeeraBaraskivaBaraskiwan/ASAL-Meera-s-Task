from abc import ABC, abstractmethod
import pandas as pd
from pathlib import Path
from typing import List

class BaseExtractor(ABC):
    
    @abstractmethod
    def extract(self, filepath: Path) -> pd.DataFrame:
        pass
    
    @abstractmethod
    def can_handle(self, filepath: Path) -> bool:
        pass

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
         pass