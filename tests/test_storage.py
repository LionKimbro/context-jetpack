from contextjetpack.defaults import DOCUMENTS, GROUPS
from contextjetpack.storage import load_data, save_data


def test_documents_are_grouped_in_display_order():
    groups = [item["group"] for item in DOCUMENTS]
    assert GROUPS == [
        "GENERAL",
        "WRITING",
        "APPLICATION FRAMEWORK",
        "TKINTER APPS",
        "M1",
        "ARCHITECTURE",
    ]
    assert groups == sorted(groups, key=GROUPS.index)
    assert [item["key"] for item in DOCUMENTS[:3]] == [
        "general-background",
        "project-directory-system",
        "programming-guidelines",
    ]


def test_new_data_uses_document_specific_defaults(tmp_path):
    data = load_data(tmp_path / "missing.json")

    assert data["options"]["encourage-questions"] is False
    assert data["options"]["request-ack"] is True
    assert data["documents"]["general-background"]["selected"] is False
    assert data["documents"]["general-background"]["designation"] == "required"
    assert data["documents"]["project-directory-system"]["selected"] is True
    assert data["documents"]["tkinter-conventions"]["selected"] is False
    assert data["documents"]["tkinter-conventions"]["designation"] == "required"
    assert data["documents"]["tkintertester-reference"]["selected"] is False
    assert data["documents"]["tkintertester-reference"]["designation"] == "required"
    assert data["documents"]["tkintertester-lionscliapp"]["selected"] is False
    assert data["documents"]["tkintertester-lionscliapp"]["designation"] == "required"
    assert data["documents"]["programming-guidelines"]["selected"] is True
    assert data["documents"]["lionscliapp"]["selected"] is False
    assert data["documents"]["json-document-writing"]["designation"] == "recommended"
    assert data["documents"]["softspec"]["selected"] is True
    assert data["documents"]["m1-core"]["designation"] == "required"
    assert data["documents"]["reducer-core-architecture"]["selected"] is False
    assert data["documents"]["reducer-core-architecture"]["designation"] == "required"
    assert data["documents"]["cira"]["selected"] is False
    assert data["documents"]["cira"]["designation"] == "required"


def test_data_round_trip(tmp_path):
    path = tmp_path / "data.json"
    data = load_data(path)
    data["purpose"] = "Remember me"
    data["documents"]["machine-root"]["selected"] = True
    data["documents"]["machine-root"]["designation"] = "required"

    save_data(path, data)
    loaded = load_data(path)

    assert loaded["purpose"] == "Remember me"
    assert loaded["documents"]["machine-root"]["selected"] is True
    assert loaded["documents"]["machine-root"]["designation"] == "required"
