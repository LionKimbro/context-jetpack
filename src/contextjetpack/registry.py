import json
from pathlib import Path

import machineroot


def resolve_registry_path(configured_path):
    configured = str(configured_path or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(machineroot.get("coding-librarian")).expanduser().resolve()


def load_registry(path):
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("registry")
    if not isinstance(entries, dict):
        raise ValueError(f"registry field must be a JSON object: {path}")
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
