import json

from contextjetpack.registry import load_registry, resolve_document


def test_load_and_resolve_registry(tmp_path):
    path = tmp_path / "registry.json"
    path.write_text(
        json.dumps(
            {
                "registry": {
                    "example": {
                        "title": "Example",
                        "location": [{"path": str(tmp_path / "example.json")}],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    entries = load_registry(path)
    resolved = resolve_document(entries, "example")

    assert resolved["document-id"] == "example"
    assert resolved["title"] == "Example"
    assert resolved["path"] == tmp_path / "example.json"


def test_relative_locations_use_registry_folder_and_existing_alternatives(tmp_path, monkeypatch):
    registry_dir = tmp_path / "library"
    registry_dir.mkdir()
    document = registry_dir / "reference.md"
    document.write_text("Reference", encoding="utf-8")
    registry = registry_dir / "registry.json"
    registry.write_text(json.dumps({"registry": {"example": {
        "location": [{"path": "old-machine/reference.md"}, {"path": "reference.md"}]
    }}}), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    entries = load_registry(registry)
    assert resolve_document(entries, "example")["path"] == document
