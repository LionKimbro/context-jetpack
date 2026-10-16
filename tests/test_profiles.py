import json

import pytest

from contextjetpack.defaults import new_data
from contextjetpack.profiles import (
    global_store, list_profiles, load_initial_profile, project_store,
    read_profile, write_profile,
)
from contextjetpack.storage import save_data


def test_missing_db_stops_without_creating_directories(tmp_path):
    with pytest.raises(ValueError, match="Run Context Jetpack in your project folder"):
        load_initial_profile(tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_legacy_migration_is_non_destructive_and_does_not_repeat(tmp_path):
    (tmp_path / "db").mkdir()
    legacy = tmp_path / ".context-jetpack" / "data.json"
    data = new_data()
    data["purpose"] = "Original project"
    save_data(legacy, data)
    original = legacy.read_bytes()
    imported, message = load_initial_profile(tmp_path)
    assert imported["title"] == "Default"
    assert "Imported" in message
    assert imported["purpose"] == "Original project"
    imported["purpose"] = "Saved new profile"
    write_profile((project_store(tmp_path), "default"), imported)
    loaded, _ = load_initial_profile(tmp_path)
    assert loaded["purpose"] == "Saved new profile"
    assert legacy.read_bytes() == original


def test_profile_round_trip_uses_ids_and_preserves_unknown_references(tmp_path):
    data = new_data()
    data.update({"title": "Same title", "hook": "A hook", "extra-documents": {
        "future-document.v1": {"selected": True, "designation": "required", "reason": "Future"}
    }})
    path = write_profile((tmp_path, "one"), data)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert "lionsphilosophyofprogramming.style-cards-2026.globals.v1" in saved["documents"]
    assert "style-card-globals" not in saved["documents"]
    loaded = read_profile(tmp_path, "one")
    assert loaded == data
    loaded["title"] = "Renamed"
    write_profile((tmp_path, "one"), loaded)
    assert len(list((tmp_path / "profiles").glob("*.json"))) == 1
    assert read_profile(tmp_path, "one")["title"] == "Renamed"


def test_global_store_is_machine_root_relative_and_lists_corrupt_files(tmp_path, monkeypatch):
    monkeypatch.setattr("contextjetpack.profiles.machineroot.get", lambda key: str(tmp_path))
    store = global_store()
    assert store == tmp_path / "context-jetpack"
    write_profile((store, "one"), new_data())
    (store / "profiles" / "bad.json").write_text("not json", encoding="utf-8")
    items, errors = list_profiles(store)
    assert len(items) == 1
    assert "bad.json" in errors[0]


def test_empty_or_relative_global_root_cannot_fall_back_to_project(tmp_path, monkeypatch):
    monkeypatch.setattr("contextjetpack.profiles.machineroot.get", lambda key: "")
    with pytest.raises(ValueError, match="absolute directory"):
        global_store()


def test_profile_id_cannot_escape_store(tmp_path):
    with pytest.raises(ValueError, match="Invalid profile ID"):
        read_profile(tmp_path, "../../outside")


def test_failed_atomic_save_preserves_previous_profile(tmp_path, monkeypatch):
    original = new_data()
    original["purpose"] = "Original"
    path = write_profile((tmp_path, "one"), original)
    contents = path.read_bytes()

    def fail_replace(source, target):
        raise PermissionError("File is busy")

    monkeypatch.setattr("contextjetpack.storage.os.replace", fail_replace)
    original["purpose"] = "Changed"
    with pytest.raises(PermissionError):
        write_profile((tmp_path, "one"), original)
    assert path.read_bytes() == contents
    assert not list(path.parent.glob("*.tmp"))


def test_unsupported_profile_version_is_not_silently_loaded(tmp_path):
    path = write_profile((tmp_path, "one"), new_data())
    incoming = json.loads(path.read_text(encoding="utf-8"))
    incoming["version"] = 99
    path.write_text(json.dumps(incoming), encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported"):
        read_profile(tmp_path, "one")
