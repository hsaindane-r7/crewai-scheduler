from __future__ import annotations

from typing import List
import re

from crewai import Agent, Crew, LLM, Process, Task

from models import Goal, Schedule, SubTask


# Configure a shared Groq-backed LLM for all agents.
# Make sure you have GROQ_API_KEY set in your environment.
groq_llm = LLM(
    model="groq/llama-3.3-70b-versatile",
)


def build_planner_agent() -> Agent:
    return Agent(
        role="Task Planner",
        goal=(
            "Break a high-level user goal into clear, atomic subtasks suitable for "
            "execution and scheduling."
        ),
        backstory=(
            "You are an expert project planner. You think in terms of concrete steps "
            "with clear outcomes. You never skip obvious prerequisites."
        ),
        llm=groq_llm,
        verbose=True,
        allow_delegation=False,
    )


def build_executor_agent() -> Agent:
    return Agent(
        role="Task Executor & Refiner",
        goal=(
            "Take a list of subtasks and refine them with realistic time estimates, "
            "priorities, and a logical order of execution."
        ),
        backstory=(
            "You are an experienced execution-focused project manager. You know how "
            "long realistic tasks take and how to order them for flow."
        ),
        llm=groq_llm,
        verbose=True,
        allow_delegation=False,
    )


def _subtasks_from_llm_output(text: str, goal: Goal) -> List[SubTask]:
    """
    Very lightweight parser for the planner's textual output.

    For real use you would probably ask the LLM for strict JSON and then parse
    with Pydantic; here we keep it minimal but a bit smarter by only treating
    lines that look like numbered list items (e.g. \"1. Do X\") as subtasks.
    """
    lines = [ln.strip("- ").strip() for ln in text.splitlines() if ln.strip()]

    # Treat only numbered list items like "1. Do X" as subtasks.
    numbered_item = re.compile(r"^\d+\.")

    subtasks: List[SubTask] = []
    for idx, line in enumerate(lines, start=1):
        if not numbered_item.match(line):
            # Skip headings, \"Estimated duration\", \"Priority order\", JSON, etc.
            continue
        subtasks.append(
            SubTask(
                id=f"task-{idx}",
                goal_title=goal.title,
                description=line,
                order=idx,
            )
        )
    return subtasks


def _schedule_from_executor_output(
    text: str,
    goal: Goal,
    original_subtasks: List[SubTask],
) -> Schedule:
    """
    Extremely simple mapping that keeps the original subtasks but allows the
    executor to override estimates and ordering if it emits a parseable pattern.

    To keep this example focused on crewai wiring, we fall back to the original
    subtasks when parsing fails.
    """
    # TODO: You could enhance this to parse JSON, YAML, or "id: estimate" lines.
    return Schedule(goal=goal, subtasks=original_subtasks)


def build_crew() -> Crew:
    planner = build_planner_agent()
    executor = build_executor_agent()

    planning_task = Task(
        description=(
            "You are helping plan a specific user goal.\n"
            "Goal title: {goal_title}\n"
            "Goal description: {goal_description}\n\n"
            "Break this goal into 5–10 concrete subtasks that are SPECIFIC to achieving "
            "this exact goal. Each subtask should be a clear, actionable step.\n"
            "DO NOT give generic project planning advice. Focus on the actual goal.\n\n"
            "Return them as a numbered list like:\n"
            "1. [Specific action for this goal]\n"
            "2. [Another specific action]\n"
            "3. [etc.]\n"
        ),
        agent=planner,
        expected_output=(
            "A numbered list of 5–10 concrete, actionable subtasks that are specific "
            "to achieving the user's stated goal. No generic advice."
        ),
    )

    execution_task = Task(
        description=(
            "You are refining the subtasks for the same specific user goal.\n"
            "Goal title: {goal_title}\n"
            "Goal description: {goal_description}\n\n"
            "You are given a numbered list of subtasks. For each subtask:\n"
            "- Suggest a realistic time estimate in minutes.\n"
            "- Optionally adjust the order for a more logical execution sequence.\n\n"
            "Return a readable list in the same numbered format, and then an optional "
            "JSON array under a 'subtasks' key, where each item has:\n"
            "  task, estimated_duration (int, minutes), priority (int).\n"
        ),
        agent=executor,
        expected_output=(
            "A refined list of subtasks with realistic time estimates (in minutes) "
            "and a logical execution order. Each subtask should include its estimated "
            "duration and priority order."
        ),
    )

    return Crew(
        agents=[planner, executor],
        tasks=[planning_task, execution_task],
        process=Process.sequential,
        verbose=True,
    )


def plan_and_execute(goal: Goal) -> Schedule:
    """
    High-level convenience wrapper:
    1. Run the crew to get planner + executor outputs.
    2. Convert the planner text into SubTask objects.
    3. Let the executor influence the final Schedule (for now, passthrough).
    """
    crew = build_crew()

    # The goal is injected via context into both tasks.
    result = crew.kickoff(inputs={"goal_title": goal.title, "goal_description": goal.description})

    # The Crew result can be agent-specific; we rely on the full text output here.
    planner_text = str(result)  # CrewResult.__str__ usually returns the combined text.
    subtasks = _subtasks_from_llm_output(planner_text, goal)

    # In a more advanced version you'd give the executor explicit structure and parse it.
    schedule = _schedule_from_executor_output(
        text=planner_text,
        goal=goal,
        original_subtasks=subtasks,
    )
    return schedule


