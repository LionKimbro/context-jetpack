import tkinter as tk

from contextjetpack.defaults import DOCUMENTS, new_data
from contextjetpack.ui import build_window


def test_document_rows_include_right_side_action_buttons(tmp_path):
    source = tmp_path / "dictionary.json"
    source.write_text("{}", encoding="utf-8")
    data_path = tmp_path / "data.json"

    root = tk.Tk()
    root.withdraw()
    try:
        window = tk.Toplevel(root)
        state = {
            "data-path": data_path,
            "registry-path": "",
            "data": new_data(),
            "document-widgets": {},
            "measure-cache": {},
            "registry-entries": {
                "lions_dictionary_for_llms": {
                    "title": "Dictionary",
                    "location": [{"path": str(source)}],
                }
            },
        }
        build_window(window, root, state)
        root.update_idletasks()

        buttons = collect_buttons(window)
        labels = [button.cget("text") for button in buttons]

        assert labels.count("Open Document") == len(DOCUMENTS)
        assert labels.count("Containing Folder") == len(DOCUMENTS)
        assert labels.count("Copy Path") == len(DOCUMENTS)
        assert any(
            button.cget("text") == "Open Document"
            and "disabled" not in button.state()
            for button in buttons
        )
        assert any(
            button.cget("text") == "Open Document"
            and "disabled" in button.state()
            for button in buttons
        )
    finally:
        root.destroy()


def collect_buttons(widget):
    buttons = []
    for child in widget.winfo_children():
        if child.winfo_class() == "TButton":
            buttons.append(child)
        buttons.extend(collect_buttons(child))
    return buttons
