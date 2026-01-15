from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

import anyio
from dotenv import load_dotenv

from agents import plan_and_execute
from async_io import load_schedule, mock_async_calendar_block, save_schedule
from models import Goal

# Load environment variables from .env file
load_dotenv()


async def async_main() -> None:
    parser = argparse.ArgumentParser(
        description="Multi-agent task planner and executor demo (crewai + pydantic + async)."
    )
    parser.add_argument(
        "title",
        type=str,
        help="Short title for your goal (e.g. 'Launch personal blog')",
    )
    parser.add_argument(
        "--description",
        type=str,
        default="",
        help="Longer free-text description of what you want to achieve.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("schedule.json"),
        help="Where to save the generated schedule JSON.",
    )
    parser.add_argument(
        "--pretty-output",
        type=Path,
        default=Path("schedule.txt"),
        help="Where to save a human-readable text version of the schedule.",
    )
    args = parser.parse_args()

    goal = Goal(
        title=args.title,
        description=args.description or args.title,
    )

    print(f"Planning goal: {goal.title}")
    schedule = plan_and_execute(goal)

    # Add simple sequential time blocks starting now.
    scheduled_with_times = schedule.with_time_blocks()

    # Persist and mock calendar blocking concurrently using asyncio.gather.
    await asyncio.gather(
        save_schedule(args.output, scheduled_with_times),
        mock_async_calendar_block(scheduled_with_times),
    )

    # Write a simple, human-readable schedule file.
    lines = [f"Goal: {goal.title}", ""]
    for idx, task in enumerate(scheduled_with_times.subtasks, start=1):
        est = f"{task.estimate_minutes} min" if task.estimate_minutes else "unknown duration"
        lines.append(f"{idx}. {task.description}")
        lines.append(f"   - Start: {task.scheduled_start:%Y-%m-%d %H:%M}")
        lines.append(f"   - Estimate: {est}")
        lines.append("")
    args.pretty_output.write_text("\n".join(lines), encoding="utf-8")

    print(f"\nSchedule JSON saved to: {args.output}")
    print(f"Readable schedule saved to: {args.pretty_output}")

    # Print a short, straightforward summary to stdout.
    print("\nPlanned subtasks:")
    for idx, task in enumerate(scheduled_with_times.subtasks, start=1):
        print(f"{idx}. {task.description}")


def main() -> None:
    anyio.run(async_main)


if __name__ == "__main__":
    main()
