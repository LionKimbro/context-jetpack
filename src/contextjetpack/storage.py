import json
import os
import tempfile
from pathlib import Path

from .defaults import DOCUMENTS, new_data


def load_data(path):
    path = Path(path)
    if not path.exists():
        return new_data()

    return normalize_data(read_object(path))


def read_object(path):
    path = Path(path)

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Could not read saved data {path}: {exc}") from None
    try:
        incoming = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Saved data is not valid JSON ({path}): {exc}") from None
    if not isinstance(incoming, dict):
        raise ValueError(f"Saved data must contain a JSON object: {path}")

    return incoming


def normalize_data(incoming):
    """Accept old form keys or portable profile document IDs."""
    data = new_data()
    data["title"] = str(incoming.get("title", "Default"))
    data["hook"] = str(incoming.get("hook", ""))

    data["purpose"] = str(incoming.get("purpose", ""))
    incoming_options = incoming.get("options", {})
    if isinstance(incoming_options, dict):
        for key in data["options"]:
            data["options"][key] = bool(incoming_options.get(key, data["options"][key]))

    incoming_documents = incoming.get("documents", {})
    if isinstance(incoming_documents, dict):
        for item in DOCUMENTS:
            key = item["key"]
            incoming_item = incoming_documents.get(
                item["document-id"], incoming_documents.get(key, {})
            )
            if not isinstance(incoming_item, dict):
                continue
            current = data["documents"][key]
            current["selected"] = bool(incoming_item.get("selected", current["selected"]))
            designation = incoming_item.get("designation", current["designation"])
            if designation in {"required", "recommended"}:
                current["designation"] = designation
            current["reason"] = str(incoming_item.get("reason", current["reason"]))
    known = {item["key"] for item in DOCUMENTS} | {item["document-id"] for item in DOCUMENTS}
    data["extra-documents"] = {
        key: value for key, value in incoming_documents.items() if key not in known
    } if isinstance(incoming_documents, dict) else {}
    return data


def save_data(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"

    fd, temp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
        os.replace(temp_path, path)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise
