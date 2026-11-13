# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: release_notes.py <version or tag> <output file>")

    version = sys.argv[1].lstrip("vV")
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    head = re.search(
        r"^## \[%s\][^\n]*\n" % re.escape(version), text, re.MULTILINE
    )

    if not head:
        sys.exit("no CHANGELOG.md section for %s" % version)

    rest = text[head.end():]
    nxt = re.search(r"^## \[", rest, re.MULTILINE)
    body = (rest[:nxt.start()] if nxt else rest).strip()

    if not body:
        sys.exit("the CHANGELOG.md section for %s is empty" % version)

    pathlib.Path(sys.argv[2]).write_text(body + "\n", encoding="utf-8")
    print("release notes written for %s" % version)


main()
