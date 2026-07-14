from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

Cell = Tuple[int, int]


@dataclass(frozen=True)
class MazeResult:
    maze: List[List[int]]  # 1=open, 0=wall
    start: Cell
    end: Cell
    solvable: bool


def make_blank_maze(rows: int, cols: int) -> List[List[int]]:
    return [[0 for _ in range(cols)] for __ in range(rows)]


def generate_random_solvable_maze(
    rows: int,
    cols: int,
    algorithm: str,
    *,
    open_prob: float = 0.72,
    max_tries: int = 150,
    seed: Optional[int] = None,
    solver_fn=None,
) -> MazeResult:
    """Generate a random 0/1 maze and ensure at least one path exists.

    Requires `solver_fn(maze, start, end, algorithm)` which returns SolveResult.
    """

    if rows < 3 or cols < 3:
        raise ValueError("Rows and Cols must be at least 3.")

    if solver_fn is None:
        raise ValueError("solver_fn must be provided")

    rng = random.Random(seed)

    start = (0, 0)
    end = (rows - 1, cols - 1)

    for _ in range(max_tries):
        m = [[1 if rng.random() < open_prob else 0 for _ in range(cols)] for __ in range(rows)]
        m[start[0]][start[1]] = 1
        m[end[0]][end[1]] = 1

        # Ensure local openness around start/end to improve UX.
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            sr, sc = start[0] + dr, start[1] + dc
            if 0 <= sr < rows and 0 <= sc < cols:
                m[sr][sc] = 1
            er, ec = end[0] + dr, end[1] + dc
            if 0 <= er < rows and 0 <= ec < cols:
                m[er][ec] = 1

        result = solver_fn(m, start, end, algorithm)
        if result.path:
            return MazeResult(maze=m, start=start, end=end, solvable=True)

    # Fallback: still return a maze (visualization will show no path)
    m = [[1 if rng.random() < open_prob else 0 for _ in range(cols)] for __ in range(rows)]
    m[start[0]][start[1]] = 1
    m[end[0]][end[1]] = 1
    return MazeResult(maze=m, start=start, end=end, solvable=False)

