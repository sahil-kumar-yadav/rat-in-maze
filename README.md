# rat-in-maze

A Python Tkinter visualization for the classic **Rat in a Maze** pathfinding problem.

## Features
- Generates a random maze (with start at top-left and end at bottom-right)
- Visualizes **BFS** (shortest path) and **DFS** search
- Animates explored cells and the final path
- Speed control + step-by-step mode

## Requirements
- Python 3.10+
- Standard library only (Tkinter)

## Run
```bash
python app.py
```

## How it works
- Maze cells: `1` = open, `0` = wall (internal representation)
- Start: `(0, 0)`
- End: `(rows-1, cols-1)`

## UI controls
- **Generate Maze**: creates a new solvable maze when possible
- **Algorithm**: choose `BFS` or `DFS`
- **Speed (ms)**: animation delay per step
- **Start Visualization**: runs animation automatically
- **Step**: advances one animation event at a time (after you start)
- **Reset**: redraws the current maze view and clears overlays

