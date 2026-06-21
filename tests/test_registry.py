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
