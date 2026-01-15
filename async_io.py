from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import anyio

from models import Schedule


async def save_schedule(path: Path, schedule: Schedule) -> None:
    """
    Asynchronously persist a schedule as JSON.

    This simulates saving to a DB; for a real app, this function could instead
    talk to an async database client.
    """
    data = schedule.model_dump(mode="json")
    payload = {
        "saved_at": datetime.now().isoformat(),
        "schedule": data,
    }
    json_str = json.dumps(payload, indent=2)

    # anyio provides a uniform async file API.
    async with await anyio.open_file(path, mode="w") as f:
        await f.write(json_str)


async def load_schedule(path: Path) -> Schedule:
    """
    Asynchronously load a schedule from JSON, if it exists.
    """
    if not path.exists():
        raise FileNotFoundError(path)

    async with await anyio.open_file(path, mode="r") as f:
        content = await f.read()

    raw: Dict[str, Any] = json.loads(content)
    schedule_data = raw["schedule"]
    return Schedule.model_validate(schedule_data)


async def mock_async_calendar_block(schedule: Schedule) -> None:
    """
    Pretend to call an external calendar API to block time for each subtask.

    In a real integration this function would use an async HTTP client like
    httpx.AsyncClient to hit Google Calendar / Outlook / etc.
    """
    for task in schedule.subtasks:
        # Simulate network latency without actually sleeping for long.
        await anyio.sleep(0.01)
        # Here we just log to stdout; swap with real API call as needed.
        print(
            f"[calendar] Would block: {task.description} "
            f"from {task.scheduled_start} to {task.scheduled_end}"
        )


