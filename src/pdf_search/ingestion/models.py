from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PageContent:
    document_name: str
    page_number: int
    text: str
    extraction_method: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class TextChunk:
    document_name: str
    page_number: int
    chunk_index: int
    extraction_method: str
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
