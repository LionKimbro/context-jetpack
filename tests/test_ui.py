"""Exercise real Tk widgets on the tkintertester event loop."""

import copy
import json
import tkinter as tk

from tkintertester import harness

from contextjetpack import ui
from contextjetpack import core
from contextjetpack.defaults import DOCUMENTS, new_data


def test_profile_projection_preserves_missing_selections_and_action_buttons():
    def enter():
        ui.widgets.clear()
        ui.document_widgets.clear()
        ui.action_buttons.clear()
        ui.form_inputs.clear()
        ui.catalog.clear()
        ui.g.update({"root": harness.g["root"], "window": tk.Toplevel(harness.g["root"]),
                     "draft": new_data(), "saved": None, "busy": False, "store": "project",
                     "projecting": False, "closing": False, "chooser": None, "change-after": None})
        ui.build_window()

    def reset():
        if ui.g["change-after"] is not None:
            ui.g["root"].after_cancel(ui.g["change-after"])
            ui.g["change-after"] = None
        ui.g["window"].destroy()

    def check_projection():
        data = new_data()
        data["title"], data["hook"] = "My profile", "A wider description"
        data["documents"]["project-directory-system"]["selected"] = True
        ui.project_profile({"data": data, "store": "global", "message": "Loaded", "saved": True})
        ui.catalog["general-background"] = {"status": "ok"}
        ui.catalog["project-directory-system"] = {"status": "missing"}
        ui.project_busy_state()
        assert ui.collect_form() == data
        assert ui.document_widgets["project-directory-system"]["selected"].get() is True
        buttons = ui.action_buttons
        labels = [button.cget("text") for button in buttons]
        for label in ("Open Document", "Containing Folder", "Copy Path"):
            assert labels.count(label) == len(DOCUMENTS)
        assert "Load Global Profile" in labels
        assert "Save Project Profile" in labels
        assert "disabled" not in ui.document_widgets["general-background"]["actions"][0].state()
        assert "disabled" in ui.document_widgets["project-directory-system"]["actions"][0].state()
        saved = copy.deepcopy(ui.g["saved"])
        ui.widgets["title"].set("Renamed")
        assert ui.g["saved"] == saved
        assert "Unsaved" in ui.widgets["profile-status"].get()
        return "success", None

    harness.tests.clear()
    harness.add_test("Profiles project into the grouped form", [check_projection])
    harness.set_resetfn(reset)
    harness.run_host(enter, "x")
    results = json.loads(harness.get_results("J"))
    harness.g["root"].destroy()
    assert all(item["status"] == "success" for item in results), results


def test_save_and_load_chooser_through_real_worker_queues(tmp_path, monkeypatch):
    (tmp_path / "db").mkdir()
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"registry": {}}), encoding="utf-8")
    monkeypatch.setattr("contextjetpack.profiles.machineroot.get", lambda key: str(tmp_path / "global"))
    while not core.results.empty():
        core.results.get_nowait()
    pending = {"thread": None, "ticks": 0, "tick-after": None}

    def tick():
        pending["ticks"] += 1
        pending["tick-after"] = ui.g["root"].after(10, tick)

    def enter():
        ui.widgets.clear()
        ui.document_widgets.clear()
        ui.action_buttons.clear()
        ui.form_inputs.clear()
        ui.catalog.clear()
        ui.g.update({"root": harness.g["root"], "window": tk.Toplevel(harness.g["root"]),
                     "draft": new_data(), "saved": None, "busy": True, "store": None,
                     "projecting": False, "closing": False, "chooser": None, "change-after": None})
        ui.build_window()
        pending["thread"] = core.start_worker({"project": str(tmp_path), "registry": str(registry)})
        ui.g["poll-after"] = ui.g["root"].after(40, ui.handle_worker_results_on_tk_thread)
        tick()

    def reset():
        for token in (ui.g["poll-after"], ui.g["change-after"], pending["tick-after"]):
            if token is not None:
                ui.g["root"].after_cancel(token)
        if pending["thread"].is_alive():
            core.requests.put({"type": "CLOSE"})
            pending["thread"].join(timeout=5)
        ui.g["window"].destroy()

    def edit_and_save():
        if ui.g["busy"]:
            return "wait", 20
        ui.widgets["title"].set("Round trip")
        ui.widgets["hook"].set("Choose this one")
        ui.handle_when_action_is_clicked({"type": "SAVE", "store": "global"})
        return "next", 20

    def open_chooser():
        if ui.g["busy"]:
            return "wait", 20
        assert ui.g["store"] == "global"
        assert "Saved" in ui.widgets["profile-status"].get()
        ui.handle_when_action_is_clicked({"type": "LIST", "store": "global"})
        return "next", 20

    def load_selection():
        if ui.g["busy"] or ui.g["chooser"] is None:
            return "wait", 20
        tree = ui.widgets["chooser-tree"]
        profile_id = tree.get_children()[0]
        assert tuple(tree.item(profile_id, "values")) == ("Round trip", "Choose this one")
        tree.selection_set(profile_id)
        ui.handle_when_action_is_clicked({"type": "LOAD", "store": "global", "id": profile_id})
        return "next", 20

    def verify_loaded_and_stop():
        if ui.g["busy"]:
            return "wait", 20
        assert ui.widgets["title"].get() == "Round trip"
        assert ui.widgets["hook"].get() == "Choose this one"
        assert ui.g["chooser"] is None
        assert pending["ticks"] > 0
        ui.g["root"].after_cancel(ui.g["poll-after"])
        ui.g["poll-after"] = None
        core.requests.put({"type": "CLOSE"})
        return "next", 20

    def verify_worker_stopped():
        if pending["thread"].is_alive():
            return "wait", 20
        return "success", None

    harness.tests.clear()
    harness.set_resetfn(reset)
    harness.add_test("Save and choose a global profile", [
        edit_and_save, open_chooser, load_selection, verify_loaded_and_stop, verify_worker_stopped,
    ])
    harness.run_host(enter, "x")
    results = json.loads(harness.get_results("J"))
    harness.g["root"].destroy()
    assert all(item["status"] == "success" for item in results), results
