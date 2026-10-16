import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Compose context messages. Run from a project root containing db/."
    )
    parser.add_argument("--registry", default="", help="Override the Librarian registry path.")
    args = parser.parse_args()
    from .ui import run

    return run(Path.cwd(), args.registry)


if __name__ == "__main__":
    raise SystemExit(main())
