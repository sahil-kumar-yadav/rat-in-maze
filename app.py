import tkinter as tk
from tkinter import ttk, messagebox
import random
from collections import deque


class RatInMazeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rat in a Maze - Visualization (BFS/DFS)")
        self.resizable(False, False)

        # --- State ---
        self.rows = tk.IntVar(value=10)
        self.cols = tk.IntVar(value=10)
        self.cell_size = 28

        self.speed_ms = tk.IntVar(value=50)
        self.algorithm = tk.StringVar(value="BFS")

        self.maze = []  # 2D: 1=open, 0=wall
        self.start = (0, 0)
        self.end = (9, 9)

        self._anim_after_id = None
        self._is_running = False

        self._explore_steps = []  # list of events for animation
        self._path_cells = set()

        # --- Layout ---
        outer = ttk.Frame(self, padding=10)
        outer.grid(row=0, column=0, sticky="nsew")

        # Controls
        ctrl = ttk.LabelFrame(outer, text="Controls", padding=10)
        ctrl.grid(row=0, column=0, sticky="nw")

        ttk.Label(ctrl, text="Rows").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(ctrl, from_=3, to=30, width=6, textvariable=self.rows, command=self.reset_view).grid(
            row=0, column=1, sticky="w", padx=(6, 12)
        )
        ttk.Label(ctrl, text="Cols").grid(row=1, column=0, sticky="w")
        ttk.Spinbox(ctrl, from_=3, to=30, width=6, textvariable=self.cols, command=self.reset_view).grid(
            row=1, column=1, sticky="w", padx=(6, 12)
        )

        ttk.Label(ctrl, text="Algorithm").grid(row=2, column=0, sticky="w", pady=(10, 0))
        algo = ttk.Combobox(ctrl, values=["BFS", "DFS"], state="readonly", width=8, textvariable=self.algorithm)
        algo.grid(row=2, column=1, sticky="w", padx=(6, 12), pady=(10, 0))

        ttk.Label(ctrl, text="Speed (ms)").grid(row=3, column=0, sticky="w", pady=(10, 0))
        ttk.Scale(ctrl, from_=10, to=200, orient="horizontal", length=120, variable=self.speed_ms).grid(
            row=3, column=1, sticky="w", padx=(6, 12), pady=(10, 0)
        )

        btns = ttk.Frame(ctrl)
        btns.grid(row=4, column=0, columnspan=2, sticky="w", pady=(12, 0))

        self.btn_generate = ttk.Button(btns, text="Generate Maze", command=self.generate_maze)
        self.btn_generate.grid(row=0, column=0, padx=(0, 10))

        self.btn_start = ttk.Button(btns, text="Start Visualization", command=self.start_visualization)
        self.btn_start.grid(row=0, column=1)

        self.btn_step = ttk.Button(btns, text="Step", command=self.step_once, state="disabled")
        self.btn_step.grid(row=1, column=0, pady=(10, 0), padx=(0, 10))

        self.btn_reset = ttk.Button(btns, text="Reset", command=self.reset_view)
        self.btn_reset.grid(row=1, column=1, pady=(10, 0))

        self.status_var = tk.StringVar(value="Click 'Generate Maze' to begin.")
        ttk.Label(outer, textvariable=self.status_var).grid(row=1, column=0, sticky="w", pady=(10, 0))

        # Canvas
        canvas_frame = ttk.LabelFrame(outer, text="Maze", padding=10)
        canvas_frame.grid(row=0, column=1, padx=(20, 0))

        self.canvas = tk.Canvas(canvas_frame, width=1, height=1, bg="white", highlightthickness=0)
        self.canvas.grid(row=0, column=0)

        # Create initial maze
        self.reset_view(initial=True)

    # ---------------- Maze generation ----------------
    def reset_view(self, initial=False):
        if self._anim_after_id is not None:
            try:
                self.after_cancel(self._anim_after_id)
            except Exception:
                pass
            self._anim_after_id = None

        self._is_running = False
        self._explore_steps = []
        self._path_cells = set()

        self.btn_step.configure(state="disabled")
        self.btn_start.configure(state="normal")

        self.start = (0, 0)
        self.end = (int(self.rows.get()) - 1, int(self.cols.get()) - 1)

        size_w = int(self.cols.get()) * self.cell_size
        size_h = int(self.rows.get()) * self.cell_size
        self.canvas.configure(width=size_w, height=size_h)

        self.canvas.delete("all")

        # If not initial, keep existing maze; otherwise create one.
        if initial or not self.maze:
            self.maze = self._make_blank_maze()
            # show as blank/open maze
            for r in range(self.end[0] + 1):
                for c in range(self.end[1] + 1):
                    self.maze[r][c] = 1
            self.maze[self.start[0]][self.start[1]] = 1
            self.maze[self.end[0]][self.end[1]] = 1

        self.draw_maze()
        self.status_var.set("Click 'Generate Maze' to begin." if initial else "Reset. Generate or start again.")

    def _make_blank_maze(self):
        r = int(self.rows.get())
        c = int(self.cols.get())
        return [[0 for _ in range(c)] for __ in range(r)]

    def generate_maze(self):
        if self._is_running:
            return

        r = int(self.rows.get())
        c = int(self.cols.get())
        if r < 3 or c < 3:
            messagebox.showerror("Invalid size", "Rows and Cols must be at least 3.")
            return

        # Generate with a reasonable open probability; retry until solvable.
        # This avoids frustration where visualization finds no path.
        open_prob = 0.72
        max_tries = 150

        self.start = (0, 0)
        self.end = (r - 1, c - 1)

        maze = None
        solvable = False
        for _ in range(max_tries):
            m = [[1 if random.random() < open_prob else 0 for _ in range(c)] for __ in range(r)]
            m[self.start[0]][self.start[1]] = 1
            m[self.end[0]][self.end[1]] = 1
            # Ensure some openness around start/end
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                sr, sc = self.start[0] + dr, self.start[1] + dc
                er, ec = self.end[0] + dr, self.end[1] + dc
                if 0 <= sr < r and 0 <= sc < c:
                    m[sr][sc] = 1
                if 0 <= er < r and 0 <= ec < c:
                    m[er][ec] = 1

            path, steps = self.solve_with_steps(m, self.start, self.end, self.algorithm.get())
            if path:
                maze = m
                solvable = True
                self._explore_steps = steps
                self._path_cells = set(path)
                break

        if not solvable:
            # Fall back to a maze anyway; visualization will show no path.
            maze = [[1 if random.random() < open_prob else 0 for _ in range(c)] for __ in range(r)]
            maze[self.start[0]][self.start[1]] = 1
            maze[self.end[0]][self.end[1]] = 1
            self._explore_steps = []
            self._path_cells = set()

        self.maze = maze
        self.draw_maze()
        self.status_var.set("Maze generated. Click 'Start Visualization'.")

        self.btn_step.configure(state="disabled")
        self.btn_start.configure(state="normal")

    # ---------------- Drawing ----------------
    def draw_maze(self):
        r = len(self.maze)
        c = len(self.maze[0]) if r else 0

        for i in range(r):
            for j in range(c):
                x0 = j * self.cell_size
                y0 = i * self.cell_size
                x1 = x0 + self.cell_size
                y1 = y0 + self.cell_size

                cell = self.maze[i][j]
                if (i, j) == self.start:
                    fill = "#1e90ff"  # blue
                elif (i, j) == self.end:
                    fill = "#ff4d4d"  # red
                else:
                    fill = "#2e8b57" if cell == 1 else "#1f1f1f"  # open / wall

                self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="#333333")

                # grid line labels for debugging could be omitted

    def draw_event(self, event):
        """event: dict with keys: type, cell=(r,c)"""
        et = event["type"]
        rr, cc = event["cell"]

        x0 = cc * self.cell_size
        y0 = rr * self.cell_size
        x1 = x0 + self.cell_size
        y1 = y0 + self.cell_size

        # Keep start/end colors
        if (rr, cc) == self.start:
            return
        if (rr, cc) == self.end:
            return

        if et == "visit":
            self.canvas.create_rectangle(x0, y0, x1, y1, fill="#ffd166", outline="#333333")
        elif et == "backtrack":
            self.canvas.create_rectangle(x0, y0, x1, y1, fill="#f4a261", outline="#333333")
        elif et == "path":
            self.canvas.create_rectangle(x0, y0, x1, y1, fill="#8a5cf6", outline="#333333")

    def clear_overlay(self):
        # Redraw base maze while keeping start/end
        self.draw_maze()

    # ---------------- Solvers (produce animation steps) ----------------
    def solve_with_steps(self, maze, start, end, algo):
        r = len(maze)
        c = len(maze[0]) if r else 0

        def in_bounds(x, y):
            return 0 <= x < r and 0 <= y < c

        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        # steps: visit events; then later path events
        steps = []
        parent = {start: None}

        if algo == "BFS":
            q = deque([start])
            visited = {start}
            while q:
                cur = q.popleft()
                if cur != start and cur != end:
                    steps.append({"type": "visit", "cell": cur})
                if cur == end:
                    break
                cr, cc = cur
                for dr, dc in dirs:
                    nr, nc = cr + dr, cc + dc
                    nxt = (nr, nc)
                    if not in_bounds(nr, nc):
                        continue
                    if maze[nr][nc] != 1:
                        continue
                    if nxt in visited:
                        continue
                    visited.add(nxt)
                    parent[nxt] = cur
                    q.append(nxt)

        elif algo == "DFS":
            # Iterative DFS with explicit stack
            stack = [start]
            visited = {start}
            while stack:
                cur = stack.pop()
                if cur != start and cur != end:
                    steps.append({"type": "visit", "cell": cur})
                if cur == end:
                    break
                cr, cc = cur
                # To make animation a bit nicer, expand in a fixed order
                for dr, dc in dirs[::-1]:
                    nr, nc = cr + dr, cc + dc
                    nxt = (nr, nc)
                    if not in_bounds(nr, nc):
                        continue
                    if maze[nr][nc] != 1:
                        continue
                    if nxt in visited:
                        continue
                    visited.add(nxt)
                    parent[nxt] = cur
                    stack.append(nxt)
                # Optional: backtrack animation is harder without recursive stack details.
        else:
            raise ValueError("Unknown algorithm")

        if end not in parent:
            return None, []

        # reconstruct path
        path = []
        cur = end
        while cur is not None:
            path.append(cur)
            cur = parent[cur]
        path.reverse()

        path_events = [{"type": "path", "cell": cell} for cell in path]
        steps.extend(path_events)
        return path, steps

    # ---------------- Animation control ----------------
    def start_visualization(self):
        if self._is_running:
            return

        if not self.maze:
            messagebox.showerror("No maze", "Generate a maze first.")
            return

        self.clear_overlay()

        # Ensure steps are computed for current maze+algorithm
        path, steps = self.solve_with_steps(self.maze, self.start, self.end, self.algorithm.get())
        self._explore_steps = steps
        self._path_cells = set(path) if path else set()

        if not steps:
            self.status_var.set("No path found for this maze.")
            return

        self.status_var.set(f"Animating {self.algorithm.get()} search + path...")

        self.btn_start.configure(state="disabled")
        self.btn_step.configure(state="normal")

        self._is_running = True
        self._anim_index = 0
        self._run_animation()

    def _run_animation(self):
        if not self._is_running:
            return
        if self._anim_index >= len(self._explore_steps):
            self._is_running = False
            self.btn_start.configure(state="normal")
            self.btn_step.configure(state="disabled")
            self.status_var.set("Done.")
            return

        event = self._explore_steps[self._anim_index]
        self._anim_index += 1
        self.draw_event(event)

        self._anim_after_id = self.after(int(self.speed_ms.get()), self._run_animation)

    def step_once(self):
        if self._is_running:
            # If currently auto-running, stepping is disabled by state.
            return
        if not hasattr(self, "_anim_index"):
            self._anim_index = 0

        if self._anim_index >= len(self._explore_steps):
            self.status_var.set("Nothing more to step.")
            return

        event = self._explore_steps[self._anim_index]
        self._anim_index += 1
        self.draw_event(event)

        if self._anim_index >= len(self._explore_steps):
            self.status_var.set("Done.")
            self.btn_step.configure(state="disabled")


def main():
    app = RatInMazeApp()
    app.mainloop()


if __name__ == "__main__":
    main()

