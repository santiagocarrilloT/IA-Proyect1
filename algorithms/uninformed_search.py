"""
uninformed_search.py - Algoritmos de Búsqueda No Informada
Implementa BFS (Amplitud) y DFS (Profundidad) para el grafo global.
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Generator, Optional
from graph import EscapeGraph, NodeState


# ─── MÉTRICAS ────────────────────────────────────────────────────────────────
@dataclass
class SearchMetrics:
    nodes_expanded: int = 0
    max_depth: int = 0
    total_cost: float = 0.0
    execution_time: float = 0.0
    solution_path: list[str] = field(default_factory=list)

    def __str__(self):
        return (f"Nodos expandidos: {self.nodes_expanded} | "
                f"Profundidad: {self.max_depth} | "
                f"Costo: {self.total_cost:.1f} | "
                f"Tiempo: {self.execution_time:.4f}s | "
                f"Camino: {' → '.join(self.solution_path)}")


# ─── EVENTO DE BÚSQUEDA (para la GUI) ────────────────────────────────────────
@dataclass
class SearchEvent:
    """Evento que se envía a la GUI en cada paso de la búsqueda."""
    type: str                        # "expand", "locked", "goal", "unlock", "log"
    node: Optional[str] = None       # Nodo actual
    path: list[str] = field(default_factory=list)
    message: str = ""
    puzzle_id: Optional[str] = None  # Si encontró un nodo bloqueado
    metrics: Optional[SearchMetrics] = None


# ─── BFS ─────────────────────────────────────────────────────────────────────
def bfs(graph: EscapeGraph,
        start: str,
        goal: str,
        solved_puzzles: set[str],
        metrics: SearchMetrics,
        ever_expanded: Optional[set] = None) -> Generator[SearchEvent, None, None]:
    """
    Búsqueda por Amplitud (BFS) sobre el grafo global.

    Estrategia: Cola FIFO → explora nivel por nivel.
    Garantía: Encuentra el camino con MENOS PASOS (no necesariamente menor costo).

    ever_expanded: conjunto persistente entre reinicios para contar nodos
                   únicos y evitar inflar metrics.nodes_expanded.

    Yields SearchEvent para cada paso relevante, permitiendo que la GUI
    dibuje el proceso en tiempo real (visualización paso a paso).
    """
    # Cola: cada elemento es (nodo_actual, camino, costo_acumulado)
    queue = deque([(start, [start], 0.0)])
    explored = set()

    yield SearchEvent("log", start, [start],
                      f"▶ Iniciando BFS desde {{{start}}}")

    while queue:
        current, path, cost = queue.popleft()

        if current in explored:
            continue
        explored.add(current)

        # Solo contar como nodo nuevo si no fue expandido en una iteración anterior
        if ever_expanded is None or current not in ever_expanded:
            metrics.nodes_expanded += 1
            if ever_expanded is not None:
                ever_expanded.add(current)

        depth = len(path) - 1
        metrics.max_depth = max(metrics.max_depth, depth)
        metrics.total_cost = cost

        yield SearchEvent("expand", current, path,
                          f"> Expandiendo nodo {{{','.join(path)}}}")

        # ¿Llegamos a la meta?
        if current == goal:
            metrics.solution_path = path
            graph.set_state(current, NodeState.SOLVED)
            yield SearchEvent("goal", current, path,
                              f"✓ META ALCANZADA → {' → '.join(path)}",
                              metrics=metrics)
            return

        # Expandir vecinos
        for neighbor, edge_weight in graph.neighbors(current):
            if neighbor in explored:
                continue

            node_state = graph.get_state(neighbor)

            # ¿Nodo bloqueado? → pausar para que el solver lance A*
            if node_state == NodeState.LOCKED:
                puzzle_id = graph.nodes[neighbor].puzzle_id
                if puzzle_id not in solved_puzzles:
                    yield SearchEvent("locked", neighbor, path,
                                      f"⚠ Nodo bloqueado {{{neighbor}}} encontrado",
                                      puzzle_id=puzzle_id)
                    return  # Pausar → la GUI/solver reanuda con nueva llamada

            # Si ya fue desbloqueado, agregar a la cola
            if graph.get_state(neighbor) != NodeState.LOCKED:
                queue.append((neighbor, path + [neighbor], cost + edge_weight))

    yield SearchEvent("log", None, [],
                      "✗ No se encontró camino a la meta.")


# ─── DFS ─────────────────────────────────────────────────────────────────────
def dfs(graph: EscapeGraph,
        start: str,
        goal: str,
        solved_puzzles: set[str],
        metrics: SearchMetrics,
        ever_expanded: Optional[set] = None) -> Generator[SearchEvent, None, None]:
    """
    Búsqueda en Profundidad (DFS) sobre el grafo global.

    Estrategia: Pila LIFO → explora tan profundo como posible.
    NO garantiza camino óptimo, pero usa menos memoria en grafos amplios.

    ever_expanded: mismo rol que en BFS — evita contar re-expansiones.
    """
    stack = [(start, [start], 0.0)]
    explored = set()

    yield SearchEvent("log", start, [start],
                      f"▶ Iniciando DFS desde {{{start}}}")

    while stack:
        current, path, cost = stack.pop()

        if current in explored:
            continue
        explored.add(current)

        # Solo contar como nodo nuevo si no fue expandido antes
        if ever_expanded is None or current not in ever_expanded:
            metrics.nodes_expanded += 1
            if ever_expanded is not None:
                ever_expanded.add(current)

        depth = len(path) - 1
        metrics.max_depth = max(metrics.max_depth, depth)
        metrics.total_cost = cost

        yield SearchEvent("expand", current, path,
                          f"> Expandiendo nodo {{{','.join(path)}}}")

        if current == goal:
            metrics.solution_path = path
            graph.set_state(current, NodeState.SOLVED)
            yield SearchEvent("goal", current, path,
                              f"✓ META ALCANZADA → {' → '.join(path)}",
                              metrics=metrics)
            return

        for neighbor, edge_weight in reversed(graph.neighbors(current)):
            if neighbor in explored:
                continue

            node_state = graph.get_state(neighbor)
            if node_state == NodeState.LOCKED:
                puzzle_id = graph.nodes[neighbor].puzzle_id
                if puzzle_id not in solved_puzzles:
                    yield SearchEvent("locked", neighbor, path,
                                      f"⚠ Nodo bloqueado {{{neighbor}}} encontrado",
                                      puzzle_id=puzzle_id)
                    return

            if graph.get_state(neighbor) != NodeState.LOCKED:
                stack.append((neighbor, path + [neighbor], cost + edge_weight))

    yield SearchEvent("log", None, [],
                      "✗ No se encontró camino a la meta.")


if __name__ == "__main__":
    from graph import build_escape_room

    graph, puzzles, _ = build_escape_room()
    metrics = SearchMetrics()
    solved = set()

    # Desbloquear C manualmente para probar sin GUI
    graph.unlock("C"); graph.unlock("H"); graph.unlock("K")
    solved = {"P1", "P2", "P3"}

    print("=== PRUEBA BFS ===")
    for event in bfs(graph, "A", "M", solved, metrics):
        print(f"  [{event.type.upper()}] {event.message}")
    print(f"\n{metrics}")
