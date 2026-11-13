# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import hashlib
import json
import os
import re
import sys
import time
import urllib.request
from urllib.parse import urlparse

from . import __version__


GITHUB_REPO = "malek-mzali01/LoukaKeyPulse"
API_URL = "https://api.github.com/repos/%s/releases/latest"
ASSET_NAME = "LoukaKeyPulse.exe"
CHECKSUM_NAME = ASSET_NAME + ".sha256"
TRUSTED_HOSTS = (
    "github.com",
    "api.github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com"
)
TIMEOUT = 15
USER_AGENT = "LoukaKeyPulse-Updater/" + __version__


def parse_version(text):
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", str(text))
    return tuple(int(x) for x in m.groups()) if m else None


def exe_path():
    return sys.executable


def can_install():
    return bool(getattr(sys, "frozen", False)) and os.name == "nt"


def _trusted(url):
    p = urlparse(url)
    host = (p.hostname or "").lower()

    return p.scheme == "https" and any(
        host == h or host.endswith("." + h) for h in TRUSTED_HOSTS
    )


def _open(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json"
    })
    resp = urllib.request.urlopen(req, timeout=TIMEOUT)

    if not _trusted(resp.geturl()):
        resp.close()
        raise ValueError("untrusted download host")

    return resp


def check():
    with _open(API_URL % GITHUB_REPO) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    tag = str(data.get("tag_name", ""))
    latest = parse_version(tag)
    current = parse_version(__version__)

    if latest is None or current is None or latest <= current:
        return None

    assets = {
        a.get("name"): a.get("browser_download_url")
        for a in data.get("assets", [])
    }
    page = data.get("html_url") or ""

    if not _trusted(page):
        page = "https://github.com/%s/releases" % GITHUB_REPO

    return {
        "tag": tag,
        "version": ".".join(str(x) for x in latest),
        "name": data.get("name") or tag,
        "notes": data.get("body") or "",
        "page": page,
        "exe": assets.get(ASSET_NAME),
        "sha": assets.get(CHECKSUM_NAME)
    }


def plain_notes(text):
    out = []

    for line in str(text).replace("\r", "").split("\n"):
        line = re.sub(r"^\s{0,3}#{1,6}\s*", "", line)
        line = re.sub(r"^(\s*)[-*]\s+", "\\1\u2022 ", line)
        line = line.replace("**", "").replace("__", "").replace("`", "")
        out.append(line.rstrip())

    return "\n".join(out).strip()


def _expected_hash(url):
    with _open(url) as resp:
        text = resp.read(4096).decode("utf-8", "replace")

    m = re.search(r"\b[0-9a-fA-F]{64}\b", text)

    if not m:
        raise ValueError("checksum file is invalid")

    return m.group(0).lower()


def download(info, dest, progress=None, cancel=None):
    if not info.get("exe") or not info.get("sha"):
        raise ValueError("this release has no installable files")

    expected = _expected_hash(info["sha"])
    digest = hashlib.sha256()

    try:
        with _open(info["exe"]) as resp, open(dest, "wb") as f:
            total = int(resp.headers.get("Content-Length") or 0)
            done = 0

            while True:
                if cancel is not None and cancel.is_set():
                    raise InterruptedError("cancelled")

                chunk = resp.read(65536)

                if not chunk:
                    break

                f.write(chunk)
                digest.update(chunk)
                done += len(chunk)

                if progress and total:
                    progress(min(1.0, done / total))

        if digest.hexdigest().lower() != expected:
            raise ValueError("checksum mismatch, download discarded")

        with open(dest, "rb") as f:
            if f.read(2) != b"MZ":
                raise ValueError("downloaded file is not an executable")

    except BaseException:
        try:
            os.remove(dest)
        except OSError:
            pass

        raise


def apply(new_path):
    exe = exe_path()
    old = exe + ".old"

    if os.path.exists(old):
        os.remove(old)

    os.replace(exe, old)

    try:
        os.replace(new_path, exe)
    except Exception:
        os.replace(old, exe)
        raise


def relaunch():
    for key in [k for k in os.environ if k.startswith("_PYI") or k == "_MEIPASS2"]:
        os.environ.pop(key, None)

    os.environ["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    os.startfile(exe_path())


def cleanup_old():
    if not can_install():
        return

    exe = exe_path()

    try:
        os.remove(exe + ".new")
    except OSError:
        pass

    old = exe + ".old"

    for _ in range(30):
        if not os.path.exists(old):
            return

        try:
            os.remove(old)
            return
        except OSError:
            time.sleep(1)
