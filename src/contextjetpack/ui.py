import tkinter as tk
from tkinter import messagebox, ttk

from .compiler import compile_message
from .defaults import DOCUMENTS, GROUPS
from .registry import load_registry, resolve_document, resolve_registry_path
from .storage import load_data, save_data


def run(data_path, configured_registry_path):
    root = tk.Tk()
    root.withdraw()

    try:
        data = load_data(data_path)
    except Exception as exc:
        detail = str(exc) or exc.__class__.__name__
        messagebox.showerror(
            "Context Jetpack",
            f"Could not open Context Jetpack:\n\n{detail}",
            parent=root,
        )
        root.destroy()
        return

    window = tk.Toplevel(root)
    window.title("Context Jetpack")
    window.geometry("1080x820")

    state = {
        "data-path": data_path,
        "registry-path": configured_registry_path,
        "data": data,
        "document-widgets": {},
        "measure-cache": {},
    }

    try:
        state["registry-entries"] = load_registry(
            resolve_registry_path(configured_registry_path)
        )
    except Exception:
        state["registry-entries"] = None
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
    document_frame.columnconfigure(0, weight=1)

    add_document_groups(document_frame, state)

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

    totals = tk.StringVar(value="")
    ttk.Label(outer, textvariable=totals, anchor="w").grid(
        row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0)
    )
    state["totals-var"] = totals

    controls = ttk.Frame(outer)
    controls.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0))

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
        row=5, column=0, columnspan=2, sticky="ew", pady=(8, 0)
    )
    state["status-var"] = status

    refresh_totals(state)

    def close_window():
        save_current_form(state)
        root.destroy()

    window.protocol("WM_DELETE_WINDOW", close_window)


def add_document_groups(parent, state):
    grouped = group_documents()
    row = 0
    for group in GROUPS:
        definitions = grouped[group]
        frame = ttk.LabelFrame(parent, text=group, padding=8)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        frame.columnconfigure(2, weight=1)

        ttk.Label(frame, text="Use").grid(row=0, column=0, sticky="w", padx=4)
        ttk.Label(frame, text="When").grid(row=0, column=1, sticky="w", padx=4)
        ttk.Label(frame, text="Document and reason").grid(row=0, column=2, sticky="w", padx=4)

        for item_row, definition in enumerate(definitions, start=1):
            add_document_row(frame, item_row, definition, state)
        row += 1


def group_documents():
    grouped = {group: [] for group in GROUPS}
    for definition in DOCUMENTS:
        grouped[definition["group"]].append(definition)
    return grouped


def document_status(state, definition):
    """Classify a document for display: 'no-id', 'missing', 'unverified', or 'ok'."""
    document_id = definition["document-id"]
    if not document_id:
        return "no-id"
    entries = state.get("registry-entries")
    if not entries:
        return "unverified"
    try:
        resolve_document(entries, document_id)
        return "ok"
    except ValueError:
        return "missing"


def add_document_row(parent, row, definition, state):
    current = state["data"]["documents"][definition["key"]]
    status_kind = document_status(state, definition)
    available = status_kind in ("ok", "unverified")

    selected = tk.BooleanVar(value=current["selected"])
    designation = tk.StringVar(value=current["designation"])
    designation_label = tk.StringVar(value=designation_text(current["designation"]))
    reason = tk.StringVar(value=current["reason"])

    if status_kind == "missing":
        selected.set(False)

    selected.trace_add("write", lambda *_: refresh_totals(state))
    designation.trace_add("write", lambda *_: designation_label.set(designation_text(designation.get())))
    designation.trace_add("write", lambda *_: refresh_totals(state))

    checkbox = ttk.Checkbutton(parent, variable=selected)
    checkbox.grid(row=row, column=0, sticky="n", padx=4, pady=8)
    if not available:
        checkbox.configure(state="disabled")

    designation_button = ttk.Button(
        parent,
        textvariable=designation_label,
        command=lambda: toggle_designation(designation),
        width=16,
    )
    designation_button.grid(row=row, column=1, sticky="n", padx=4, pady=8)
    if not available:
        designation_button.configure(state="disabled")

    details = ttk.Frame(parent)
    details.grid(row=row, column=2, sticky="ew", padx=4, pady=8)
    details.columnconfigure(0, weight=1)

    if status_kind == "no-id":
        id_text, id_color = "unresolved: no Librarian document ID", "#666666"
    elif status_kind == "missing":
        id_text, id_color = f"{definition['document-id']} — I can't find this.", "#b00020"
    else:
        id_text, id_color = definition["document-id"], "#666666"
    ttk.Label(details, text=definition["label"]).grid(row=0, column=0, sticky="w")
    ttk.Label(details, text=id_text, foreground=id_color).grid(row=1, column=0, sticky="w")
    ttk.Entry(details, textvariable=reason).grid(row=2, column=0, sticky="ew", pady=(3, 0))

    state["document-widgets"][definition["key"]] = {
        "selected": selected,
        "designation": designation,
        "reason": reason,
    }


DESIGNATION_LABELS = {"required": "Read now", "recommended": "When relevant"}


def designation_text(value):
    return DESIGNATION_LABELS.get(value, value)


def toggle_designation(variable):
    if variable.get() == "required":
        variable.set("recommended")
    else:
        variable.set("required")


def estimate_tokens(text):
    return (len(text) + 3) // 4


def measure_document_tokens(state, path):
    cache = state["measure-cache"]
    key = str(path)
    if key not in cache:
        try:
            cache[key] = estimate_tokens(path.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            cache[key] = None
    return cache[key]


def compute_token_totals(state):
    entries = state.get("registry-entries")
    if not entries:
        return None
    data = collect_form(state)
    totals = {"required": 0, "recommended": 0}
    unknown = 0
    for definition in DOCUMENTS:
        status = data["documents"][definition["key"]]
        if not status["selected"]:
            continue
        document_id = definition["document-id"]
        if not document_id:
            continue
        try:
            resolved = resolve_document(entries, document_id)
        except ValueError:
            unknown += 1
            continue
        tokens = measure_document_tokens(state, resolved["path"])
        if tokens is None:
            unknown += 1
            continue
        totals[status["designation"]] += tokens
    return totals, unknown


def refresh_totals(state):
    var = state.get("totals-var")
    if var is None:
        return
    result = compute_token_totals(state)
    if result is None:
        var.set("Token estimate unavailable (registry not loaded).")
        return
    totals, unknown = result
    required = totals["required"]
    both = required + totals["recommended"]
    text = (
        f"Estimated tokens — Read now: ~{required:,}  ·  "
        f"Read now + when-relevant: ~{both:,}"
    )
    if unknown:
        text += f"  ({unknown} could not be measured)"
    var.set(text)


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
        state["registry-entries"] = entries
        window.clipboard_clear()
        window.clipboard_append(message)
        window.update()
        refresh_totals(state)
    except Exception as exc:
        detail = str(exc) or exc.__class__.__name__
        messagebox.showerror(
            "Context Jetpack", f"Could not compile message:\n\n{detail}", parent=window
        )
        state["status-var"].set(f"Could not compile: {detail}")
        return

    state["status-var"].set(
        f"Message copied to clipboard. Registry: {registry_path}"
    )


def registry_status(configured_path):
    if str(configured_path or "").strip():
        return f"Registry configured explicitly: {configured_path}"
    return 'Registry: Machine Root key "coding-librarian"'
