import tkinter as tk
from tkinter import messagebox, ttk

from .compiler import compile_message
from .defaults import DOCUMENTS
from .registry import load_registry, resolve_registry_path
from .storage import load_data, save_data


def run(data_path, configured_registry_path):
    root = tk.Tk()
    root.withdraw()
    window = tk.Toplevel(root)
    window.title("Context Jetpack")
    window.geometry("1080x820")

    state = {
        "data-path": data_path,
        "registry-path": configured_registry_path,
        "data": load_data(data_path),
        "document-widgets": {},
    }
    build_window(window, root, state)
    root.mainloop()


def build_window(window, root, state):
    outer = ttk.Frame(window, padding=12)
    outer.pack(fill="both", expand=True)
    outer.columnconfigure(0, weight=1)
    outer.rowconfigure(2, weight=1)

    ttk.Label(outer, text="What are we making?").grid(row=0, column=0, sticky="w")
    purpose = tk.Text(outer, height=3, wrap="word")
    purpose.grid(row=1, column=0, sticky="ew", pady=(4, 10))
    purpose.insert("1.0", state["data"]["purpose"])
    state["purpose-widget"] = purpose

    canvas = tk.Canvas(outer, highlightthickness=0)
    scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.grid(row=2, column=0, sticky="nsew")
    scrollbar.grid(row=2, column=1, sticky="ns")

    document_frame = ttk.Frame(canvas)
    window_id = canvas.create_window((0, 0), window=document_frame, anchor="nw")
    document_frame.columnconfigure(2, weight=1)

    ttk.Label(document_frame, text="Use").grid(row=0, column=0, sticky="w", padx=4)
    ttk.Label(document_frame, text="Reading").grid(row=0, column=1, sticky="w", padx=4)
    ttk.Label(document_frame, text="Document and reason").grid(row=0, column=2, sticky="w", padx=4)

    for row, definition in enumerate(DOCUMENTS, start=1):
        add_document_row(document_frame, row, definition, state)

    document_frame.bind(
        "<Configure>",
        lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
    )
    canvas.bind(
        "<Configure>",
        lambda event: canvas.itemconfigure(window_id, width=event.width),
    )
    canvas.bind_all(
        "<MouseWheel>",
        lambda event: canvas.yview_scroll(int(-event.delta / 120), "units"),
    )

    controls = ttk.Frame(outer)
    controls.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))

    encourage = tk.BooleanVar(value=state["data"]["options"]["encourage-questions"])
    request_ack = tk.BooleanVar(value=state["data"]["options"]["request-ack"])
    ttk.Checkbutton(controls, text="Encourage questions", variable=encourage).pack(side="left")
    ttk.Checkbutton(controls, text="Request ack", variable=request_ack).pack(side="left", padx=(14, 0))
    state["encourage-var"] = encourage
    state["ack-var"] = request_ack

    ttk.Button(
        controls,
        text="Compile Message to Codex",
        command=lambda: compile_to_clipboard(window, state),
    ).pack(side="right")

    status = tk.StringVar(value=registry_status(state["registry-path"]))
    ttk.Label(outer, textvariable=status, anchor="w").grid(
        row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0)
    )
    state["status-var"] = status

    def close_window():
        save_current_form(state)
        root.destroy()

    window.protocol("WM_DELETE_WINDOW", close_window)


def add_document_row(parent, row, definition, state):
    current = state["data"]["documents"][definition["key"]]
    available = bool(definition["document-id"])

    selected = tk.BooleanVar(value=current["selected"])
    designation = tk.StringVar(value=current["designation"])
    reason = tk.StringVar(value=current["reason"])

    checkbox = ttk.Checkbutton(parent, variable=selected)
    checkbox.grid(row=row, column=0, sticky="n", padx=4, pady=8)
    if not available:
        checkbox.configure(state="disabled")

    combo = ttk.Combobox(
        parent,
        textvariable=designation,
        values=("required", "recommended"),
        state="readonly",
        width=13,
    )
    combo.grid(row=row, column=1, sticky="n", padx=4, pady=8)

    details = ttk.Frame(parent)
    details.grid(row=row, column=2, sticky="ew", padx=4, pady=8)
    details.columnconfigure(0, weight=1)

    id_text = definition["document-id"] or "unresolved: no Librarian document ID"
    ttk.Label(details, text=definition["label"]).grid(row=0, column=0, sticky="w")
    ttk.Label(details, text=id_text, foreground="#666666").grid(row=1, column=0, sticky="w")
    ttk.Entry(details, textvariable=reason).grid(row=2, column=0, sticky="ew", pady=(3, 0))

    state["document-widgets"][definition["key"]] = {
        "selected": selected,
        "designation": designation,
        "reason": reason,
    }


def collect_form(state):
    data = state["data"]
    data["purpose"] = state["purpose-widget"].get("1.0", "end-1c")
    data["options"]["encourage-questions"] = state["encourage-var"].get()
    data["options"]["request-ack"] = state["ack-var"].get()
    for key, widgets in state["document-widgets"].items():
        data["documents"][key] = {
            "selected": widgets["selected"].get(),
            "designation": widgets["designation"].get(),
            "reason": widgets["reason"].get(),
        }
    return data


def save_current_form(state):
    save_data(state["data-path"], collect_form(state))


def compile_to_clipboard(window, state):
    try:
        data = collect_form(state)
        registry_path = resolve_registry_path(state["registry-path"])
        entries = load_registry(registry_path)
        message = compile_message(data, entries)
        save_data(state["data-path"], data)
        window.clipboard_clear()
        window.clipboard_append(message)
        window.update()
    except Exception as exc:
        messagebox.showerror("Context Jetpack", str(exc), parent=window)
        state["status-var"].set(f"Could not compile: {exc}")
        return

    state["status-var"].set(
        f"Message copied to clipboard. Registry: {registry_path}"
    )


def registry_status(configured_path):
    if str(configured_path or "").strip():
        return f"Registry configured explicitly: {configured_path}"
    return 'Registry: Machine Root key "coding-librarian"'
