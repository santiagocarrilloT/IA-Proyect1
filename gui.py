"""
gui.py - Interfaz Gráfica del Escape Room Solver
Panel izquierdo: Grafo Global (BFS/DFS)
Panel derecho: Puzzle Solver (A*)
Consolas y estadísticas en la parte inferior.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
import time
import math
import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "algorithms"))

from graph import build_escape_room, NodeState, EscapeGraph, Puzzle
from algorithms.uninformed_search import SearchEvent, SearchMetrics, bfs, dfs
from algorithms.informed_search import PuzzleEvent, PuzzleMetrics, astar


# ─── PALETA DE COLORES ────────────────────────────────────────────────────────
COLORS = {
    "bg":          "#0a0e1a",
    "bg2":         "#111827",
    "bg3":         "#1a2235",
    "bg4":         "#1e2a3e",
    "border":      "#2a3550",
    "green":       "#00ff88",
    "green_dim":   "#00cc66",
    "blue":        "#4488ff",
    "blue_dim":    "#2255cc",
    "red":         "#ff4466",
    "yellow":      "#ffcc00",
    "gray":        "#556677",
    "gray_dim":    "#334455",
    "purple":      "#aa66ff",
    "cyan":        "#00ccff",
    "white":       "#e8eeff",
    "text_dim":    "#8899bb",
    "node_start":  "#00ff88",
    "node_avail":  "#4488ff",
    "node_locked": "#556677",
    "node_solved": "#00cc66",
    "node_goal":   "#ff4466",
    "node_expand": "#ffcc00",
}

STATE_COLOR = {
    NodeState.START:     COLORS["node_start"],
    NodeState.AVAILABLE: COLORS["node_avail"],
    NodeState.LOCKED:    COLORS["node_locked"],
    NodeState.SOLVED:    COLORS["node_solved"],
    NodeState.GOAL:      COLORS["node_goal"],
}


class EscapeRoomGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Escape Room Solver — BFS + A*")
        self.root.configure(bg=COLORS["bg"])
        self.root.geometry("1200x750")
        self.root.minsize(900, 600)

        # Estado
        self.graph = None
        self.puzzles = None
        self.positions = None
        self.solved_puzzles: set[str] = set()
        self.global_metrics = SearchMetrics()
        self.puzzle_metrics: dict[str, PuzzleMetrics] = {}

        # Animación
        self.anim_nodes: set[str] = set()    # Nodos en expansión actual
        self.path_edges: set[str] = set()    # Aristas del camino actual
        self.puzzle_anim: set[str] = set()   # Nodos puzzle animados
        self.puzzle_path_edges: set[str] = set()
        self.current_puzzle: Optional[Puzzle] = None
        self.ever_expanded: set[str] = set() # Nodos únicos expandidos globalmente
        self._exec_start: float = 0.0        # Timestamp de inicio de ejecución
        self.running = False
        self.step_gen = None

        self._build_ui()
        self._reset()

    # ─── CONSTRUCCIÓN DE LA UI ────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg=COLORS["bg2"],
                       highlightbackground=COLORS["border"],
                       highlightthickness=1)
        hdr.pack(fill="x", side="top")
        tk.Label(hdr, text="🔐  ESCAPE ROOM SOLVER", bg=COLORS["bg2"],
                 fg=COLORS["green"], font=("Courier", 13, "bold")).pack(side="left", padx=12, pady=8)
        self.status_lbl = tk.Label(hdr, text="● Listo", bg=COLORS["bg2"],
                                   fg=COLORS["text_dim"], font=("Courier", 10))
        self.status_lbl.pack(side="left", padx=8)

        # Paneles principales
        panels = tk.Frame(self.root, bg=COLORS["bg"])
        panels.pack(fill="both", expand=True)

        # Canvas izquierdo — Grafo Global
        lf = tk.Frame(panels, bg=COLORS["bg2"],
                      highlightbackground=COLORS["border"], highlightthickness=1)
        lf.pack(side="left", fill="both", expand=True, padx=(4,2), pady=4)
        tk.Label(lf, text="GLOBAL GRAPH — Búsqueda No Informada",
                 bg=COLORS["bg2"], fg=COLORS["text_dim"],
                 font=("Courier", 9)).pack(anchor="w", padx=8, pady=(4,0))
        self.canvas_global = tk.Canvas(lf, bg=COLORS["bg"], highlightthickness=0)
        self.canvas_global.pack(fill="both", expand=True, padx=4, pady=4)
        self.canvas_global.bind("<Configure>", lambda e: self._draw_all())

        # Canvas derecho — Puzzle
        rf = tk.Frame(panels, bg=COLORS["bg2"],
                      highlightbackground=COLORS["border"], highlightthickness=1)
        rf.pack(side="right", fill="both", expand=True, padx=(2,4), pady=4)
        tk.Label(rf, text="PUZZLE SOLVER — Búsqueda Informada (A*)",
                 bg=COLORS["bg2"], fg=COLORS["text_dim"],
                 font=("Courier", 9)).pack(anchor="w", padx=8, pady=(4,0))
        self.canvas_puzzle = tk.Canvas(rf, bg=COLORS["bg"], highlightthickness=0)
        self.canvas_puzzle.pack(fill="both", expand=True, padx=4, pady=4)

        # Footer
        footer = tk.Frame(self.root, bg=COLORS["bg2"],
                          highlightbackground=COLORS["border"], highlightthickness=1)
        footer.pack(fill="x", side="bottom")

        # Controles
        ctrl = tk.Frame(footer, bg=COLORS["bg3"])
        ctrl.pack(fill="x", padx=6, pady=4)

        btn_style = {"bg": COLORS["bg4"],
                     "font": ("Courier", 10), "relief": "flat",
                     "padx": 12, "pady": 4, "cursor": "hand2",
                     "activebackground": COLORS["border"],
                     "activeforeground": COLORS["white"]}

        self.btn_run = tk.Button(ctrl, text="▶  Ejecutar", **btn_style,
                                 fg=COLORS["green"], command=self._toggle_run)
        self.btn_run.pack(side="left", padx=(0,4))

        tk.Button(ctrl, text="⏭  Paso", **btn_style,
                  fg=COLORS["white"], command=self._step).pack(side="left", padx=4)

        tk.Button(ctrl, text="↺  Reiniciar", **btn_style,
                  fg=COLORS["red"], command=self._reset).pack(side="left", padx=4)

        tk.Label(ctrl, text="Velocidad:", bg=COLORS["bg3"],
                 fg=COLORS["text_dim"], font=("Courier", 9)).pack(side="left", padx=(12,4))
        self.speed_var = tk.StringVar(value="Normal")
        speed_map = {"Lenta": 900, "Normal": 450, "Rápida": 180, "Turbo": 60}
        self.speed_map = speed_map
        spd = ttk.Combobox(ctrl, textvariable=self.speed_var,
                           values=list(speed_map.keys()), width=8, state="readonly")
        spd.pack(side="left")

        tk.Label(ctrl, text="Algoritmo:", bg=COLORS["bg3"],
                 fg=COLORS["text_dim"], font=("Courier", 9)).pack(side="left", padx=(12,4))
        self.algo_var = tk.StringVar(value="BFS")
        algo = ttk.Combobox(ctrl, textvariable=self.algo_var,
                            values=["BFS", "DFS"], width=6, state="readonly")
        algo.pack(side="left")
        algo.bind("<<ComboboxSelected>>", lambda e: self._reset())

        # Leyenda
        leg = tk.Frame(ctrl, bg=COLORS["bg3"])
        leg.pack(side="right", padx=8)
        for label, color in [("Inicio/Resuelto", COLORS["node_start"]),
                              ("Disponible",      COLORS["node_avail"]),
                              ("Bloqueado",       COLORS["node_locked"]),
                              ("Meta",            COLORS["node_goal"])]:
            f = tk.Frame(leg, bg=COLORS["bg3"])
            f.pack(side="left", padx=4)
            tk.Canvas(f, width=10, height=10, bg=color,
                      highlightthickness=0).pack(side="left")
            tk.Label(f, text=label, bg=COLORS["bg3"],
                     fg=COLORS["text_dim"], font=("Courier", 8)).pack(side="left", padx=2)

        # Consolas + estadísticas
        bottom = tk.Frame(footer, bg=COLORS["bg2"])
        bottom.pack(fill="x")

        # Consola global
        gl = tk.Frame(bottom, bg=COLORS["bg2"])
        gl.pack(side="left", fill="both", expand=True)
        tk.Label(gl, text="▸ CONSOLA GLOBAL", bg=COLORS["bg2"],
                 fg=COLORS["green"], font=("Courier", 8)).pack(anchor="w", padx=6, pady=(2,0))
        self.log_global = tk.Text(gl, height=5, bg=COLORS["bg"],
                                  fg=COLORS["cyan"], font=("Courier", 9),
                                  state="disabled", relief="flat", wrap="word")
        self.log_global.pack(fill="both", expand=True, padx=4, pady=(0,4))

        # Consola puzzle
        pl = tk.Frame(bottom, bg=COLORS["bg2"])
        pl.pack(side="left", fill="both", expand=True)
        tk.Label(pl, text="▸ CONSOLA PUZZLE", bg=COLORS["bg2"],
                 fg=COLORS["purple"], font=("Courier", 8)).pack(anchor="w", padx=6, pady=(2,0))
        self.log_puzzle = tk.Text(pl, height=5, bg=COLORS["bg"],
                                  fg=COLORS["purple"], font=("Courier", 9),
                                  state="disabled", relief="flat", wrap="word")
        self.log_puzzle.pack(fill="both", expand=True, padx=4, pady=(0,4))

        # Estadísticas
        stats = tk.Frame(bottom, bg=COLORS["bg3"], width=220)
        stats.pack(side="right", fill="y", padx=4)
        stats.pack_propagate(False)

        tk.Label(stats, text="ESTADÍSTICAS", bg=COLORS["bg3"],
                 fg=COLORS["text_dim"], font=("Courier", 8)).pack(padx=8, pady=(6,2))

        gf = tk.Frame(stats, bg=COLORS["bg3"])
        gf.pack(fill="x", padx=6)
        tk.Label(gf, text="Global Search", bg=COLORS["bg3"],
                 fg=COLORS["green"], font=("Courier", 8, "bold")).pack(anchor="w")

        self.stat_vars = {}
        for key, lbl in [("g_nodes","Nodos expandidos:"),("g_depth","Profundidad:"),
                          ("g_cost","Costo total:"),("g_time","Tiempo:"),("g_algo","Algoritmo:")]:
            row = tk.Frame(gf, bg=COLORS["bg3"])
            row.pack(fill="x")
            tk.Label(row, text=lbl, bg=COLORS["bg3"],
                     fg=COLORS["text_dim"], font=("Courier", 8)).pack(side="left")
            var = tk.StringVar(value="0")
            tk.Label(row, textvariable=var, bg=COLORS["bg3"],
                     fg=COLORS["white"], font=("Courier", 8, "bold")).pack(side="right")
            self.stat_vars[key] = var

        pf = tk.Frame(stats, bg=COLORS["bg3"])
        pf.pack(fill="x", padx=6, pady=(4,0))
        tk.Label(pf, text="Local Puzzle (A*)", bg=COLORS["bg3"],
                 fg=COLORS["purple"], font=("Courier", 8, "bold")).pack(anchor="w")

        for key, lbl in [("p_nodes","Nodos expandidos:"),("p_cost","Costo total:"),("p_time","Tiempo:")]:
            row = tk.Frame(pf, bg=COLORS["bg3"])
            row.pack(fill="x")
            tk.Label(row, text=lbl, bg=COLORS["bg3"],
                     fg=COLORS["text_dim"], font=("Courier", 8)).pack(side="left")
            var = tk.StringVar(value="-")
            tk.Label(row, textvariable=var, bg=COLORS["bg3"],
                     fg=COLORS["white"], font=("Courier", 8, "bold")).pack(side="right")
            self.stat_vars[key] = var

    # ─── RESET ────────────────────────────────────────────────────────────────
    def _reset(self):
        self.running = False
        self.step_gen = None
        self.graph, self.puzzles, self.positions = build_escape_room()
        self.solved_puzzles.clear()
        self.global_metrics = SearchMetrics()
        self.puzzle_metrics.clear()
        self.anim_nodes.clear()
        self.path_edges.clear()
        self.puzzle_anim.clear()
        self.puzzle_path_edges.clear()
        self.current_puzzle = None
        self.ever_expanded.clear()
        self._exec_start = 0.0
        self._clear_log(self.log_global)
        self._clear_log(self.log_puzzle)
        for k in self.stat_vars:
            self.stat_vars[k].set("0" if k not in ("p_time", "g_time") else "-")
        self.stat_vars["g_algo"].set(self.algo_var.get())
        self.btn_run.config(text="▶  Ejecutar")
        self.status_lbl.config(text="● Listo", fg=COLORS["text_dim"])
        self._draw_all()

    # ─── DIBUJO GRAFO GLOBAL ─────────────────────────────────────────────────
    def _draw_global(self):
        cv = self.canvas_global
        cv.delete("all")
        W = cv.winfo_width()
        H = cv.winfo_height()
        if W < 10 or H < 10:
            return

        # Grid de fondo
        for x in range(0, W, 40):
            cv.create_line(x, 0, x, H, fill="#1a2235", width=1)
        for y in range(0, H, 40):
            cv.create_line(0, y, W, y, fill="#1a2235", width=1)

        # Calcular posiciones en píxeles
        pad = 40
        npos = {}
        for nid, (nx, ny) in self.positions.items():
            npos[nid] = (int(pad + nx * (W - 2*pad)),
                         int(pad + ny * (H - 2*pad)))

        # Aristas
        for edge in self.graph.edges:
            pa, pb = npos[edge.source], npos[edge.target]
            key = f"{edge.source}-{edge.target}"
            is_path = key in self.path_edges
            color = COLORS["blue"] if is_path else COLORS["border"]
            width = 2 if is_path else 1
            dash = () if is_path else (4, 4)
            self._draw_arrow(cv, pa, pb, color, width, dash, r=22)

        # Nodos
        R = 22
        for nid, (nx, ny) in npos.items():
            state = self.graph.get_state(nid)
            is_anim = nid in self.anim_nodes
            color = COLORS["node_expand"] if is_anim else STATE_COLOR.get(state, COLORS["gray"])

            # Glow effect
            if is_anim or state in (NodeState.START, NodeState.GOAL, NodeState.SOLVED):
                for r_off in (6, 4, 2):
                    cv.create_oval(nx-R-r_off, ny-R-r_off, nx+R+r_off, ny+R+r_off,
                                   outline=color, fill="", width=1,
                                   stipple="gray25" if r_off == 6 else "gray50" if r_off == 4 else "")

            cv.create_oval(nx-R, ny-R, nx+R, ny+R,
                           fill=self._hex_alpha(color, 0.2), outline=color, width=2)

            if state == NodeState.LOCKED:
                cv.create_text(nx, ny-4, text="🔒", font=("", 10), fill=COLORS["gray"])
                cv.create_text(nx, ny+10, text=nid, font=("Courier", 10, "bold"),
                               fill=COLORS["text_dim"])
            else:
                cv.create_text(nx, ny, text=nid, font=("Courier", 12, "bold"), fill=color)

            if state == NodeState.SOLVED:
                cv.create_text(nx, ny-R-8, text="✓", font=("Courier", 9), fill=COLORS["green"])
            if state == NodeState.GOAL:
                cv.create_text(nx, ny+R+10, text="META", font=("Courier", 8), fill=COLORS["red"])

    # ─── DIBUJO PUZZLE ────────────────────────────────────────────────────────
    def _draw_puzzle(self):
        cv = self.canvas_puzzle
        cv.delete("all")
        W = cv.winfo_width()
        H = cv.winfo_height()
        if W < 10 or H < 10:
            return

        for x in range(0, W, 40):
            cv.create_line(x, 0, x, H, fill="#1a2235", width=1)
        for y in range(0, H, 40):
            cv.create_line(0, y, W, y, fill="#1a2235", width=1)

        if not self.current_puzzle:
            cv.create_text(W//2, H//2, text="Esperando puzzle...",
                           font=("Courier", 12), fill=COLORS["gray"])
            return

        pad = 40
        npos = {}
        for nid, pn in self.current_puzzle.nodes.items():
            npos[nid] = (int(pad + pn.x * (W - 2*pad)),
                         int(pad + pn.y * (H - 2*pad)))

        # Aristas con pesos
        for pe in self.current_puzzle.edges:
            if pe.source not in npos or pe.target not in npos:
                continue
            pa, pb = npos[pe.source], npos[pe.target]
            key = f"{pe.source}-{pe.target}"
            is_path = key in self.puzzle_path_edges
            color = COLORS["purple"] if is_path else COLORS["border"]
            self._draw_arrow(cv, pa, pb, color, 2 if is_path else 1,
                             () if is_path else (3, 3), r=22)
            # Peso
            mx, my = (pa[0]+pb[0])//2, (pa[1]+pb[1])//2
            cv.create_text(mx, my-12, text=str(int(pe.weight)),
                           font=("Courier", 9, "bold"),
                           fill=COLORS["purple"] if is_path else COLORS["text_dim"])

        # Nodos
        R = 22
        for nid, (nx, ny) in npos.items():
            is_anim = nid in self.puzzle_anim
            is_start = nid == self.current_puzzle.start
            is_goal = nid == self.current_puzzle.goal
            is_in_path = any(e.startswith(nid+"-") or e.endswith("-"+nid)
                             for e in self.puzzle_path_edges)

            if is_goal and self.puzzle_path_edges:
                color = COLORS["node_solved"]
            elif is_goal:
                color = COLORS["node_goal"]
            elif is_start:
                color = COLORS["node_start"]
            elif is_anim:
                color = COLORS["purple"]
            else:
                color = COLORS["node_avail"] if is_in_path else COLORS["gray"]

            if is_anim or is_start or is_goal:
                for r_off in (5, 3):
                    cv.create_oval(nx-R-r_off, ny-R-r_off, nx+R+r_off, ny+R+r_off,
                                   outline=color, fill="", width=1)

            cv.create_oval(nx-R, ny-R, nx+R, ny+R,
                           fill=self._hex_alpha(color, 0.25), outline=color, width=2)
            cv.create_text(nx, ny, text=nid, font=("Courier", 11, "bold"), fill=color)

            if is_anim:
                h = self.current_puzzle.heuristic(nid)
                cv.create_text(nx, ny-R-10, text=f"h={h}",
                               font=("Courier", 8), fill=COLORS["purple"])

        cv.create_text(10, 10, anchor="nw",
                       text=self.current_puzzle.name,
                       font=("Courier", 9, "bold"),
                       fill=COLORS["purple"])

    def _draw_all(self):
        self._draw_global()
        self._draw_puzzle()
        self._update_stats()

    def _draw_arrow(self, cv, pa, pb, color, width=1, dash=(), r=20):
        dx = pb[0]-pa[0]; dy = pb[1]-pa[1]
        length = math.hypot(dx, dy)
        if length < 1:
            return
        sx = pa[0] + dx/length*r; sy = pa[1] + dy/length*r
        ex = pb[0] - dx/length*r; ey = pb[1] - dy/length*r
        cv.create_line(sx, sy, ex, ey, fill=color, width=width, dash=dash)
        ang = math.atan2(ey-sy, ex-sx)
        size = 9
        cv.create_polygon(
            ex, ey,
            ex - size*math.cos(ang-0.4), ey - size*math.sin(ang-0.4),
            ex - size*math.cos(ang+0.4), ey - size*math.sin(ang+0.4),
            fill=color, outline=color
        )

    @staticmethod
    def _hex_alpha(hex_color: str, alpha: float) -> str:
        """Simula transparencia mezclando con el fondo #0a0e1a."""
        bg = (10, 14, 26)
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        r2 = int(r*alpha + bg[0]*(1-alpha))
        g2 = int(g*alpha + bg[1]*(1-alpha))
        b2 = int(b*alpha + bg[2]*(1-alpha))
        return f"#{r2:02x}{g2:02x}{b2:02x}"

    # ─── LOGGING ─────────────────────────────────────────────────────────────
    def _log(self, widget: tk.Text, msg: str):
        widget.config(state="normal")
        widget.insert("end", msg + "\n")
        widget.see("end")
        widget.config(state="disabled")

    def _clear_log(self, widget: tk.Text):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.config(state="disabled")

    def _update_stats(self):
        self.stat_vars["g_nodes"].set(str(self.global_metrics.nodes_expanded))
        self.stat_vars["g_depth"].set(str(self.global_metrics.max_depth))
        self.stat_vars["g_cost"].set(f"{self.global_metrics.total_cost:.1f}")
        self.stat_vars["g_algo"].set(self.algo_var.get())
        if self._exec_start > 0:
            elapsed = time.time() - self._exec_start
            self.stat_vars["g_time"].set(f"{elapsed:.3f}s")

        if self.puzzle_metrics:
            last = list(self.puzzle_metrics.values())[-1]
            self.stat_vars["p_nodes"].set(str(last.nodes_expanded))
            self.stat_vars["p_cost"].set(f"{last.total_cost:.1f}")
            self.stat_vars["p_time"].set(f"{last.execution_time:.3f}s")

    # ─── CONTROL DE EJECUCIÓN ─────────────────────────────────────────────────
    def _toggle_run(self):
        if self.running:
            self.running = False
            self.btn_run.config(text="▶  Ejecutar")
            self.status_lbl.config(text="⏸ Pausado", fg=COLORS["yellow"])
        else:
            self.running = True
            self.btn_run.config(text="⏸  Pausar")
            self.status_lbl.config(text="● Ejecutando...", fg=COLORS["green"])
            if not self.step_gen:
                self.step_gen = self._make_generator()
                self._exec_start = time.time()
            self._auto_run()

    def _auto_run(self):
        if not self.running:
            return
        finished = self._advance_one_step()
        if not finished:
            delay = self.speed_map.get(self.speed_var.get(), 450)
            self.root.after(delay, self._auto_run)

    def _step(self):
        if not self.step_gen:
            self.step_gen = self._make_generator()
            self._exec_start = time.time()
        self._advance_one_step()

    def _advance_one_step(self) -> bool:
        """Avanza un paso. Retorna True si terminó."""
        try:
            kind, event = next(self.step_gen)
        except StopIteration:
            self.running = False
            self.btn_run.config(text="▶  Ejecutar")
            self.status_lbl.config(text="✓ Completado", fg=COLORS["green"])
            self.step_gen = None
            self._draw_all()
            return True

        if kind == "global":
            self._handle_global_event(event)
        else:
            self._handle_puzzle_event(event)
        self._draw_all()
        return False

    def _handle_global_event(self, event: SearchEvent):
        self._log(self.log_global, event.message)
        if event.type == "expand":
            self.anim_nodes.clear()
            self.anim_nodes.add(event.node)
            for i in range(len(event.path)-1):
                self.path_edges.add(f"{event.path[i]}-{event.path[i+1]}")
        elif event.type == "locked":
            self._log(self.log_global,
                      f"- Initiating informed search for Puzzle at Node {{{event.node}}}")
            self.status_lbl.config(text=f"🔒 Resolviendo puzzle...", fg=COLORS["yellow"])
        elif event.type == "goal":
            self.anim_nodes.clear()
            for i in range(len(event.path)-1):
                self.path_edges.add(f"{event.path[i]}-{event.path[i+1]}")
            elapsed = time.time() - self._exec_start if self._exec_start > 0 else 0.0
            self.global_metrics.execution_time = elapsed
            self.stat_vars["g_time"].set(f"{elapsed:.3f}s")
            self.status_lbl.config(text="✓ ¡Meta alcanzada!", fg=COLORS["green"])
            messagebox.showinfo("¡Escape Room Resuelto!",
                                f"Camino: {' → '.join(event.path)}\n\n"
                                f"Nodos expandidos: {self.global_metrics.nodes_expanded}\n"
                                f"Profundidad: {self.global_metrics.max_depth}\n"
                                f"Costo: {self.global_metrics.total_cost:.1f}\n"
                                f"Tiempo total: {elapsed:.3f}s")

    def _handle_puzzle_event(self, event: PuzzleEvent):
        self._log(self.log_puzzle, event.message)
        if event.type == "expand":
            self.puzzle_anim.add(event.node_id)
        elif event.type == "solved":
            self.puzzle_path_edges.clear()
            for i in range(len(event.path)-1):
                self.puzzle_path_edges.add(f"{event.path[i]}-{event.path[i+1]}")
            # Las métricas se asignan con la clave correcta en _make_generator

    # ─── GENERADOR INTEGRADO ──────────────────────────────────────────────────
    def _make_generator(self):
        """
        Generador que coordina búsqueda global + puzzles.
        Siempre reinicia desde A para explorar el grafo completo;
        ever_expanded garantiza que los nodos ya contados no inflen métricas.
        """
        goal = "M"

        for _ in range(50):  # máx iteraciones
            algo_fn = bfs if self.algo_var.get() == "BFS" else dfs
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

                    # Resolver puzzle con A*
                    if locked_puzzle and locked_puzzle not in self.solved_puzzles:
                        puzzle = self.puzzles[locked_puzzle]
                        self.current_puzzle = puzzle
                        self.puzzle_anim.clear()
                        self.puzzle_path_edges.clear()
                        pm = PuzzleMetrics()
                        t0 = time.time()
                        for p_event in astar(puzzle, pm):
                            yield ("puzzle", p_event)
                        pm.execution_time = time.time() - t0

                        if pm.solution_path:
                            self.solved_puzzles.add(locked_puzzle)
                            self.graph.unlock(locked_node)
                            self.puzzle_metrics[locked_puzzle] = pm
                            self._log(self.log_puzzle,
                                      f"- Puzzle Solved! Unlocking Node {{{locked_node}}}")
                            self._log(self.log_global,
                                      f"✓ Nodo {{{locked_node}}} desbloqueado. Reanudando búsqueda...")
                    break

            if goal_reached:
                return
            if not locked_puzzle:
                return


if __name__ == "__main__":
    root = tk.Tk()
    app = EscapeRoomGUI(root)
    root.mainloop()
