from dataclasses import dataclass, field

#Clase usada para almacenar las métricas del scape room
@dataclass
class PuzzleMetrics:
    nodes_expanded: int = 0
    total_cost: int = 0
    solution_path: list[str] = field(default_factory=list)
    execution_time: float = 0.0

    def __str__(self):
        return (f"Nodos expandidos: {self.nodes_expanded} | "
                f"Costo total: {self.total_cost:.1f} | "
                f"Camino: {' → '.join(self.solution_path)} | "
                f"Tiempo: {self.execution_time:.4f}s")
