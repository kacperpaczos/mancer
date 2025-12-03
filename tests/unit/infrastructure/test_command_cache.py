from __future__ import annotations

from unittest.mock import MagicMock

import polars as pl

from mancer.application.command_cache import CommandCache
from mancer.domain.model.command_result import CommandResult


def _result(value: str, success: bool = True) -> CommandResult:
    return CommandResult(
        raw_output=value,
        success=success,
        structured_output=pl.DataFrame({"value": [value]}),
        exit_code=0 if success else 1,
    )


class TestCommandCache:
    def test_store_and_get_returns_same_result(self) -> None:
        cache = CommandCache(max_size=3)
        cache.store("cmd-1", "echo 1", _result("one"))

        retrieved = cache.get("cmd-1")
        assert retrieved is not None
        assert retrieved.raw_output == "one"

    def test_store_respects_size_limit(self) -> None:
        cache = CommandCache(max_size=2)

        cache.store("a", "cmd a", _result("a"))
        cache.store("b", "cmd b", _result("b"))
        cache.store("c", "cmd c", _result("c"))

        assert cache.get("a") is None  # evicted
        assert cache.get("c") is not None
        assert len(cache) == 2

    def test_history_and_filters(self) -> None:
        cache = CommandCache(max_size=5)
        cache.store("success", "ok", _result("ok", success=True))
        cache.store("failure", "fail", _result("fail", success=False))

        full_history = cache.get_history()
        success_only = cache.get_history(success_only=True)

        assert len(full_history) == 2
        assert len(success_only) == 1
        assert success_only[0][0] == "success"

    def test_statistics_counts_success_and_errors(self) -> None:
        cache = CommandCache(max_size=5)
        cache.store("ok", "cmd", _result("ok", success=True))
        cache.store("err", "cmd", _result("err", success=False))

        stats = cache.get_statistics()
        assert stats["total_commands"] == 2
        assert stats["success_count"] == 1
        assert stats["error_count"] == 1

    def test_export_data_includes_results(self) -> None:
        cache = CommandCache(max_size=2)
        cache.store("cmd", "echo", _result("ok"), metadata={"user": "dev"})

        exported = cache.export_data(include_results=True)

        assert "history" in exported
        assert "statistics" in exported
        assert "cmd" in exported["results"]
        assert exported["results"]["cmd"]["metadata"]["metadata"]["user"] == "dev"

    def test_set_auto_refresh_toggles_state(self, monkeypatch) -> None:
        cache = CommandCache(auto_refresh=False)
        started = {"called": False}

        def fake_start():
            started["called"] = True
            cache._refresh_thread = MagicMock()

        monkeypatch.setattr(cache, "_start_refresh_thread", fake_start)
        cache.set_auto_refresh(True, interval=3)

        assert cache._auto_refresh
        assert cache._refresh_interval == 3
        assert started["called"]

        stopped = {"called": False}
        monkeypatch.setattr(cache, "stop_refresh", lambda: stopped.__setitem__("called", True))
        cache.set_auto_refresh(False)

        assert not cache._auto_refresh
        assert stopped["called"]

    def test_clear_resets_cache(self) -> None:
        cache = CommandCache(max_size=3)
        cache.store("cmd-1", "command", _result("one"))
        cache.clear()

        assert len(cache) == 0
        assert cache.get_history() == []

