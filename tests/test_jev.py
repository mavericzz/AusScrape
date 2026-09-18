from src.sources.jev import JEV_SOURCES, jev_tasks, run_jev_task


def test_jev_tasks_cover_all_browser_sources_without_requiring_typed_text():
    tasks = jev_tasks("2026-09-20")
    names = {t["name"] for t in tasks}
    assert names == {s["name"] for s in JEV_SOURCES}
    for task in tasks:
        assert "2026-09-20" in task["goal"] or "20 September 2026" in task["goal"]
        assert "TYPE_TEXT" not in task["goal"]
        assert task["url"].startswith("https://")


def test_run_jev_task_uses_injected_agent_and_keeps_page_text():
    class FakeAgent:
        def __init__(self, url, goal):
            self.url = url
            self.goal = goal

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def run(self):
            yield {
                "status": "done",
                "page": {"url": self.url, "text": "Armidale R1 fields visible", "title": "Form"},
                "history": [{"action": "DONE"}],
                "elapsed_ms": 12,
            }

    result = run_jev_task(
        {"name": "racing_sports", "url": "https://example.test/form", "goal": "Stop when fields are visible."},
        agent_cls=FakeAgent,
    )
    assert result["ok"] is True
    assert "Armidale" in result["text"]
    assert result["source"] == "racing_sports"
