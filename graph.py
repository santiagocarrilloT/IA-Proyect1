"""
graph.py - Modelado del Escape Room como grafo dirigido acíclico
Cada nodo representa un estado del juego, cada arista una acción posible.
"""

from dataclasses import dataclass, field
from typing import Optional


# ─── ESTADO DE UN NODO ───────────────────────────────────────────────────────
class NodeState:
    START     = "start"      # Nodo inicial (verde)
    AVAILABLE = "available"  # Disponible para expansión (azul)
    LOCKED    = "locked"     # Bloqueado por un acertijo (gris)
    SOLVED    = "solved"     # Desbloqueado / visitado (verde claro)
    GOAL      = "goal"       # Meta del escape room (rojo)


@dataclass
class Node:
    id: str
    label: str
    state: str = NodeState.AVAILABLE
    puzzle_id: Optional[str] = None   # Si es locked, qué puzzle lo desbloquea


@dataclass
class Edge:
    source: str
    target: str
    weight: float = 1.0


# ─── GRAFO GLOBAL ─────────────────────────────────────────────────────────────
class EscapeGraph:
    """Grafo dirigido acíclico del escape room."""

    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []
        self._adj: dict[str, list[tuple[str, float]]] = {}

    def add_node(self, node: Node):
        self.nodes[node.id] = node
        if node.id not in self._adj:
            self._adj[node.id] = []

    def add_edge(self, source: str, target: str, weight: float = 1.0):
        self.edges.append(Edge(source, target, weight))
        self._adj.setdefault(source, []).append((target, weight))

    def neighbors(self, node_id: str) -> list[tuple[str, float]]:
        """Retorna lista de (vecino, peso) desde node_id."""
        return self._adj.get(node_id, [])

    def get_state(self, node_id: str) -> str:
        return self.nodes[node_id].state

    def set_state(self, node_id: str, state: str):
        self.nodes[node_id].state = state

    def is_locked(self, node_id: str) -> bool:
        return self.nodes[node_id].state == NodeState.LOCKED

    def unlock(self, node_id: str):
        self.nodes[node_id].state = NodeState.SOLVED


# ─── PUZZLE (Subproblema) ─────────────────────────────────────────────────────
@dataclass
class PuzzleNode:
    id: str
    label: str
    x: float = 0.5   # Posición normalizada para dibujar (0.0 - 1.0)
    y: float = 0.5


@dataclass
class PuzzleEdge:
    source: str
    target: str
    weight: float = 1.0


class Puzzle:
    """Subgrafo independiente asociado a un nodo bloqueado."""

    def __init__(self, puzzle_id: str, name: str, start: str, goal: str):
        self.puzzle_id = puzzle_id
        self.name = name
        self.start = start
        self.goal = goal
        self.nodes: dict[str, PuzzleNode] = {}
        self.edges: list[PuzzleEdge] = []
        self._adj: dict[str, list[tuple[str, float]]] = {}

    def add_node(self, node: PuzzleNode):
        self.nodes[node.id] = node
        self._adj.setdefault(node.id, [])

    def add_edge(self, source: str, target: str, weight: float = 1.0):
        self.edges.append(PuzzleEdge(source, target, weight))
        self._adj.setdefault(source, []).append((target, weight))

    def neighbors(self, node_id: str) -> list[tuple[str, float]]:
        return self._adj.get(node_id, [])

    def heuristic(self, node_id: str) -> float:
        """
        Heurística admisible: distancia euclidiana normalizada al nodo meta.
        h(n) <= costo_real → admisible → A* encuentra el óptimo.
        """
        n = self.nodes[node_id]
        g = self.nodes[self.goal]
        return round(((g.x - n.x)**2 + (g.y - n.y)**2) ** 0.5 * 20, 2)


# ─── CONSTRUCTOR DEL ESCENARIO ─────────────────────────────────────────────────
def build_escape_room() -> tuple[EscapeGraph, dict[str, Puzzle], dict[str, tuple[float, float]]]:
    """
    Construye el grafo principal y los 3 puzzles del escape room.
    Retorna (grafo, puzzles, posiciones_xy).
    """
    graph = EscapeGraph()

    # Posiciones (x, y) normalizadas para la GUI (0.0 - 1.0)
    positions = {
        "A": (0.10, 0.45),
        "B": (0.28, 0.18),
        "C": (0.48, 0.18),
        "E": (0.28, 0.72),
        "G": (0.48, 0.55),
        "H": (0.32, 0.88),
        "I": (0.67, 0.28),
        "J": (0.54, 0.85),
        "K": (0.70, 0.60),
        "L": (0.87, 0.22),
        "M": (0.90, 0.60),
    }

    # Nodos del grafo global
    nodos = [
        Node("A", "A", NodeState.START),
        Node("B", "B", NodeState.AVAILABLE),
        Node("C", "C", NodeState.LOCKED, puzzle_id="P1"),   # Bloqueado
        Node("E", "E", NodeState.AVAILABLE),
        Node("G", "G", NodeState.AVAILABLE),
        Node("H", "H", NodeState.LOCKED, puzzle_id="P2"),   # Bloqueado
        Node("I", "I", NodeState.AVAILABLE),
        Node("J", "J", NodeState.AVAILABLE),
        Node("K", "K", NodeState.LOCKED, puzzle_id="P3"),   # Bloqueado
        Node("L", "L", NodeState.AVAILABLE),
        Node("M", "M", NodeState.GOAL),
    ]
    for n in nodos:
        graph.add_node(n)

    # Aristas del grafo global
    aristas = [
        ("A", "B"), ("A", "E"),
        ("B", "C"), ("E", "G"), ("E", "H"),
        ("C", "I"), ("G", "I"), ("G", "K"),
        ("H", "J"),
        ("I", "L"), ("K", "M"), ("J", "K"),
        ("L", "M"),
    ]
    for src, dst in aristas:
        graph.add_edge(src, dst, weight=1.0)

    # ── PUZZLE 1: Candado del nodo C ────────────────────────────────────────
    p1 = Puzzle("P1", "Candado de C", start="S", goal="G")
    for nid, x, y in [("S",0.10,0.50),("N1",0.33,0.22),("N2",0.33,0.78),
                       ("N3",0.62,0.22),("N4",0.62,0.78),("G",0.88,0.50)]:
        p1.add_node(PuzzleNode(nid, nid, x, y))
    for src, dst, w in [("S","N1",7),("S","N2",3),("N1","N3",8),
                         ("N2","N3",5),("N2","N4",4),("N3","G",2),("N4","G",6)]:
        p1.add_edge(src, dst, w)

    # ── PUZZLE 2: Candado del nodo H ────────────────────────────────────────
    p2 = Puzzle("P2", "Candado de H", start="S", goal="G")
    for nid, x, y in [("S",0.10,0.50),("A",0.35,0.20),("B",0.35,0.80),
                       ("C",0.62,0.50),("G",0.88,0.50)]:
        p2.add_node(PuzzleNode(nid, nid, x, y))
    for src, dst, w in [("S","A",4),("S","B",6),("A","C",3),("B","C",5),("C","G",2)]:
        p2.add_edge(src, dst, w)

    # ── PUZZLE 3: Candado del nodo K ────────────────────────────────────────
    p3 = Puzzle("P3", "Candado de K", start="S", goal="G")
    for nid, x, y in [("S",0.10,0.50),("X",0.35,0.25),("Y",0.35,0.75),
                       ("Z",0.62,0.50),("G",0.88,0.50)]:
        p3.add_node(PuzzleNode(nid, nid, x, y))
    for src, dst, w in [("S","X",5),("S","Y",9),("X","Z",3),("Y","Z",2),("Z","G",4)]:
        p3.add_edge(src, dst, w)

    puzzles = {"P1": p1, "P2": p2, "P3": p3}
    return graph, puzzles, positions


if __name__ == "__main__":
    graph, puzzles, pos = build_escape_room()
    print("=== GRAFO GLOBAL ===")
    for nid, node in graph.nodes.items():
        vecinos = graph.neighbors(nid)
        print(f"  {nid} ({node.state}): -> {[v for v,_ in vecinos]}")
    print(f"\nNodos totales: {len(graph.nodes)}")
    print(f"Aristas totales: {len(graph.edges)}")
    print(f"\n=== PUZZLES ===")
    for pid, puz in puzzles.items():
        print(f"  {pid}: {puz.name} | Nodos={len(puz.nodes)} | {puz.start} -> {puz.goal}")
