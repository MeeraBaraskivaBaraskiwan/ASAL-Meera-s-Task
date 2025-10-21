from pathlib import Path
from typing import List
from data_extract.base_extractor import BaseExtractor
from data_extract.csv_extractor import CsvExtractor
from data_extract.json_extractor import JsonExtractor
from data_extract.txt_extractor import TxtExtractor


class ExtractorFactory:

    def __init__(self) -> None:
        self._extractors: List[BaseExtractor] = []
        self._register_default_extractors()
    
    def _register_default_extractors(self) -> None:
        self.register_extractor(CsvExtractor())
        self.register_extractor(JsonExtractor())
        self.register_extractor(TxtExtractor())
        print("[Factory] Registered: CSV, JSON, TXT")
    
    def register_extractor(self, extractor: BaseExtractor) -> None:
        self._extractors.append(extractor)
    
    def get_extractor(self, filepath: Path) -> BaseExtractor:
        for extractor in self._extractors:
            if extractor.can_handle(filepath):
                return extractor
        
        supported = self.get_supported_extensions()
        raise ValueError(
            f"No extractor for: {filepath.suffix}\n"
            f"Supported: {', '.join(supported)}"
        )
    
    def get_supported_extensions(self) -> List[str]:

        extensions: List[str] = []
        for extractor in self._extractors:
            extensions.extend(extractor.get_supported_extensions())
       
        return list(dict.fromkeys(extensions))