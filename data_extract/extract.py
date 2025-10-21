import pandas as pd 
from pathlib import Path
from typing import List, Union
from data_extract.extractor_factory import ExtractorFactory

_factory: ExtractorFactory = ExtractorFactory()

def list_incoming_files(incoming_dir: Union[str, Path] = 'Incoming-data') -> List[Path]:
    if isinstance(incoming_dir, str):
        incoming_dir = Path(incoming_dir)
    files: List[Path] = []
    supported_extensions: List[str] = _factory.get_supported_extensions()
    for f in incoming_dir.iterdir():
        if f.is_file() and f.suffix.lower() in supported_extensions:
            files.append(f)
    return sorted(files)

def read_file(filepath: Union[str, Path]) -> pd.DataFrame:
  
    if isinstance(filepath, str):
        filepath = Path(filepath)
    
    extractor = _factory.get_extractor(filepath)
    return extractor.extract(filepath)


def get_factory() -> ExtractorFactory:
    return _factory

    


    