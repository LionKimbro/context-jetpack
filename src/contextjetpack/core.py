"""Single worker machine. No Tk objects cross either queue.

Only the worker reads/writes g. Tk posts plain events and consumes plain
results. Each event is reduced before its requested effects run, in order.
"""

import copy
import importlib.util
import queue
import shutil
import subprocess
import sys
import threading
import uuid
from pathlib import Path

from .chat_pack import open_path, stage_read_now_files
from .compiler import compile_message
from .defaults import DOCUMENTS, new_data
from .profiles import (
    global_store, list_profiles, load_initial_profile, profile_path,
    project_store, read_profile, write_profile,
)
from .registry import load_registry, resolve_document, resolve_registry_path


# Queues are the sole cross-thread communication channel; mutated, never rebound.
requests = queue.Queue()
results = queue.Queue()
g = {
    "project": None, "registry-option": "", "registry-path": None,
    "entries": None, "documents": {}, "data": None,
    "profile-id": "default", "store": "project", "running": False,
    "ready": False, "profile-ids": {},
}
chat_folders = []  # Only folders created by this session, cleaned on worker shutdown.


def emit(result):
    results.put(copy.deepcopy(result))


def reduce_event(event):
    kind = event["type"]
    if kind == "START":
        g["project"] = Path(event["project"])
        g["registry-option"] = event.get("registry", "")
        return [{"type": "INITIALIZE"}]
    if kind == "CLOSE":
        return [{"type": "SHUTDOWN"}]
    if not g["ready"]:
        raise ValueError("Context Jetpack has not finished starting.")
    if "data" in event:
        g["data"] = event["data"]
    if kind == "FORM_CHANGED":
        return [{"type": "MEASURE"}]
    if kind == "NEW":
        g["data"] = new_data()
        g["data"]["title"] = "Untitled"
        g["profile-id"] = str(uuid.uuid4())
        g["store"] = None
        g["profile-ids"].clear()
        return [{"type": "PROJECT_PROFILE", "message": "New profile. Not saved."}]
    if kind in {"LIST", "LOAD", "SAVE", "COMPILE", "REFRESH", "DOCUMENT", "LIBRARIAN"}:
        return [event]
    raise ValueError(f"Unknown event: {kind}")


def resolve_store(name):
    if name == "project":
        return project_store(g["project"])
    if name == "global":
        return global_store()
    raise ValueError("Choose the project or global profile store.")


def refresh_registry():
    g["registry-path"] = resolve_registry_path(g["registry-option"])
    g["entries"] = load_registry(g["registry-path"])
    g["documents"].clear()
    for definition in DOCUMENTS:
        key, document_id = definition["key"], definition["document-id"]
        if not document_id:
            g["documents"][key] = {"status": "no-id", "error": "No Librarian document ID"}
            continue
        try:
            resolved = resolve_document(g["entries"], document_id)
            path = resolved["path"]
            if not path.is_file():
                raise ValueError(f"File not found: {path}")
            g["documents"][key] = {"status": "ok", "path": str(path), "tokens": None}
        except (ValueError, OSError) as exc:
            g["documents"][key] = {"status": "missing", "error": str(exc)}


def measure_selected_documents():
    totals = {"required": 0, "recommended": 0}
    unknown = 0
    for definition in DOCUMENTS:
        selection = g["data"]["documents"][definition["key"]]
        if not selection["selected"] or not definition["document-id"]:
            continue
        info = g["documents"].get(definition["key"], {})
        if info.get("status") != "ok":
            unknown += 1
            continue
        try:
            if info["tokens"] is None:
                text = Path(info["path"]).read_text(encoding="utf-8", errors="ignore")
                info["tokens"] = (len(text) + 3) // 4
            totals[selection["designation"]] += info["tokens"]
        except OSError:
            unknown += 1
    emit({"type": "MEASURED", "totals": totals, "unknown": unknown})


def project_profile(message):
    saved = g["store"] is not None and profile_path(
        resolve_store(g["store"]), g["profile-id"]
    ).is_file()
    emit({
        "type": "PROFILE", "data": g["data"], "id": g["profile-id"],
        "store": g["store"], "message": message, "saved": saved,
    })
    measure_selected_documents()


def route_effect(effect):
    kind = effect["type"]
    if kind == "INITIALIZE":
        # Validate before creating any application directories or reading profiles.
        project_store(g["project"])
        g["data"], message = load_initial_profile(g["project"])
        g["profile-id"] = "default"
        g["store"] = "project"
        g["profile-ids"].clear()
        g["profile-ids"]["project"] = "default"
        try:
            refresh_registry()
        except Exception as exc:
            g["entries"] = None
            message += f" | Registry unavailable: {exc}"
        g["ready"] = True
        emit({"type": "CATALOG", "documents": g["documents"]})
        project_profile(message)
    elif kind == "PROJECT_PROFILE":
        project_profile(effect["message"])
    elif kind == "MEASURE":
        measure_selected_documents()
    elif kind == "LIST":
        store = resolve_store(effect["store"])
        items, errors = list_profiles(store)
        emit({"type": "PROFILES", "store": effect["store"], "items": items, "errors": errors})
    elif kind == "LOAD":
        data = read_profile(resolve_store(effect["store"]), effect["id"])
        g["data"] = data
        g["profile-id"] = effect["id"]
        g["store"] = effect["store"]
        g["profile-ids"].clear()
        g["profile-ids"][g["store"]] = g["profile-id"]
        project_profile(f"Loaded {g['store']} profile: {data['title']}")
    elif kind == "SAVE":
        store = resolve_store(effect["store"])
        # A shared global store must not conflate every project's Default profile.
        profile_id = g["profile-ids"].get(effect["store"], g["profile-id"])
        if effect["store"] not in g["profile-ids"] and effect["store"] != g["store"]:
            profile_id = str(uuid.uuid4())
        path = write_profile((store, profile_id), g["data"])
        g["profile-id"], g["store"] = profile_id, effect["store"]
        g["profile-ids"][g["store"]] = profile_id
        emit({"type": "SAVED", "data": g["data"], "store": g["store"], "path": str(path)})
    elif kind == "REFRESH":
        refresh_registry()
        emit({"type": "CATALOG", "documents": g["documents"]})
        measure_selected_documents()
        emit({"type": "STATUS", "message": f"Registry refreshed: {g['registry-path']}"})
    elif kind == "COMPILE":
        refresh_registry()
        emit({"type": "CATALOG", "documents": g["documents"]})
        missing = [
            item["label"] for item in DOCUMENTS
            if item["document-id"] and g["data"]["documents"][item["key"]]["selected"]
            and g["documents"][item["key"]]["status"] != "ok"
        ]
        if missing:
            raise ValueError("Can't find selected reference documents:\n" + "\n".join(missing))
        message = compile_message(g["data"], g["entries"])
        detail = "Message copied to clipboard."
        if effect.get("chat"):
            folder, copied = stage_read_now_files(
                g["data"], g["entries"], project_store(g["project"])
            )
            chat_folders.append(folder)
            open_path(folder)
            detail += f" {len(copied)} read-now file(s) staged in {folder}."
        emit({"type": "CLIPBOARD", "text": message, "message": detail})
        measure_selected_documents()
    elif kind == "DOCUMENT":
        definition = next(item for item in DOCUMENTS if item["key"] == effect["key"])
        if g["entries"] is None:
            raise ValueError("Registry is not loaded. Use Refresh References.")
        path = resolve_document(g["entries"], definition["document-id"])["path"]
        if effect["action"] == "copy":
            emit({"type": "CLIPBOARD", "text": str(path), "message": f"Copied path: {path}"})
        else:
            open_path(path.parent if effect["action"] == "containing" else path)
    elif kind == "LIBRARIAN":
        registry = resolve_registry_path(g["registry-option"])
        # The public command is librarian; use this Python's installed Librarian2
        # entry point to avoid accidentally launching the older librarian package.
        if importlib.util.find_spec("librarian2") is None:
            raise ValueError("Librarian2 is not installed in this Python. Install lions-librarian to use this button.")
        subprocess.Popen(
            [sys.executable, "-c", "from librarian2._entry import main; main()",
             "--path.registry", str(registry)],
            cwd=Path.home(),
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        emit({"type": "STATUS", "message": "Librarian launched. Use Refresh References after editing its registry."})
    elif kind == "SHUTDOWN":
        for folder in chat_folders:
            shutil.rmtree(folder, ignore_errors=True)
        chat_folders.clear()
        g["running"] = False
        emit({"type": "CLOSED"})


def run_worker():
    g["running"] = True
    while g["running"]:
        event = requests.get()
        try:
            for effect in reduce_event(event):
                route_effect(effect)
        except Exception as exc:
            emit({"type": "ERROR", "message": str(exc) or type(exc).__name__,
                  "fatal": event["type"] == "START"})
            if event["type"] == "START":
                g["running"] = False
        finally:
            if event.get("busy"):
                emit({"type": "DONE"})
            requests.task_done()


def start_worker(options):
    if g["running"]:
        raise RuntimeError("Context Jetpack worker is already running.")
    g["ready"] = False
    g["documents"].clear()
    requests.put({"type": "START", **options})
    worker = threading.Thread(target=run_worker, name="context-jetpack-core", daemon=False)
    worker.start()
    return worker
