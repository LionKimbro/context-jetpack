# Context Jetpack implementation

Current architecture, updated 2026-10-16. This is maintained documentation,
not a historical specification.

`cli.main()` captures the launch directory and optional `--registry` override.
There is no lionscliapp dependency. `ui.run()` owns one hidden Tk root, the
main Toplevel, and the worker thread's lifetime. The worker validates that
the launch directory contains `db/`; missing `db/` is a fatal startup error
and creates no data directories.

`ui.py` is the interactive adapter. It owns widgets, editable draft projection,
unsaved-change indication, confirmation dialogs, the profile chooser, and the
clipboard. Callbacks post plain dictionaries to `core.requests`. Text edits
are coalesced by a short Tk timer; explicit actions capture the latest draft
immediately. Worker operations disable form editing until completion, so a
late load or save cannot overwrite a newer edit. No filesystem operations,
registry reads, token measurements, or application subprocess launches run
on the Tk thread.

`core.py` is a single worker machine. Only that thread reads/writes its `g`
bundle. `reduce_event()` establishes semantic state and returns effect
requests. `route_effect()` performs file access and launches external tools;
those effects execute serially after each event. Results are copied into
`core.results`; a Tk `after()` callback drains them every 40 ms. No live Tk
objects cross the queues. A failed operation reports an error and leaves
the worker available for another request; failed startup stops the worker.
Close queues shutdown, cleans only this session's chat staging directories,
and waits for a CLOSED response before destroying the Tk runtime.

`profiles.py` resolves project and global stores, validates and lists profiles,
and imports legacy data. Project storage is `db/context-jetpack/`; global
storage is `<Machine Root db-root-2026>/context-jetpack/`. Each store contains
`profiles/<profile-id>.json`. Profiles use version 1, with title, hook,
purpose, options, and document selections keyed by Librarian IDs. Empty-ID
catalog placeholders retain their catalog key. Unknown document references
are preserved for forward compatibility. Renaming a profile does not change
its file identity. First saving a profile to another store creates a separate
copy; further saves in that editing session update each store's copy.

On startup, the project `profiles/default.json` is loaded when present. If
absent, a legacy `.context-jetpack/data.json` (or its configured
`projpath.data`) is imported once as Default. The original is preserved.
Otherwise the application starts with an unsaved Default draft. Compile and
Close never save profiles. Only the two explicit Save actions persist edits.

`storage.py` provides legacy normalization and atomic JSON replacement.
`defaults.py` remains the fixed grouped document catalog. `registry.py` reads
the machine-local Librarian registry, resolves relative paths against the
registry directory, and prefers an existing registered filesystem location.
`compiler.py` builds the launch message. `chat_pack.py` stages required
documents for chat attachments and opens files/folders through the OS.

The Librarian button launches the installed `librarian2._entry` in the same
Python environment, passing the active registry. It does not implement
Librarian single-instance behavior or FileTalk location reporting. After
editing the registry, use Refresh References.

Tests cover storage, compilation, profile migration and identity, registry
resolution, worker queue behavior, and GUI projection with tkintertester.
`db/ideas.json` records the deferred location-reporting and richer browsing
ideas using the PyDeck26 ideas format.
