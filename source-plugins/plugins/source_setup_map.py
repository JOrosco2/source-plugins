from dataclasses import dataclass

@dataclass
class SourceInfo:
    module_number: int
    source_number: int
    wavelength: str
    state: int
