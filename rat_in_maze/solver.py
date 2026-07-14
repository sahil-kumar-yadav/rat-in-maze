from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

Cell = Tuple[int, int]


@dataclass(frozen=True)
class SolveResult:
    path: Optional[List[Cell]]
    steps: List[dict]


def _in_bounds(r: int, c: int, x: int, y: int) -> bool:
    return 0 <= x < r and 0 <= y < c


def solve_with_steps(
    maze: List[List[int]],
    start: Cell,
    end: Cell,
    algo: str,
) -> SolveResult:
    """Generate animation steps for BFS/DFS.

    Maze representation: 1=open, 0=wall.

    steps format: {"type": "visit"|"backtrack"|"path", "cell": (r,c)}
    """

    r = len(maze)
    c = len(maze[0]) if r else 0

    dirs: Sequence[Tuple[int, int]] = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    parent: Dict[Cell, Optional[Cell]] = {start: None}

    steps: List[dict] = []

    if algo == "BFS":
        q = deque([start])
        visited: Set[Cell] = {start}
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
                if not _in_bounds(r, c, nr, nc):
                    continue
                if maze[nr][nc] != 1:
                    continue
                if nxt in visited:
                    continue

                visited.add(nxt)
                parent[nxt] = cur
                q.append(nxt)

    elif algo == "DFS":
        # Iterative DFS with explicit stack; provides a simple backtrack animation.
        stack: List[Cell] = [start]
        visited: Set[Cell] = {start}

        # To animate backtracking: when a node is popped after exhausting its neighbors.
        # Since we don't have recursion frames, we approximate by emitting backtrack when
        # we pop a node that isn't the end and doesn't expand to any new nodes.
        # This keeps behavior lightweight while improving the UI.
        while stack:
            cur = stack.pop()

            if cur != start and cur != end:
                steps.append({"type": "visit", "cell": cur})
            if cur == end:
                break

            cr, cc = cur
            expanded_any = False
            for dr, dc in dirs[::-1]:
                nr, nc = cr + dr, cc + dc
                nxt = (nr, nc)
                if not _in_bounds(r, c, nr, nc):
                    continue
                if maze[nr][nc] != 1:
                    continue
                if nxt in visited:
                    continue

                visited.add(nxt)
                parent[nxt] = cur
                stack.append(nxt)
                expanded_any = True

            if not expanded_any and cur != start and cur != end:
                steps.append({"type": "backtrack", "cell": cur})

    else:
        raise ValueError(f"Unknown algorithm: {algo}")

    if end not in parent:
        return SolveResult(path=None, steps=[])

    # Reconstruct path
    path: List[Cell] = []
    cur: Optional[Cell] = end
    while cur is not None:
        path.append(cur)
        cur = parent.get(cur)
    path.reverse()

    steps.extend({"type": "path", "cell": cell} for cell in path)

    return SolveResult(path=path, steps=steps)

