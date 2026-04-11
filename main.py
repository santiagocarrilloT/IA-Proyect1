"""
main.py - Punto de entrada del Escape Room Solver
Ejecuta la GUI o el modo consola según argumentos.

Uso:
    python main.py          → Lanza la interfaz gráfica
    python main.py --cli    → Modo consola (sin GUI)
    python main.py --algo dfs --cli  → Consola con DFS
"""

import sys
import os
import argparse

# Asegurarse de que los módulos locales se importen correctamente
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "algorithms"))


def run_gui():
    """Lanza la interfaz gráfica Tkinter."""
    import tkinter as tk
    from gui import EscapeRoomGUI
    root = tk.Tk()
    app = EscapeRoomGUI(root)
    root.mainloop()


def run_cli(algorithm: str = "bfs"):
    """Ejecuta el solver en modo consola con output detallado."""
    from solver import EscapeRoomSolver
    from algorithms.uninformed_search import SearchEvent
    from algorithms.informed_search import PuzzleEvent

    print("\n" + "═"*55)
    print(f"  ESCAPE ROOM SOLVER — Modo Consola ({algorithm.upper()})")
    print("═"*55 + "\n")

    algo_label = "BFS" if algorithm == "bfs" else "DFS"

    def on_global(event: SearchEvent):
        prefix = {
            "expand": f"  [{algo_label}] ",
            "locked": "  [🔒] ",
            "goal":   "  [✓]  ",
            "log":    "  [---] ",
        }.get(event.type, "  ")
        print(prefix + event.message)

    def on_puzzle(event: PuzzleEvent):
        prefix = {
            "expand": "    [A*]    ",
            "solved": "    [✓ A*]  ",
            "log":    "    [---]   ",
        }.get(event.type, "    ")
        print(prefix + event.message)

    solver = EscapeRoomSolver(
        algorithm=algorithm,
        on_global_event=on_global,
        on_puzzle_event=on_puzzle,
    )
    result = solver.solve()
    print("\n" + result.report())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Escape Room Solver")
    parser.add_argument("--cli", action="store_true", help="Ejecutar en modo consola")
    parser.add_argument("--algo", choices=["bfs", "dfs"], default="bfs", help="Algoritmo de búsqueda global (bfs o dfs)")
    
    args = parser.parse_args()
    
    if args.cli:
        run_cli(args.algo)
    else:
        run_gui()
