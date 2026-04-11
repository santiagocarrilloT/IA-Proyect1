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

    def on_global(event: SearchEvent):
        prefix = {
            "expand": "  [BFS] ",
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
    args = sys.argv[1:]
    cli_mode = "--cli" in args
    algo = "bfs"
    if "--algo" in args:
        idx = args.index("--algo")
        if idx + 1 < len(args):
            algo = args[idx + 1].lower()

    if cli_mode:
        run_cli(algo)
    else:
        run_gui()
