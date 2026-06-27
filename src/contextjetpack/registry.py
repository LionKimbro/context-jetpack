import json
from pathlib import Path

import machineroot


def resolve_registry_path(configured_path):
    configured = str(configured_path or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    try:
        location = machineroot.get("coding-librarian")
    except machineroot.MachineRootKeyError:
        raise ValueError(
            'No registry configured. Set registry.path, or add a "coding-librarian" '
            "key to Machine Root pointing at your Librarian2 registry.json."
        ) from None
    return Path(location).expanduser().resolve()


def load_registry(path):
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ValueError(f"Registry file not found: {path}") from None
    except OSError as exc:
        raise ValueError(f"Could not read registry file {path}: {exc}") from None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Registry file is not valid JSON ({path}): {exc}") from None
    if not isinstance(data, dict):
        raise ValueError(f"Registry file must contain a JSON object: {path}")
    entries = data.get("registry")
    if not isinstance(entries, dict):
        raise ValueError(f'Registry file must have a "registry" object: {path}')
    return entries


def resolve_document(entries, document_id):
    if document_id not in entries:
        raise ValueError(f"document ID is not in the registry: {document_id}")

    entry = entries[document_id]
    locations = entry.get("location", [])
    if not isinstance(locations, list):
        raise ValueError(f"registry location must be a list: {document_id}")

    for location in locations:
        if isinstance(location, dict) and location.get("path"):
            path = Path(location["path"]).expanduser()
            if not path.is_absolute():
                path = path.resolve()
            return {
                "document-id": document_id,
                "title": entry.get("title") or document_id,
                "path": path,
            }
    raise ValueError(f"document has no filesystem path: {document_id}")
