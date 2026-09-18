"""Click-only jev-ultrafast goals for AU form sites."""

from __future__ import annotations

from datetime import datetime

JEV_SOURCES = (
    {
        "name": "racing_sports",
        "url": "https://www.racingandsports.com.au/form-guide",
        "label": "Racing & Sports",
    },
    {
        "name": "punting_form",
        "url": "https://puntingform.com.au/",
        "label": "Punting Form",
    },
    {
        "name": "racing_com",
        "url": "https://www.racing.com/form",
        "label": "racing.com form",
    },
    {
        "name": "sportsbet_form",
        "url": "https://form-guide.com.au/",
        "label": "Sportsbet form guide",
    },
)


def _pretty_date(iso_date: str) -> str:
    return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d %B %Y").lstrip("0")


def jev_tasks(iso_date: str) -> list[dict]:
    pretty = _pretty_date(iso_date)
    tasks = []
    for source in JEV_SOURCES:
        url = source["url"]
        if source["name"] == "sportsbet_form":
            url = f"https://form-guide.com.au/day/{iso_date}"
        if source["name"] == "racing_com":
            url = f"https://www.racing.com/form/{iso_date}"
        goal = (
            f"Open the {source['label']} page for Australian thoroughbreds on {pretty} ({iso_date}). "
            "Use only clicks, selects, waits, and scrolls — do not type. "
            "Stop when meeting names and race fields or tips for that date are visible."
        )
        tasks.append({"name": source["name"], "url": url, "goal": goal, "label": source["label"]})
    return tasks


def _import_agent():
    from jev_ultrafast import Agent

    return Agent


def run_jev_task(task: dict, agent_cls=None) -> dict:
    cls = agent_cls or _import_agent()
    last: dict | None = None
    with cls(task["url"], task["goal"]) as agent:
        for state in agent.run():
            last = state
    page = (last or {}).get("page") or {}
    status = (last or {}).get("status")
    return {
        "ok": status == "done",
        "source": task.get("name"),
        "label": task.get("label"),
        "url": page.get("url") or task.get("url"),
        "text": page.get("text") or "",
        "title": page.get("title"),
        "status": status,
        "history": (last or {}).get("history") or [],
        "elapsed_ms": (last or {}).get("elapsed_ms"),
    }


def scrape_all(iso_date: str, agent_cls=None) -> list[dict]:
    results = []
    for task in jev_tasks(iso_date):
        try:
            results.append(run_jev_task(task, agent_cls=agent_cls))
        except Exception as exc:
            results.append({"ok": False, "source": task["name"], "error": str(exc), "text": ""})
    return results
