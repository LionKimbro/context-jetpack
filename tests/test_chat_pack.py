from contextjetpack.chat_pack import cleanup_chat_folders, stage_read_now_files
from contextjetpack.defaults import new_data


def test_stage_read_now_files_copies_only_required_selected_documents(tmp_path):
    required = tmp_path / "required.txt"
    recommended = tmp_path / "recommended.txt"
    required.write_text("required", encoding="utf-8")
    recommended.write_text("recommended", encoding="utf-8")

    data = new_data()
    for document in data["documents"].values():
        document["selected"] = False
    data["documents"]["programming-guidelines"]["selected"] = True
    data["documents"]["programming-guidelines"]["designation"] = "required"
    data["documents"]["softspec"]["selected"] = True
    data["documents"]["softspec"]["designation"] = "recommended"

    registry = {
        "lionsphilosophyofprogramming.2025.simplified": {
            "title": "Programming",
            "location": [{"path": str(required)}],
        },
        "softspec.spec.v2": {
            "title": "SoftSpec",
            "location": [{"path": str(recommended)}],
        },
    }

    folder, copied = stage_read_now_files(data, registry, tmp_path)

    names = sorted(path.name for path in folder.iterdir())
    assert len(copied) == 1
    assert names == ["lionsphilosophyofprogramming.2025.simplified.txt"]
    assert (folder / names[0]).read_text(encoding="utf-8") == "required"


def test_cleanup_chat_folders_deletes_only_chat_temp_folders(tmp_path):
    chat_a = tmp_path / "context-jetpack-chat-a"
    chat_b = tmp_path / "context-jetpack-chat-b"
    other = tmp_path / "ordinary-folder"
    file_with_prefix = tmp_path / "context-jetpack-chat-file.txt"
    chat_a.mkdir()
    chat_b.mkdir()
    other.mkdir()
    file_with_prefix.write_text("not a folder", encoding="utf-8")

    cleanup_chat_folders(tmp_path)

    assert not chat_a.exists()
    assert not chat_b.exists()
    assert other.exists()
    assert file_with_prefix.exists()
