"""Profile files and migration. Called only by the worker."""

import json
import re
from pathlib import Path

import machineroot

from .defaults import DOCUMENTS, new_data
from .storage import load_data, normalize_data, read_object, save_data


def project_store(project):
    project = Path(project)
    if not (project / "db").is_dir():
        raise ValueError(
            f"No db/ directory in {project}. Run Context Jetpack in your project folder."
        )
    return project / "db" / "context-jetpack"


def global_store():
    try:
        location = machineroot.get("db-root-2026")
    except (machineroot.MachineRootError, KeyError) as exc:
        raise ValueError(
            'Global profiles need Machine Root key "db-root-2026": ' + str(exc)
        ) from None
    path = Path(location).expanduser()
    if not str(location).strip() or not path.is_absolute():
        raise ValueError('Machine Root key "db-root-2026" must be an absolute directory path.')
    return path / "context-jetpack"


def profile_path(store, profile_id):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", profile_id):
        raise ValueError("Invalid profile ID.")
    return Path(store) / "profiles" / f"{profile_id}.json"


def read_profile(store, profile_id):
    path = profile_path(store, profile_id)
    if not path.is_file():
        raise ValueError(f"Profile no longer exists: {path}")
    incoming = read_object(path)
    if incoming.get("version") != 1:
        raise ValueError(f"Unsupported or missing profile version: {path}")
    for key in ("title", "hook", "purpose"):
        if not isinstance(incoming.get(key), str):
            raise ValueError(f"Profile {key} must be text: {path}")
    for key in ("documents", "options"):
        if not isinstance(incoming.get(key), dict):
            raise ValueError(f"Profile {key} must be an object: {path}")
    for key in ("request-ack", "encourage-questions"):
        if not isinstance(incoming["options"].get(key), bool):
            raise ValueError(f"Profile option {key} must be true or false: {path}")
    for document_id, item in incoming["documents"].items():
        if (not isinstance(item, dict)
                or not isinstance(item.get("selected"), bool)
                or item.get("designation") not in ("required", "recommended")
                or not isinstance(item.get("reason"), str)):
            raise ValueError(f"Invalid profile reference {document_id}: {path}")
    return normalize_data(incoming)


def write_profile(destination, data):
    store, profile_id = destination
    if not data["title"].strip():
        raise ValueError("Give the profile a title before saving.")
    documents = dict(data.get("extra-documents", {}))
    for item in DOCUMENTS:
        documents[item["document-id"] or item["key"]] = data["documents"][item["key"]]
    saved = {
        "version": 1,
        "title": data["title"],
        "hook": data["hook"],
        "purpose": data["purpose"],
        "options": data["options"],
        "documents": documents,
    }
    path = profile_path(store, profile_id)
    save_data(path, saved)
    return path


def list_profiles(store):
    items, errors = [], []
    for path in (Path(store) / "profiles").glob("*.json"):
        try:
            data = read_profile(store, path.stem)
            items.append({"id": path.stem, "title": data["title"], "hook": data["hook"]})
        except (ValueError, OSError) as exc:
            errors.append(str(exc))
    items.sort(key=lambda item: (item["title"].casefold(), item["id"]))
    return items, errors


def load_initial_profile(project):
    store = project_store(project)
    if profile_path(store, "default").exists():
        data = read_profile(store, "default")
        return data, f"Loaded project profile: {data['title']}"
    legacy_dir = Path(project) / ".context-jetpack"
    legacy_path = legacy_dir / "data.json"
    config_path = legacy_dir / "config.json"
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))
        configured = config.get("options", {}).get("projpath.data")
        if configured:
            legacy_path = legacy_dir / Path(configured).expanduser()
    if legacy_path.exists():
        data = load_data(legacy_path)
        data["title"] = "Default"
        write_profile((store, "default"), data)
        return data, f"Imported old form as project profile Default. Original preserved: {legacy_path}"
    return new_data(), "New Default profile. Use Save Project Profile or Save Global Profile to keep it."
