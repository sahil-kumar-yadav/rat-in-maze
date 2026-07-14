from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional


@dataclass
class AnimationState:
    steps: List[dict]
    index: int = 0
    running: bool = False


class Animator:
    def __init__(self):
        self.state = AnimationState(steps=[])

    def reset(self, steps: List[dict]):
        self.state = AnimationState(steps=list(steps), index=0, running=False)

    def has_more(self) -> bool:
        return self.state.index < len(self.state.steps)

    def next_event(self) -> Optional[dict]:
        if self.state.index >= len(self.state.steps):
            return None
        ev = self.state.steps[self.state.index]
        self.state.index += 1
        return ev

    def start(self):
        self.state.running = True

    def stop(self):
        self.state.running = False

    def is_running(self) -> bool:
        return self.state.running


def play_with_tk_after(
    *,
    after_func: Callable[[int, Callable[[], None]], str],
    cancel_func: Callable[[str], None],
    delay_ms: int,
    on_tick: Callable[[], None],
):
    """Small helper so UI can schedule the next frame."""
    after_id = after_func(delay_ms, on_tick)
    return after_id

