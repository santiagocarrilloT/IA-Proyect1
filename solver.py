"""
solver.py - Coordinador: integra BFS/DFS global con A* local para puzzles.
Este es el "cerebro" del sistema que orquesta ambos niveles de búsqueda.
"""

import time
from dataclasses import dataclass, field
from typing import Callable, Optional
from graph import EscapeGraph, Puzzle, NodeState, build_escape_room
from algorithms.uninformed_search import (
    bfs, dfs, SearchEvent, SearchMetrics
)
from algorithms.informed_search import (
    astar, PuzzleEvent, PuzzleMetrics
)


# ─── RESULTADO COMPLETO ───────────────────────────────────────────────────────
@dataclass
class SolverResult:
    success: bool
    global_path: list[str] = field(default_factory=list)
    global_metrics: SearchMetrics = field(default_factory=SearchMetrics)
    puzzle_metrics: dict[str, PuzzleMetrics] = field(default_factory=dict)
    total_time: float = 0.0

    def report(self) -> str:
        lines = [
            "═" * 55,
            "  REPORTE FINAL — ESCAPE ROOM SOLVER",
            "═" * 55,
            f"  Estado:          {'✓ ÉXITO' if self.success else '✗ FALLIDO'}",
            f"  Camino global:   {' → '.join(self.global_path) if self.global_path else 'N/A'}",
            f"  Tiempo total:    {self.total_time:.4f}s",
            "",
            "  BÚSQUEDA GLOBAL",
            f"    Nodos expandidos: {self.global_metrics.nodes_expanded}",
            f"    Profundidad max:  {self.global_metrics.max_depth}",
            f"    Costo total:      {self.global_metrics.total_cost:.1f}",
            f"    Tiempo ejecución: {self.global_metrics.execution_time:.4f}s",
        ]
        if self.puzzle_metrics:
            lines += ["", "  PUZZLES (A*)"]
            for pid, pm in self.puzzle_metrics.items():
                lines += [
                    f"    [{pid}] Nodos: {pm.nodes_expanded} | "
                    f"Costo: {pm.total_cost:.1f} | "
                    f"Tiempo: {pm.execution_time:.4f}s | "
                    f"Camino: {' → '.join(pm.solution_path)}"
                ]
        lines.append("═" * 55)
        return "\n".join(lines)


# ─── SOLVER PRINCIPAL ─────────────────────────────────────────────────────────
class EscapeRoomSolver:
    """
    Coordina la búsqueda global (BFS/DFS) con los puzzles locales (A*).

    Flujo:
    1. BFS/DFS recorre el grafo global.
    2. Al encontrar nodo bloqueado → lanza A* para el puzzle.
    3. A* resuelve el subproblema → desbloquea el nodo.
    4. BFS/DFS continúa desde donde estaba.
    5. Repite hasta llegar a la META.
    """

    def __init__(self,
                 algorithm: str = "bfs",
                 on_global_event: Optional[Callable] = None,
                 on_puzzle_event: Optional[Callable] = None):
        self.algorithm = algorithm
        self.on_global_event = on_global_event   # Callback GUI búsqueda global
        self.on_puzzle_event = on_puzzle_event   # Callback GUI puzzle
        self.graph, self.puzzles, self.positions = build_escape_room()
        self.solved_puzzles: set[str] = set()
        self.global_metrics = SearchMetrics()
        self.puzzle_metrics: dict[str, PuzzleMetrics] = {}
        self.ever_expanded: set[str] = set()     # Nodos únicos expandidos globalmente
        self.result: Optional[SolverResult] = None

    def reset(self):
        self.graph, self.puzzles, self.positions = build_escape_room()
        self.solved_puzzles.clear()
        self.global_metrics = SearchMetrics()
        self.puzzle_metrics.clear()
        self.ever_expanded: set[str] = set()
        self.result = None

    def _run_puzzle(self, puzzle_id: str) -> PuzzleMetrics:
        """Ejecuta A* en el puzzle indicado y retorna sus métricas."""
        puzzle = self.puzzles[puzzle_id]
        pm = PuzzleMetrics()
        t0 = time.time()

        for event in astar(puzzle, pm):
            if self.on_puzzle_event:
                self.on_puzzle_event(event)

        pm.execution_time = time.time() - t0
        self.puzzle_metrics[puzzle_id] = pm
        return pm

    def solve(self) -> SolverResult:
        """
        Ejecuta la solución completa de forma SÍNCRONA.
        Útil para pruebas en consola sin GUI.
        """
        t0 = time.time()
        self._run_global_loop()
        total_time = time.time() - t0

        self.global_metrics.execution_time = total_time
        self.result = SolverResult(
            success=bool(self.global_metrics.solution_path),
            global_path=self.global_metrics.solution_path,
            global_metrics=self.global_metrics,
            puzzle_metrics=self.puzzle_metrics,
            total_time=total_time,
        )
        return self.result

    def _run_global_loop(self):
        """
        Bucle principal que coordina la búsqueda global con los puzzles.

        Tras desbloquear un nodo, siempre reinicia desde A para que BFS/DFS
        explore el grafo completo y encuentre el camino óptimo. El conjunto
        ever_expanded evita inflar metrics.nodes_expanded con re-expansiones.
        """
        goal = "M"
        max_iterations = 100
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            algo_fn = bfs if self.algorithm == "bfs" else dfs
            gen = algo_fn(self.graph, "A", goal,
                          self.solved_puzzles, self.global_metrics,
                          self.ever_expanded)

            goal_reached = False
            locked_node = None
            locked_puzzle = None

            for event in gen:
                if self.on_global_event:
                    self.on_global_event(event)

                if event.type == "goal":
                    goal_reached = True
                    break

                if event.type == "locked":
                    locked_node = event.node
                    locked_puzzle = event.puzzle_id
                    break

            if goal_reached:
                break

            if locked_puzzle and locked_puzzle not in self.solved_puzzles:
                # Resolver el puzzle con A*
                pm = self._run_puzzle(locked_puzzle)
                if pm.solution_path:
                    self.solved_puzzles.add(locked_puzzle)
                    self.graph.unlock(locked_node)
                    # Reiniciar desde A para explorar el grafo completo
                    # con el nodo recién desbloqueado disponible
                else:
                    break   # Puzzle sin solución → imposible continuar
            else:
                break

    # ─── GENERADOR PARA LA GUI (paso a paso) ─────────────────────────────────
    def step_generator(self):
        """
        Generador que la GUI puede consumir paso a paso.
        Yields tuplas ("global", SearchEvent) o ("puzzle", PuzzleEvent).
        """
        goal = "M"
        max_iter = 100

        for _ in range(max_iter):
            algo_fn = bfs if self.algorithm == "bfs" else dfs
            gen = algo_fn(self.graph, "A", goal,
                          self.solved_puzzles, self.global_metrics,
                          self.ever_expanded)

            goal_reached = False
            locked_node = None
            locked_puzzle = None

            for event in gen:
                yield ("global", event)

                if event.type == "goal":
                    goal_reached = True
                    break

                if event.type == "locked":
                    locked_node = event.node
                    locked_puzzle = event.puzzle_id

                    # Resolver el puzzle con A*
                    if locked_puzzle and locked_puzzle not in self.solved_puzzles:
                        puzzle = self.puzzles[locked_puzzle]
                        pm = PuzzleMetrics()
                        t0 = time.time()

                        for p_event in astar(puzzle, pm):
                            yield ("puzzle", p_event)

                        pm.execution_time = time.time() - t0
                        self.puzzle_metrics[locked_puzzle] = pm

                        if pm.solution_path:
                            self.solved_puzzles.add(locked_puzzle)
                            self.graph.unlock(locked_node)
                            # Reiniciar desde A con ever_expanded para métricas correctas
                    break

            if goal_reached:
                return


if __name__ == "__main__":
    print("Ejecutando solver en modo consola (BFS + A*)...\n")

    def log_global(event: SearchEvent):
        print(f"  [GLOBAL] {event.message}")

    def log_puzzle(event: PuzzleEvent):
        print(f"    [PUZZLE] {event.message}")

    solver = EscapeRoomSolver(
        algorithm="bfs",
        on_global_event=log_global,
        on_puzzle_event=log_puzzle,
    )
    result = solver.solve()
    print("\n" + result.report())
