import os
import threading
from types import SimpleNamespace
from uuid import uuid4

import pytest

from ecotrace.callbacks import EcoTraceLangChainCallback, EcoTraceLangChainHandler
from ecotrace.callbacks import langchain as lc_module


class FakeTracker:
    """Deterministic stand-in for EmissionsTracker (no hardware access)."""

    instances = 0

    def __init__(self, **kwargs):
        FakeTracker.instances += 1
        self.kwargs = kwargs
        self.active = False
        self.final_emissions_g = 0.0
        self.duration_seconds = 0.0

    def start(self):
        self.active = True

    def stop(self):
        self.active = False
        self.final_emissions_g = 0.5
        self.duration_seconds = 0.25
        return self.final_emissions_g / 1000.0


@pytest.fixture
def fake_tracker(monkeypatch):
    FakeTracker.instances = 0
    monkeypatch.setattr(lc_module, "EmissionsTracker", FakeTracker)
    return FakeTracker


def test_import_alias_and_lazy_export():
    assert EcoTraceLangChainHandler is EcoTraceLangChainCallback


def test_module_imports_without_langchain_installed():
    # BaseCallbackHandler always resolves, real or stand-in.
    assert issubclass(EcoTraceLangChainCallback, lc_module.BaseCallbackHandler)


def test_single_call_lifecycle(fake_tracker):
    cb = EcoTraceLangChainCallback(project_name="unit")
    run_id = uuid4()

    cb.on_llm_start({"name": "FakeLLM"}, ["hi"], run_id=run_id)
    assert cb.active_runs == 1

    response = SimpleNamespace(llm_output={"token_usage": {"total_tokens": 42}})
    cb.on_llm_end(response, run_id=run_id)

    assert cb.active_runs == 0
    assert len(cb.records) == 1
    rec = cb.records[0]
    assert rec["run_id"] == str(run_id)
    assert rec["model"] == "FakeLLM"
    assert rec["status"] == "success"
    assert rec["emissions_g"] == pytest.approx(0.5)
    assert rec["emissions_kg"] == pytest.approx(0.0005)
    assert rec["token_usage"] == {"total_tokens": 42}
    assert cb.total_emissions_g == pytest.approx(0.5)
    assert cb.total_duration_s == pytest.approx(0.25)


def test_chat_model_start_uses_invocation_params(fake_tracker):
    cb = EcoTraceLangChainCallback()
    run_id = uuid4()
    cb.on_chat_model_start(
        {"id": ["langchain", "chat_models", "ChatX"]},
        [[]],
        run_id=run_id,
        invocation_params={"model": "gpt-test"},
    )
    cb.on_llm_end(SimpleNamespace(llm_output=None), run_id=run_id)
    assert cb.records[0]["model"] == "gpt-test"
    assert "token_usage" not in cb.records[0]


def test_error_path_stops_tracker(fake_tracker):
    cb = EcoTraceLangChainCallback()
    run_id = uuid4()
    cb.on_llm_start(None, ["x"], run_id=run_id)
    tracker = cb._active[run_id]["tracker"]

    cb.on_llm_error(RuntimeError("boom"), run_id=run_id)

    assert not tracker.active
    assert cb.active_runs == 0
    assert cb.records[0]["status"] == "error"
    assert "boom" in cb.records[0]["error"]
    assert cb.summary()["errors"] == 1


def test_unknown_run_id_is_ignored(fake_tracker):
    cb = EcoTraceLangChainCallback()
    cb.on_llm_end(SimpleNamespace(llm_output=None), run_id=uuid4())
    cb.on_llm_error(RuntimeError("x"), run_id=uuid4())
    assert cb.records == []


def test_overlapping_runs_tracked_independently(fake_tracker):
    cb = EcoTraceLangChainCallback()
    a, b = uuid4(), uuid4()
    cb.on_llm_start({"name": "A"}, ["a"], run_id=a)
    cb.on_llm_start({"name": "B"}, ["b"], run_id=b)
    assert cb.active_runs == 2
    assert cb._active[a]["tracker"] is not cb._active[b]["tracker"]

    cb.on_llm_end(SimpleNamespace(llm_output=None), run_id=b)
    cb.on_llm_end(SimpleNamespace(llm_output=None), run_id=a)

    assert [r["model"] for r in cb.records] == ["B", "A"]
    assert cb.total_emissions_g == pytest.approx(1.0)


def test_trackers_are_reused(fake_tracker):
    cb = EcoTraceLangChainCallback()
    for _ in range(5):
        run_id = uuid4()
        cb.on_llm_start(None, ["x"], run_id=run_id)
        cb.on_llm_end(SimpleNamespace(llm_output=None), run_id=run_id)
    assert fake_tracker.instances == 1
    assert len(cb.records) == 5


def test_thread_safety(fake_tracker):
    cb = EcoTraceLangChainCallback()

    def worker():
        for _ in range(20):
            run_id = uuid4()
            cb.on_llm_start(None, ["x"], run_id=run_id)
            cb.on_llm_end(SimpleNamespace(llm_output=None), run_id=run_id)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(cb.records) == 160
    assert cb.active_runs == 0
    assert cb.total_emissions_g == pytest.approx(80.0)


def test_reset_and_summary(fake_tracker):
    cb = EcoTraceLangChainCallback(project_name="summ")
    run_id = uuid4()
    cb.on_llm_start(None, ["x"], run_id=run_id)
    cb.on_llm_end(SimpleNamespace(llm_output=None), run_id=run_id)

    summary = cb.summary()
    assert summary["project_name"] == "summ"
    assert summary["calls"] == 1

    cb.reset()
    assert cb.records == []
    assert cb.total_emissions_g == 0.0


def test_real_tracker_writes_csv(tmp_path):
    cb = EcoTraceLangChainCallback(
        project_name="lc_csv_test",
        output_dir=str(tmp_path),
        output_file="lc.csv",
    )
    run_id = uuid4()
    cb.on_llm_start({"name": "FakeLLM"}, ["hi"], run_id=run_id)
    _ = sum(i * i for i in range(20000))
    cb.on_llm_end(SimpleNamespace(llm_output=None), run_id=run_id)

    assert cb.total_emissions_g >= 0.0
    path = os.path.join(str(tmp_path), "lc.csv")
    assert os.path.isfile(path)
    with open(path, encoding="utf-8") as f:
        assert "lc_csv_test" in f.read()


def test_end_to_end_with_langchain():
    fake_llms = pytest.importorskip("langchain_core.language_models.fake")

    cb = EcoTraceLangChainCallback(project_name="e2e")
    llm = fake_llms.FakeListLLM(responses=["one", "two", "three"])

    llm.invoke("q1", config={"callbacks": [cb]})
    llm.batch(["q2", "q3"], config={"callbacks": [cb]})

    assert len(cb.records) == 3
    assert all(r["status"] == "success" for r in cb.records)
    assert cb.active_runs == 0
    assert cb.total_emissions_g >= 0.0


def test_end_to_end_chat_model_with_langchain():
    fake_chat = pytest.importorskip("langchain_core.language_models.fake_chat_models")

    cb = EcoTraceLangChainCallback(project_name="e2e_chat")
    chat = fake_chat.FakeListChatModel(responses=["hello"])
    chat.invoke("hi", config={"callbacks": [cb]})

    assert len(cb.records) == 1
    assert cb.records[0]["status"] == "success"
