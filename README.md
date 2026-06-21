# context-jetpack

Context Jetpack is a small persistent Tkinter form for composing launch
messages for Codex.

Select the reference documents a project needs, mark each one required or
recommended, explain why it matters, and click **Compile Message to Codex**.
The application resolves every document through a Librarian2 registry and
copies the completed message to the clipboard.

## Registry resolution

Set an explicit registry when needed:

```text
context-jetpack set registry.path C:\path\to\registry.json
```

When `registry.path` is empty, Context Jetpack uses:

```python
machineroot.get("coding-librarian")
```

## Development

```text
pip install -e .
context-jetpack
pytest
```
