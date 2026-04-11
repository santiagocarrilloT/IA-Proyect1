from dataclasses import dataclass, field
from typing import Optional
from classes.puzzleMetrics import PuzzleMetrics

"""
Esta clase de encarga de mostrar los eventos que están ocurriendo, 
indispensable para la GUI
"""
#Type = 'expand', 'solved', 'log'
@dataclass
class PuzzleEvent:
    type: str 
    node_id: str = ""
    g: float = 0.0
    h: float = 0.0
    path: list[str] = field(default_factory=list)
    message: str = ""
    metrics: Optional[PuzzleMetrics] = None