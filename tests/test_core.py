import copy
import json
import queue
import threading

import pytest

from contextjetpack import core
from contextjetpack.defaults import new_data


def receive(kind):
    while True:
        result = core.results.get(timeout=5)
        if result["type"] == "ERROR":
            pytest.fail(result["message"])
        if result["type"] == kind:
            return result


@pytest.fixture
def worker(tmp_path, monkeypatch):
    while not core.results.empty():
        core.results.get_nowait()
    (tmp_path / "db").mkdir()
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"registry": {}}), encoding="utf-8")
    monkeypatch.setattr("contextjetpack.profiles.machineroot.get", lambda key: str(tmp_path / "global"))
    thread = core.start_worker({"project": str(tmp_path), "registry": str(registry)})
    initial = receive("PROFILE")
    assert not initial["saved"]
    try:
        yield tmp_path
    finally:
        core.requests.put({"type": "CLOSE"})
        thread.join(timeout=5)
        assert not thread.is_alive()


def test_saves_run_on_worker_and_project_global_defaults_do_not_collide(worker, monkeypatch):
    writes = []
    real_write = core.write_profile

    def record_write(destination, data):
        writes.append(threading.current_thread().name)
        return real_write(destination, data)

    monkeypatch.setattr(core, "write_profile", record_write)
    data = new_data()
    data["title"] = "My profile"
    for store in ("project", "global", "project", "global"):
        core.requests.put({"type": "SAVE", "store": store, "data": copy.deepcopy(data)})
        receive("SAVED")
    assert writes == ["context-jetpack-core"] * 4
    assert len(list((worker / "db/context-jetpack/profiles").glob("*.json"))) == 1
    global_files = list((worker / "global/context-jetpack/profiles").glob("*.json"))
    assert len(global_files) == 1
    assert global_files[0].stem != "default"


def test_compile_and_close_never_save_profiles(worker):
    data = new_data()
    for item in data["documents"].values():
        item["selected"] = False
    core.requests.put({"type": "COMPILE", "data": data})
    result = receive("CLIPBOARD")
    assert "No reference documents were selected" in result["text"]
    assert not (worker / "db/context-jetpack/profiles").exists()


def test_failed_load_keeps_current_profile_and_worker_recovers(worker):
    core.requests.put({"type": "LOAD", "store": "project", "id": "missing"})
    while True:
        result = core.results.get(timeout=5)
        if result["type"] == "ERROR":
            assert "no longer exists" in result["message"]
            break
    core.requests.put({"type": "SAVE", "store": "project", "data": new_data()})
    assert receive("SAVED")["data"]["title"] == "Default"


def test_start_without_db_exits_worker_and_does_not_create_store(tmp_path):
    while not core.results.empty():
        core.results.get_nowait()
    thread = core.start_worker({"project": str(tmp_path)})
    result = core.results.get(timeout=5)
    assert result["type"] == "ERROR" and result["fatal"]
    thread.join(timeout=5)
    assert not thread.is_alive()
    assert list(tmp_path.iterdir()) == []


def test_loading_profile_and_compiling_use_new_registry_locations(worker):
    reference = worker / "moved-reference.md"
    reference.write_text("Current reference", encoding="utf-8")
    registry = worker / "registry.json"
    registry.write_text(json.dumps({"registry": {
        "lionsphilosophyofprogramming.style-cards-2026.globals.v1": {
            "location": [{"path": str(reference)}], "title": "Globals"
        }
    }}), encoding="utf-8")
    data = new_data()
    for item in data["documents"].values():
        item["selected"] = False
    data["documents"]["style-card-globals"]["selected"] = True
    data["hook"] = "Find this in the chooser"
    core.requests.put({"type": "SAVE", "store": "project", "data": data})
    receive("SAVED")
    core.requests.put({"type": "NEW"})
    assert receive("PROFILE")["data"]["title"] == "Untitled"
    core.requests.put({"type": "LOAD", "store": "project", "id": "default"})
    loaded = receive("PROFILE")
    assert loaded["data"]["hook"] == data["hook"]
    core.requests.put({"type": "COMPILE"})
    assert str(reference) in receive("CLIPBOARD")["text"]
