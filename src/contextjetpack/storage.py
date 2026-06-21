import json
import os
import tempfile
from pathlib import Path

from .defaults import DOCUMENTS, new_data


def load_data(path):
    path = Path(path)
    data = new_data()
    if not path.exists():
        return data

    incoming = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(incoming, dict):
        raise ValueError("data.json must contain a JSON object")

    data["purpose"] = str(incoming.get("purpose", ""))
    incoming_options = incoming.get("options", {})
    if isinstance(incoming_options, dict):
        for key in data["options"]:
            data["options"][key] = bool(incoming_options.get(key, data["options"][key]))

    incoming_documents = incoming.get("documents", {})
    if isinstance(incoming_documents, dict):
        for item in DOCUMENTS:
            key = item["key"]
            incoming_item = incoming_documents.get(key, {})
            if not isinstance(incoming_item, dict):
                continue
            current = data["documents"][key]
            current["selected"] = bool(incoming_item.get("selected", current["selected"]))
            designation = incoming_item.get("designation", current["designation"])
            if designation in {"required", "recommended"}:
                current["designation"] = designation
            current["reason"] = str(incoming_item.get("reason", current["reason"]))
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
