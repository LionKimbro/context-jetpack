import lionscliapp as app

from .ui import run


def cmd_run():
    run(app.ctx["projpath.data"], app.ctx["registry.path"])


def main():
    app.declare_app("context-jetpack", "0.1.0")
    app.describe_app("Compose registry-resolved context messages for Codex.")
    app.declare_projectdir(".context-jetpack")

    app.declare_key("projpath.data", "data.json")
    app.declare_key("registry.path", "")
    app.describe_key("projpath.data", "Persistent Context Jetpack form data.")
    app.describe_key(
        "registry.path",
        'Librarian registry path. Empty uses Machine Root key "coding-librarian".',
    )

    app.declare_cmd("", cmd_run)
    app.declare_cmd("run", cmd_run)
    app.describe_cmd("", "Open Context Jetpack.")
    app.describe_cmd("run", "Open Context Jetpack.")
    app.main()


if __name__ == "__main__":
    main()
