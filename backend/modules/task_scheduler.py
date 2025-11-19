"""Dynamic task scheduler for R-v0.4 load balancing."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from modules.log_manager import log_manager


@dataclass(order=True)
class ScheduledTask:
    priority: int
    name: str = field(compare=False)
    payload: Dict[str, object] = field(compare=False, default_factory=dict)


class TaskScheduler:
    def __init__(self):
        self._queue: List[ScheduledTask] = []
        self._registry: Dict[str, ScheduledTask] = {}

    def update_tasks(self, tasks: List[Dict[str, object]]) -> None:
        self._queue.clear()
        self._registry.clear()
        for entry in tasks:
            name = entry.get("name")
            priority = int(entry.get("priority", 5))
            payload = entry.get("payload", {})
            if not name:
                continue
            task = ScheduledTask(priority, name, payload)
            heapq.heappush(self._queue, task)
            self._registry[name] = task
        log_manager.info(f"[TaskScheduler] Loaded {len(self._registry)} tasks.")

    def pop_next(self) -> Optional[ScheduledTask]:
        if not self._queue:
            return None
        task = heapq.heappop(self._queue)
        self._registry.pop(task.name, None)
        log_manager.debug(f"[TaskScheduler] Dispatching task {task.name} (priority {task.priority}).")
        return task

    def peek_schedule(self) -> List[Dict[str, object]]:
        return [
            {"name": task.name, "priority": task.priority, "payload": task.payload}
            for task in sorted(self._queue)
        ]

    def modify_priority(self, name: str, priority: int) -> bool:
        task = self._registry.get(name)
        if not task:
            return False
        task.priority = priority
        heapq.heapify(self._queue)
        return True


scheduler = TaskScheduler()
