# Context Jetpack

Context Jetpack is a Tkinter form for composing reference-document launch
messages. Select documents, choose **Read now** or **When relevant**, explain
why they matter, and compile a message to the clipboard. Chat compilation
also opens a temporary folder containing copies of the read-now documents.

## Install and run

Requires Python 3.11 or later with Tkinter.

```text
pip install -e .
cd path/to/your/project
context-jetpack
```

Run from the project's root directory. **That directory must already contain
`db/`.** Otherwise Jetpack stops and asks you to run it in your project folder.
It does not search parent directories or create `db/` automatically.

## Profiles

Edit the large **Title**, the wider **Hook** beneath it, the project purpose,
and the grouped reference selections. Use **New Profile** to start another
profile. The hook describes the profile in the chooser; it is not added to
the compiled message.

- **Save Project Profile** stores the profile under
  `<project>/db/context-jetpack/profiles/`.
- **Save Global Profile** stores it under
  `<db-root-2026>/context-jetpack/profiles/`, where `db-root-2026` is resolved
  through Machine Root. If the key is missing, the operation explains the
  problem; project profiles remain available.
- **Load Project Profile** and **Load Global Profile** open separate chooser
  windows. Select a title/hook, then click **Load Profile**.

Saving updates the profile even when its title changes. Saving to the other
store makes a copy. **Compile and Close do not save.** Unsaved changes are
marked, and replacing or closing a draft asks before discarding them.

On first launch, the old `.context-jetpack/data.json` form is imported as
the project's **Default** profile; the original file is preserved. Legacy
`projpath.data` configuration is honored during import. Subsequent launches
open the project's Default profile when it exists; use a chooser for others.

## Reference locations and Librarian

Profiles store stable Librarian document IDs rather than absolute document
paths. The current machine supplies the registry through:

```python
machineroot.get("coding-librarian")
```

To override it for a launch:

```text
context-jetpack --registry C:\path\to\registry.json
```

Relative document paths resolve against the registry's directory. If multiple
filesystem locations are registered, Jetpack prefers one that exists.
Missing references are marked and retain their selections; deselect them or
repair the registry before compiling.

**Librarian** opens the installed Librarian2 editor with the active registry.
Install `lions-librarian` into the same Python environment to enable this
action. Use **Refresh References** after editing the registry. Single-instance
summoning remains future work in Librarian2.

## Development

```text
pip install -e ".[test]"
python -m pytest
```

On Windows, `run-tests.bat` runs the same suite. GUI tests require a desktop
and use tkintertester. Tk owns interaction and clipboard operations; the
worker owns reducers, file access, registry resolution, token estimates,
compilation, and external tool launches. See
[implementation notes](docs/code/architecture.md) and
[deferred ideas](db/ideas.json).
