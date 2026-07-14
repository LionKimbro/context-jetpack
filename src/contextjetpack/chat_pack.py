import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .defaults import DOCUMENTS
from .registry import resolve_document


TEMP_PREFIX = "context-jetpack-chat-"


def stage_read_now_files(data, registry_entries, parent_dir=None):
    parent = Path(parent_dir) if parent_dir else None
    if parent:
        parent.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix=TEMP_PREFIX, dir=parent))
    copied = []
    used_names = set()

    for definition in DOCUMENTS:
        state = data["documents"][definition["key"]]
        if not state["selected"] or state["designation"] != "required":
            continue
        document_id = definition["document-id"]
        if not document_id:
            continue
        resolved = resolve_document(registry_entries, document_id)
        source = resolved["path"]
        target = folder / unique_attachment_name(document_id, source, used_names)
        shutil.copy2(source, target)
        copied.append(
            {
                "document-id": document_id,
                "source": source,
                "target": target,
            }
        )

    return folder, copied


def cleanup_chat_folders(project_dir):
    project = Path(project_dir).resolve()
    if not project.exists():
        return

    for folder in project.glob(f"{TEMP_PREFIX}*"):
        try:
            if not folder.is_dir():
                continue
            resolved = folder.resolve()
            if resolved.parent != project:
                continue
            shutil.rmtree(resolved, ignore_errors=True)
        except OSError:
            pass


def unique_attachment_name(document_id, source, used_names):
    source = Path(source)
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", document_id).strip("._")
    if not stem:
        stem = source.stem or "document"
    suffix = source.suffix
    candidate = f"{stem}{suffix}"
    index = 2
    while candidate.lower() in used_names:
        candidate = f"{stem}_{index}{suffix}"
        index += 1
    used_names.add(candidate.lower())
    return candidate


def open_path(path):
    path = Path(path)
    if sys.platform.startswith("win"):
        os.startfile(path)  # noqa: S606 - opening a user-visible folder is intended.
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


def open_folder(path):
    open_path(path)
