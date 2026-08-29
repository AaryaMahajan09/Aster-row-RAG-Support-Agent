from dataclasses import dataclass
from typing import Optional


@dataclass
class DocumentChunk:
    text: str
    filename: str
    heading: str
    status: str
    authority: str
    score: Optional[float] = None