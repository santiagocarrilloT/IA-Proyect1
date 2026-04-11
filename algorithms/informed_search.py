"""
informed_search.py - Algoritmo A* para resolver Puzzles (Búsqueda Informada)
Cada nodo bloqueado tiene un subgrafo independiente; A* lo resuelve con heurística.
"""

import heapq
from dataclasses import dataclass, field
from typing import Generator, Optional
from graph import Puzzle


# ─── MÉTRICAS DEL PUZZLE ────────────z─────────────────────────────────────────
@dataclass
class PuzzleMetrics:
    nodes_expanded: int = 0
    total_cost: float = 0.0
    solution_path: list[str] = field(default_factory=list)
    execution_time: float = 0.0    # segundos

    def __str__(self):
        return (f"Nodos expandidos: {self.nodes_expanded} | "
                f"Costo total: {self.total_cost:.1f} | "
                f"Camino: {' → '.join(self.solution_path)} | "
                f"Tiempo: {self.execution_time:.4f}s")


# ─── NODO INTERNO DE A* ───────────────────────────────────────────────────────
@dataclass(order=True)
class AStarNode:
    """
    Nodo en la cola de prioridad de A*.
    f = g + h  (costo acumulado + heurística)
    Se ordena por f para que heapq entregue siempre el menor.
    """
    f: float
    g: float = field(compare=False)
    h: float = field(compare=False)
    node_id: str = field(compare=False)
    path: list[str] = field(compare=False, default_factory=list)


# ─── EVENTO DE PUZZLE (para la GUI) ──────────────────────────────────────────
@dataclass
class PuzzleEvent:
    type: str          # "expand", "solved", "log"
    node_id: str = ""
    g: float = 0.0
    h: float = 0.0
    path: list[str] = field(default_factory=list)
    message: str = ""
    metrics: Optional[PuzzleMetrics] = None


# ─── A* ──────────────────────────────────────────────────────────────────────
def astar(puzzle: Puzzle,
          metrics: PuzzleMetrics) -> Generator[PuzzleEvent, None, None]:
    """
    Algoritmo A* para resolver un puzzle (subproblema de búsqueda informada).

    Propiedades:
    - COMPLETO: Si existe solución, la encuentra.
    - ÓPTIMO: Porque h(n) es admisible (nunca sobreestima el costo real).
    - f(n) = g(n) + h(n)
        g(n): costo acumulado desde el inicio
        h(n): heurística (distancia euclidiana al goal)

    Yields PuzzleEvent en cada expansión para que la GUI lo visualice.
    """
    start_id = puzzle.start
    goal_id  = puzzle.goal

    h0 = puzzle.heuristic(start_id)
    start_node = AStarNode(f=h0, g=0.0, h=h0,
                           node_id=start_id, path=[start_id])

    # Cola de prioridad (min-heap) ordenada por f
    open_heap: list[AStarNode] = [start_node]
    # g-scores: costo mínimo conocido para llegar a cada nodo
    g_score: dict[str, float] = {start_id: 0.0}
    closed: set[str] = set()

    yield PuzzleEvent("log", start_id, 0, h0, [start_id],
                      f"▶ A* iniciando en {{{start_id}}} | h={h0}")

    while open_heap:
        current = heapq.heappop(open_heap)

        if current.node_id in closed:
            continue
        closed.add(current.node_id)

        metrics.nodes_expanded += 1

        yield PuzzleEvent(
            type="expand",
            node_id=current.node_id,
            g=current.g,
            h=current.h,
            path=current.path,
            message=(f"> Expandiendo {{{current.node_id}}} "
                     f"| f={current.f:.1f} g={current.g:.1f} h={current.h:.1f}")
        )

        # ¿Meta?
        if current.node_id == goal_id:
            metrics.total_cost = current.g
            metrics.solution_path = current.path
            yield PuzzleEvent(
                type="solved",
                node_id=current.node_id,
                g=current.g,
                h=0,
                path=current.path,
                message=(f"✓ Puzzle Resuelto! Costo={current.g:.1f} | "
                         f"Camino: {' → '.join(current.path)}"),
                metrics=metrics
            )
            return

        # Expandir vecinos
        for neighbor_id, edge_weight in puzzle.neighbors(current.node_id):
            if neighbor_id in closed:
                continue

            tentative_g = current.g + edge_weight

            # Solo procesar si encontramos un camino mejor
            if neighbor_id not in g_score or tentative_g < g_score[neighbor_id]:
                g_score[neighbor_id] = tentative_g
                h = puzzle.heuristic(neighbor_id)
                f = tentative_g + h
                new_node = AStarNode(
                    f=f, g=tentative_g, h=h,
                    node_id=neighbor_id,
                    path=current.path + [neighbor_id]
                )
                heapq.heappush(open_heap, new_node)

    yield PuzzleEvent("log", "", 0, 0, [],
                      "✗ Puzzle sin solución.")


if __name__ == "__main__":
    import time
    from graph import build_escape_room

    _, puzzles, _ = build_escape_room()

    for pid, puzzle in puzzles.items():
        print(f"\n=== {puzzle.name} ({pid}) ===")
        metrics = PuzzleMetrics()
        t0 = time.time()
        for event in astar(puzzle, metrics):
            print(f"  [{event.type.upper()}] {event.message}")
        metrics.execution_time = time.time() - t0
        print(f"\n  {metrics}")
