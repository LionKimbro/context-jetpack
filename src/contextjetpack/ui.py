"""Tk adapter: collects drafts, posts events, and projects worker results."""

import copy
import queue
import sys
import tkinter as tk
from tkinter import font, messagebox, ttk

from . import core
from .defaults import DOCUMENTS, GROUPS, new_data


# Tk-only state and widget collections. The worker never reads these containers.
g = {
    "root": None, "window": None, "worker": None, "draft": None,
    "saved": None, "store": None, "busy": True, "projecting": False,
    "closing": False, "change-after": None, "exit-code": 0,
    "chooser": None, "chooser-sort": [], "poll-after": None,
}
widgets = {}
document_widgets = {}
catalog = {}
action_buttons = []
form_inputs = []
DESIGNATION_LABELS = {"required": "Read now", "recommended": "When relevant"}


def run(project, configured_registry=""):
    g.update({"draft": new_data(), "saved": None, "store": None,
              "busy": True, "closing": False, "projecting": False, "exit-code": 0,
              "change-after": None, "chooser": None})
    widgets.clear()
    document_widgets.clear()
    catalog.clear()
    action_buttons.clear()
    form_inputs.clear()
    root = tk.Tk()
    root.withdraw()
    window = tk.Toplevel(root)
    window.title("Context Jetpack")
    window.geometry("1180x900")
    g["root"], g["window"] = root, window
    build_window()
    g["worker"] = core.start_worker({"project": str(project), "registry": configured_registry})
    g["poll-after"] = root.after(40, handle_worker_results_on_tk_thread)
    try:
        root.mainloop()
    finally:
        if g["worker"].is_alive() and not g["closing"]:
            core.requests.put({"type": "CLOSE"})
        g["worker"].join()
    return g["exit-code"]


def make_action(parent, text, event):
    button = ttk.Button(parent, text=text, command=lambda: handle_when_action_is_clicked(event))
    action_buttons.append(button)
    return button


def build_window():
    window = g["window"]
    outer = ttk.Frame(window, padding=12)
    outer.pack(fill="both", expand=True)
    outer.columnconfigure(0, weight=1)
    outer.rowconfigure(6, weight=1)

    profiles = ttk.Frame(outer)
    profiles.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
    for label, event in (
        ("Load Global Profile", {"type": "LIST", "store": "global"}),
        ("Load Project Profile", {"type": "LIST", "store": "project"}),
        ("New Profile", {"type": "NEW"}),
        ("Save Global Profile", {"type": "SAVE", "store": "global"}),
        ("Save Project Profile", {"type": "SAVE", "store": "project"}),
    ):
        make_action(profiles, label, event).pack(side="left", padx=(0, 6))

    title_font = font.nametofont("TkDefaultFont").copy()
    title_font.configure(size=18)
    widgets["title-font"] = title_font
    for row, key, label in ((1, "title", "Title"), (2, "hook", "Hook")):
        frame = ttk.Frame(outer)
        frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        ttk.Label(frame, text=label, width=6).pack(side="left")
        variable = tk.StringVar(value=g["draft"][key])
        entry = ttk.Entry(frame, textvariable=variable, width=48 if key == "title" else 100)
        if key == "title":
            entry.configure(font=title_font)
        entry.pack(side="left", fill="x", expand=key == "hook")
        variable.trace_add("write", handle_when_form_field_changes)
        widgets[key] = variable
        form_inputs.append(entry)

    widgets["profile-status"] = tk.StringVar(value="Starting…")
    ttk.Label(outer, textvariable=widgets["profile-status"]).grid(row=3, column=0, sticky="w")
    ttk.Label(outer, text="What are we making?").grid(row=4, column=0, sticky="w", pady=(6, 0))
    purpose = tk.Text(outer, height=3, wrap="word")
    purpose.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(4, 10))
    purpose.bind("<<Modified>>", handle_when_purpose_text_changes)
    widgets["purpose"] = purpose
    form_inputs.append(purpose)

    canvas = tk.Canvas(outer, highlightthickness=0)
    scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.grid(row=6, column=0, sticky="nsew")
    scrollbar.grid(row=6, column=1, sticky="ns")
    documents = ttk.Frame(canvas)
    canvas_id = canvas.create_window((0, 0), window=documents, anchor="nw")
    documents.columnconfigure(0, weight=1)
    documents.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda event: canvas.itemconfigure(canvas_id, width=event.width))
    window.bind("<MouseWheel>", lambda event: canvas.yview_scroll(int(-event.delta / 120), "units"))
    for row, group in enumerate(GROUPS):
        frame = ttk.LabelFrame(documents, text=group, padding=8)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        frame.columnconfigure(2, weight=1)
        for col, label in enumerate(("Use", "When", "Document and reason")):
            ttk.Label(frame, text=label).grid(row=0, column=col, sticky="w", padx=4)
        for index, definition in enumerate((d for d in DOCUMENTS if d["group"] == group), 1):
            add_document_row(frame, (index, definition))

    widgets["totals"] = tk.StringVar(value="Estimating reference tokens…")
    ttk.Label(outer, textvariable=widgets["totals"]).grid(row=7, column=0, sticky="w", pady=(8, 0))
    controls = ttk.Frame(outer)
    controls.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(10, 0))
    for key, label in (("encourage-questions", "Encourage questions"), ("request-ack", "Request ack")):
        var = tk.BooleanVar(value=g["draft"]["options"][key])
        widgets[key] = var
        var.trace_add("write", handle_when_form_field_changes)
        button = ttk.Checkbutton(controls, text=label, variable=var)
        button.pack(side="left", padx=(0, 10))
        form_inputs.append(button)
    make_action(controls, "Compile Message for Chat", {"type": "COMPILE", "chat": True}).pack(side="right")
    make_action(controls, "Compile Message for Agentic AI", {"type": "COMPILE"}).pack(side="right")
    tools = ttk.Frame(outer)
    tools.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(8, 0))
    make_action(tools, "Librarian", {"type": "LIBRARIAN"}).pack(side="left")
    make_action(tools, "Refresh References", {"type": "REFRESH"}).pack(side="left", padx=6)
    widgets["status"] = tk.StringVar(value="Opening project…")
    widgets["status-label"] = ttk.Label(outer, textvariable=widgets["status"], wraplength=1100)
    widgets["status-label"].grid(row=10, column=0, columnspan=2, sticky="ew", pady=(8, 0))
    window.protocol("WM_DELETE_WINDOW", handle_when_main_window_closes)
    project_busy_state()


def add_document_row(parent, row_definition):
    row, definition = row_definition
    key = definition["key"]
    current = g["draft"]["documents"][key]
    record = {name: (tk.BooleanVar(value=value) if name == "selected" else tk.StringVar(value=value))
              for name, value in current.items()}
    checkbox = ttk.Checkbutton(parent, variable=record["selected"])
    checkbox.grid(row=row, column=0, sticky="n", padx=4, pady=8)
    record["designation-label"] = tk.StringVar(value=DESIGNATION_LABELS[current["designation"]])
    designation = ttk.Button(parent, textvariable=record["designation-label"], width=16,
                             command=lambda: handle_when_reading_designation_changes(key))
    designation.grid(row=row, column=1, sticky="n", padx=4, pady=8)
    details = ttk.Frame(parent)
    details.grid(row=row, column=2, sticky="ew", padx=4, pady=8)
    details.columnconfigure(0, weight=1)
    ttk.Label(details, text=definition["label"]).grid(row=0, column=0, sticky="w")
    actions = ttk.Frame(details)
    actions.grid(row=0, column=1, sticky="e", padx=(12, 0))
    record["actions"] = []
    for label, action in (("Open Document", "open"), ("Containing Folder", "containing"), ("Copy Path", "copy")):
        button = make_action(actions, label, {"type": "DOCUMENT", "key": key, "action": action})
        button.pack(side="left", padx=(0, 4))
        record["actions"].append(button)
    record["info"] = ttk.Label(details, text=definition["document-id"], foreground="#666666")
    record["info"].grid(row=1, column=0, columnspan=2, sticky="w")
    reason = ttk.Entry(details, textvariable=record["reason"])
    reason.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(3, 0))
    form_inputs.extend((checkbox, designation, reason))
    for name in ("selected", "designation", "reason"):
        record[name].trace_add("write", handle_when_form_field_changes)
    document_widgets[key] = record


def collect_form():
    data = copy.deepcopy(g["draft"])
    data.update({"title": widgets["title"].get(), "hook": widgets["hook"].get(),
                 "purpose": widgets["purpose"].get("1.0", "end-1c")})
    for key in data["options"]:
        data["options"][key] = widgets[key].get()
    for key, record in document_widgets.items():
        data["documents"][key] = {name: record[name].get() for name in ("selected", "designation", "reason")}
    return data


def project_draft_status():
    dirty = collect_form() != g["saved"]
    widgets["profile-status"].set(f"{(g['store'] or 'New').title()} profile • {'Unsaved changes' if dirty else 'Saved'}")
    g["window"].title(f"Context Jetpack — {widgets['title'].get()}{' *' if dirty else ''}")


def handle_when_form_field_changes(*_):
    if g["projecting"] or g["closing"]:
        return
    for record in document_widgets.values():
        record["designation-label"].set(DESIGNATION_LABELS[record["designation"].get()])
    project_draft_status()
    if g["change-after"] is not None:
        g["root"].after_cancel(g["change-after"])
    g["change-after"] = g["root"].after(180, handle_after_form_edit_settles)


def handle_after_form_edit_settles():
    g["change-after"] = None
    core.requests.put({"type": "FORM_CHANGED", "data": collect_form()})


def handle_when_purpose_text_changes(event):
    if event.widget.edit_modified():
        event.widget.edit_modified(False)
        handle_when_form_field_changes()


def handle_when_reading_designation_changes(key):
    var = document_widgets[key]["designation"]
    var.set("recommended" if var.get() == "required" else "required")


def may_discard_current_draft():
    return collect_form() == g["saved"] or messagebox.askyesno(
        "Unsaved profile", "Discard unsaved changes to this profile?\nUse a Save button first to keep them.",
        parent=g["window"],
    )


def handle_when_action_is_clicked(event):
    if g["busy"] or g["closing"]:
        return
    if event["type"] in {"NEW", "LOAD"} and not may_discard_current_draft():
        return
    if g["change-after"] is not None:
        g["root"].after_cancel(g["change-after"])
        g["change-after"] = None
    request = dict(event)
    request.update({"data": collect_form(), "busy": True})
    g["busy"] = True
    project_busy_state()
    set_status("Working…")
    core.requests.put(request)


def project_busy_state():
    state = "disabled" if g["busy"] or g["closing"] else "normal"
    for widget in form_inputs + action_buttons:
        widget.configure(state=state)
    for key, record in document_widgets.items():
        available = catalog.get(key, {}).get("status") == "ok"
        for button in record["actions"]:
            button.configure(state=state if available else "disabled")


def set_status(message, error=False):
    widgets["status"].set(message)
    widgets["status-label"].configure(foreground="#a00000" if error else "#006000")


def project_profile(result):
    g["projecting"] = True
    g["draft"] = result["data"]
    g["store"] = result["store"]
    g["saved"] = copy.deepcopy(result["data"]) if result.get("saved", True) else None
    for key in ("title", "hook"):
        widgets[key].set(result["data"][key])
    purpose = widgets["purpose"]
    purpose.configure(state="normal")
    purpose.delete("1.0", "end")
    purpose.insert("1.0", result["data"]["purpose"])
    purpose.edit_modified(False)
    for key, value in result["data"]["options"].items():
        widgets[key].set(value)
    for key, record in document_widgets.items():
        for name in ("selected", "designation", "reason"):
            record[name].set(result["data"]["documents"][key][name])
        record["designation-label"].set(DESIGNATION_LABELS[record["designation"].get()])
    g["projecting"] = False
    project_draft_status()
    set_status(result["message"])
    if g["chooser"] is not None:
        g["chooser"].destroy()
        g["chooser"] = None


def show_profile_chooser(result):
    if g["chooser"] is not None:
        g["chooser"].destroy()
    window = tk.Toplevel(g["window"])
    g["chooser"] = window
    window.title(f"Load {result['store'].title()} Profile")
    window.geometry("760x420")
    frame = ttk.Frame(window, padding=12)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text=f"{result['store'].title()} profiles", font=widgets["title-font"]).pack(anchor="w")
    tree = ttk.Treeview(frame, columns=("title", "hook"), show="headings", selectmode="browse")
    tree.heading("title", text="Title")
    tree.heading("hook", text="Hook")
    tree.column("title", width=220)
    tree.column("hook", width=460)
    widgets["chooser-tree"] = tree
    g["chooser-sort"].clear()
    for column in ("title", "hook"):
        tree.heading(column, command=lambda name=column: handle_when_profile_column_is_clicked(name))
    tree.pack(fill="both", expand=True, pady=10)
    for item in result["items"]:
        tree.insert("", "end", iid=item["id"], values=(item["title"], item["hook"]))
    text = "Select a profile, then click Load Profile." if result["items"] else "No profiles saved in this store yet."
    if result["errors"]:
        text += "\nUnreadable profiles:\n" + "\n".join(result["errors"])
    ttk.Label(frame, text=text, wraplength=720).pack(anchor="w")

    def handle_when_selected_profile_is_loaded():
        selection = tree.selection()
        if selection:
            handle_when_action_is_clicked({"type": "LOAD", "store": result["store"], "id": selection[0]})

    ttk.Button(frame, text="Load Profile", command=handle_when_selected_profile_is_loaded).pack(anchor="e", pady=(10, 0))
    window.protocol("WM_DELETE_WINDOW", handle_when_profile_chooser_closes)
    window.transient(g["window"])


def handle_when_profile_chooser_closes():
    g["chooser"].destroy()
    g["chooser"] = None


def handle_when_profile_column_is_clicked(column):
    order = g["chooser-sort"]
    ascending = not order[0][1] if order and order[0][0] == column else True
    order[:] = [(name, direction) for name, direction in order if name != column]
    order.insert(0, (column, ascending))
    tree = widgets["chooser-tree"]
    items = list(tree.get_children())
    for name, direction in reversed(order):
        items.sort(key=lambda item: tree.set(item, name).casefold(), reverse=not direction)
    for index, item in enumerate(items):
        tree.move(item, "", index)


def handle_worker_results_on_tk_thread():
    for _ in range(100):
        try:
            result = core.results.get_nowait()
        except queue.Empty:
            break
        kind = result["type"]
        if kind == "PROFILE":
            project_profile(result)
            g["busy"] = False
        elif kind == "SAVED":
            g["saved"] = result["data"]
            g["store"] = result["store"]
            project_draft_status()
            set_status(f"Saved {result['store']} profile: {result['path']}")
        elif kind == "CATALOG":
            catalog.clear()
            catalog.update(result["documents"])
            for definition in DOCUMENTS:
                info = catalog.get(definition["key"], {})
                text = definition["document-id"]
                if info.get("status") in {"missing", "no-id"}:
                    text += " — I can't find this. " + info.get("error", "")
                document_widgets[definition["key"]]["info"].configure(
                    text=text, foreground="#a00000" if info.get("status") == "missing" else "#666666"
                )
        elif kind == "MEASURED":
            totals = result["totals"]
            widgets["totals"].set(
                f"Estimated tokens — Read now: ~{totals['required']:,}  ·  "
                f"Read now + when-relevant: ~{sum(totals.values()):,}"
                + (f"  ({result['unknown']} could not be measured)" if result["unknown"] else "")
            )
        elif kind == "PROFILES":
            show_profile_chooser(result)
            set_status(f"Choose a {result['store']} profile.")
        elif kind == "CLIPBOARD":
            g["root"].clipboard_clear()
            g["root"].clipboard_append(result["text"])
            set_status(result["message"])
        elif kind == "STATUS":
            set_status(result["message"])
        elif kind == "ERROR":
            set_status(result["message"], True)
            if result.get("fatal"):
                g["exit-code"] = 1
                g["closing"] = True
                print(result["message"], file=sys.stderr)
                messagebox.showerror("Context Jetpack", result["message"], parent=g["window"])
                g["root"].destroy()
                return
        elif kind == "DONE":
            g["busy"] = False
        elif kind == "CLOSED":
            g["closing"] = True
            g["root"].destroy()
            return
        project_busy_state()
    g["poll-after"] = g["root"].after(40, handle_worker_results_on_tk_thread)


def handle_when_main_window_closes():
    if g["closing"]:
        return
    if g["busy"]:
        set_status("Please wait for the current operation to finish before closing.")
        return
    if not may_discard_current_draft():
        return
    if g["change-after"] is not None:
        g["root"].after_cancel(g["change-after"])
        g["change-after"] = None
    g["closing"] = True
    project_busy_state()
    core.requests.put({"type": "CLOSE"})
