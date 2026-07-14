from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import List, Optional, Sequence, Tuple

from .animator import Animator
from .maze import generate_random_solvable_maze
from .solver import solve_with_steps

Cell = Tuple[int, int]


class RatInMazeUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Rat in a Maze - BFS/DFS Visualization")
        self.resizable(True, True)

        self.rows = tk.IntVar(value=10)
        self.cols = tk.IntVar(value=10)
        self.cell_size = 28

        self.speed_ms = tk.IntVar(value=50)
        self.algorithm = tk.StringVar(value="BFS")

        self.maze: List[List[int]] = []
        self.start: Cell = (0, 0)
        self.end: Cell = (9, 9)

        self._anim = Animator()
        self._after_id: Optional[str] = None
        self._anim_index_var_guard = False

        self._apply_theme()
        self._build_layout()

        self.reset_view(initial=True)

    # ---------------- Theme / Layout ----------------
    def _apply_theme(self):
        style = ttk.Style(self)
        # Works across most Tk installations.
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background="#f6f7fb")
        style.configure("TLabelframe", background="#f6f7fb")
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", background="#f6f7fb", font=("Segoe UI", 10))
        style.configure("TButton", padding=(8, 4))
        style.configure("TSpinbox", padding=(2, 0))

    def _build_layout(self):
        outer = ttk.Frame(self, padding=14)
        outer.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(0, weight=1)

        # Left controls
        ctrl = ttk.LabelFrame(outer, text="Controls", padding=12)
        ctrl.grid(row=0, column=0, sticky="nw")

        ttk.Label(ctrl, text="Rows").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(
            ctrl,
            from_=3,
            to=60,
            width=6,
            textvariable=self.rows,
            command=self.reset_view,
        ).grid(row=0, column=1, sticky="w", padx=(8, 10))

        ttk.Label(ctrl, text="Cols").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Spinbox(
            ctrl,
            from_=3,
            to=60,
            width=6,
            textvariable=self.cols,
            command=self.reset_view,
        ).grid(row=1, column=1, sticky="w", padx=(8, 10), pady=(8, 0))

        ttk.Label(ctrl, text="Algorithm").grid(row=2, column=0, sticky="w", pady=(12, 0))
        algo = ttk.Combobox(
            ctrl,
            values=["BFS", "DFS"],
            state="readonly",
            width=10,
            textvariable=self.algorithm,
        )
        algo.grid(row=2, column=1, sticky="w", padx=(8, 10), pady=(12, 0))

        ttk.Label(ctrl, text="Speed (ms)").grid(row=3, column=0, sticky="w", pady=(12, 0))
        ttk.Scale(ctrl, from_=10, to=250, orient="horizontal", length=140, variable=self.speed_ms).grid(
            row=3, column=1, sticky="w", padx=(8, 10), pady=(12, 0)
        )

        btns = ttk.Frame(ctrl)
        btns.grid(row=4, column=0, columnspan=2, sticky="w", pady=(14, 0))

        self.btn_generate = ttk.Button(btns, text="Generate Maze", command=self.generate_maze)
        self.btn_generate.grid(row=0, column=0, padx=(0, 8), pady=(0, 8), sticky="ew")

        self.btn_start = ttk.Button(btns, text="Start", command=self.start_visualization)
        self.btn_start.grid(row=0, column=1, padx=(0, 0), pady=(0, 8), sticky="ew")

        self.btn_step = ttk.Button(btns, text="Step", command=self.step_once, state="disabled")
        self.btn_step.grid(row=1, column=0, padx=(0, 8), pady=(0, 0), sticky="ew")

        self.btn_reset = ttk.Button(btns, text="Reset", command=self.reset_view)
        self.btn_reset.grid(row=1, column=1, padx=(0, 0), pady=(0, 0), sticky="ew")

        # Status
        self.status_var = tk.StringVar(value="Click 'Generate Maze' to begin.")
        ttk.Label(outer, textvariable=self.status_var).grid(row=1, column=0, sticky="w", pady=(10, 0), columnspan=1)

        # Legend
        legend = ttk.LabelFrame(outer, text="Legend", padding=10)
        legend.grid(row=2, column=0, sticky="nw", pady=(10, 0))
        self._build_legend(legend)

        # Canvas area
        canvas_frame = ttk.LabelFrame(outer, text="Maze", padding=10)
        canvas_frame.grid(row=0, column=1, rowspan=3, sticky="nsew", padx=(16, 0))
        outer.rowconfigure(0, weight=1)
        outer.rowconfigure(1, weight=0)
        outer.rowconfigure(2, weight=0)
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_frame, bg="#ffffff", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        # Re-render on resize: keep it light by only adjusting canvas size.
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _build_legend(self, parent: ttk.Frame):
        items = [
            ("Start", "#1e90ff"),
            ("End", "#ff4d4d"),
            ("Wall", "#1f1f1f"),
            ("Open", "#2e8b57"),
            ("Visited", "#ffd166"),
            ("Backtrack", "#f4a261"),
            ("Path", "#8a5cf6"),
        ]
        for i, (label, color) in enumerate(items):
            r = i // 2
            c = (i % 2)
            frame = ttk.Frame(parent)
            frame.grid(row=r, column=c, padx=(6, 14), pady=(6, 0), sticky="w")
            sw = tk.Canvas(frame, width=16, height=16, highlightthickness=0, bg=color)
            sw.pack(side="left")
            ttk.Label(frame, text=label).pack(side="left", padx=(8, 0))

    def _on_canvas_configure(self, _event=None):
        # Keep canvas size synced with grid drawing (actual grid size based on cell_size).
        # Layout weights handle the rest.
        if self.maze:
            size_w = len(self.maze[0]) * self.cell_size
            size_h = len(self.maze) * self.cell_size
            self.canvas.configure(scrollregion=(0, 0, size_w, size_h), width=size_w, height=size_h)

    # ---------------- Core actions ----------------
    def reset_view(self, initial: bool = False):
        self._cancel_animation()
        self._anim.reset([])

        self.btn_step.configure(state="disabled")
        self.btn_start.configure(state="normal")

        self.start = (0, 0)
        self.end = (int(self.rows.get()) - 1, int(self.cols.get()) - 1)

        size_w = int(self.cols.get()) * self.cell_size
        size_h = int(self.rows.get()) * self.cell_size
        self.canvas.configure(width=size_w, height=size_h)

        self.canvas.delete("all")

        if initial or not self.maze:
            self.maze = [[1 for _ in range(int(self.cols.get()))] for __ in range(int(self.rows.get()))]
            # show start/end
            self.maze[self.start[0]][self.start[1]] = 1
            self.maze[self.end[0]][self.end[1]] = 1

        self._draw_base_grid()
        self.status_var.set("Click 'Generate Maze' to begin." if initial else "Reset. Generate or start again.")

    def generate_maze(self):
        if self._anim.is_running():
            return

        r = int(self.rows.get())
        c = int(self.cols.get())
        if r < 3 or c < 3:
            messagebox.showerror("Invalid size", "Rows and Cols must be at least 3.")
            return

        self.status_var.set("Generating solvable maze...")
        result = generate_random_solvable_maze(
            r,
            c,
            self.algorithm.get(),
            solver_fn=lambda m, s, e, algo: solve_with_steps(m, s, e, algo),
        )
        self.maze = result.maze
        self.start = result.start
        self.end = result.end

        self._draw_base_grid()
        self.status_var.set("Maze generated. Click 'Start' to visualize." if result.solvable else "Maze generated (may be unsolvable).")

        self.btn_step.configure(state="disabled")
        self.btn_start.configure(state="normal")

    # ---------------- Drawing ----------------
    def _draw_base_grid(self):
        self.canvas.delete("all")

        rows = len(self.maze)
        cols = len(self.maze[0]) if rows else 0

        for i in range(rows):
            for j in range(cols):
                x0 = j * self.cell_size
                y0 = i * self.cell_size
                x1 = x0 + self.cell_size
                y1 = y0 + self.cell_size

                if (i, j) == self.start:
                    fill = "#1e90ff"
                elif (i, j) == self.end:
                    fill = "#ff4d4d"
                else:
                    fill = "#2e8b57" if self.maze[i][j] == 1 else "#1f1f1f"

                self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="#d0d0d0")

                # subtle grid lines
                if j < cols - 1:
                    self.canvas.create_line(x1, y0, x1, y1, fill="#eeeeee")
                if i < rows - 1:
                    self.canvas.create_line(x0, y1, x1, y1, fill="#eeeeee")

    def _draw_event(self, event: dict):
        et = event["type"]
        rr, cc = event["cell"]

        if (rr, cc) == self.start or (rr, cc) == self.end:
            return

        colors = {
            "visit": "#ffd166",
            "backtrack": "#f4a261",
            "path": "#8a5cf6",
        }
        fill = colors.get(et)
        if not fill:
            return

        x0 = cc * self.cell_size
        y0 = rr * self.cell_size
        x1 = x0 + self.cell_size
        y1 = y0 + self.cell_size
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="#c9c9c9")

    # ---------------- Animation ----------------
    def start_visualization(self):
        if self._anim.is_running():
            return
        if not self.maze:
            messagebox.showerror("No maze", "Generate a maze first.")
            return

        result = solve_with_steps(self.maze, self.start, self.end, self.algorithm.get())
        self._anim.reset(result.steps)

        # Fresh base redraw so overlays aren't stacked.
        self._draw_base_grid()

        if not result.steps:
            self.status_var.set("No path found for this maze.")
            self.btn_step.configure(state="disabled")
            self.btn_start.configure(state="normal")
            return

        self.status_var.set(f"Animating {self.algorithm.get()} (explore + path)...")

        self.btn_start.configure(state="disabled")
        self.btn_step.configure(state="normal")

        self._anim.start()
        self._schedule_next_tick()

    def _schedule_next_tick(self):
        self._cancel_animation()
        delay = int(self.speed_ms.get())
        self._after_id = self.after(delay, self._tick)

    def _tick(self):
        if not self._anim.is_running():
            return

        ev = self._anim.next_event()
        if ev is None:
            self._anim.stop()
            self.btn_start.configure(state="normal")
            self.btn_step.configure(state="disabled")
            self.status_var.set("Done.")
            return

        self._draw_event(ev)
        self._schedule_next_tick()

    def _cancel_animation(self):
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = None

    def step_once(self):
        if self._anim.is_running():
            return
        if not self._anim.state.steps:
            return

        self._draw_event(self._anim.next_event() or {})

        if not self._anim.has_more():
            self.btn_step.configure(state="disabled")
            self.status_var.set("Done.")


def main():
    app = RatInMazeUI()
    app.mainloop()

