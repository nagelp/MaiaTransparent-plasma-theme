#!/usr/bin/env python3

"""
Run this script in order to replace the original cyan-ish color the theme uses
(e.g. for highlighting the currently active application in the task bar) to the
currently set system accent color (as defined in KDE Plasma settings).

There is probably a much nicer way to do this, but this LLM-generated quick-and-
dirty script should work for most cases.
"""

import os
import gzip
import io
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
SVGZ_DIRS = [os.path.join(ROOT, "widgets"), os.path.join(ROOT, "icons"), os.path.join(ROOT, "dialogs")]

CYANISH = {
    "#3daee9",
    "#3DAEE9",
    "#3DAEE6",
    "#3498db",
    "#2a8dfc",
    "#31a7f2",
    "#38c2e9",
    "#43ace8",
    "#1489ff",
    "#00ffff",
    "#06c8a8",
    "#21a8a0",
    "#1abc9c",
    "#16a085",
    "#29d7f5",
    "#00785d",
}

HEX_RE = re.compile(r"^#([0-9a-fA-F]{6})$")


def detect_accent() -> str:
    import subprocess
    import shutil
    import re

    # Try kreadconfig5/6 from kdeglobals General AccentColor
    for cmd in ("kreadconfig6", "kreadconfig5"):
        if shutil.which(cmd):
            try:
                out = subprocess.check_output(
                    [cmd, "--file", "kdeglobals", "--group", "General", "--key", "AccentColor"], text=True
                ).strip()
                if out:
                    if out.startswith("#") and re.match(r"^#([0-9a-fA-F]{6})$", out):
                        return out.lower()
                    if "," in out:
                        r, g, b = [int(p) for p in out.split(",")]
                        return f"#{r:02x}{g:02x}{b:02x}"
            except Exception:
                pass
    # Fallback: Selection BackgroundNormal from kdeglobals
    for cmd in ("kreadconfig6", "kreadconfig5"):
        if shutil.which(cmd):
            try:
                out = subprocess.check_output(
                    [cmd, "--file", "kdeglobals", "--group", "Colors:Selection", "--key", "BackgroundNormal"], text=True
                ).strip()
                if out and "," in out:
                    r, g, b = [int(p) for p in out.split(",")]
                    return f"#{r:02x}{g:02x}{b:02x}"
            except Exception:
                pass
    raise RuntimeError("Could not detect accent color via kdeglobals; please set an AccentColor")


def process_file(path: str, accent: str):
    with gzip.open(path, "rb") as g:
        data = g.read()
    text = data.decode("utf-8", errors="ignore")
    new = text
    # Replace any known cyan-ish colors
    for c in CYANISH:
        new = new.replace(c, accent)
    # Also replace any rgb(...) matching accent-like slots if they exist (rare)
    # Replace pagecolor or color attributes if they were set to previous accent variants
    # Ensure accent is lowercase hex
    m = HEX_RE.match(accent)
    if not m:
        raise ValueError(f"Accent must be hex like #rrggbb, got {accent}")
    if new != text:
        buf = io.BytesIO()
        with gzip.GzipFile(filename="", mode="wb", fileobj=buf) as gz:
            gz.write(new.encode("utf-8"))
        with open(path, "wb") as f:
            f.write(buf.getvalue())
        return True
    return False


def main():
    accent = detect_accent().lower()
    changed = 0
    for d in SVGZ_DIRS:
        if not os.path.isdir(d):
            continue
        for root, _, files in os.walk(d):
            for name in files:
                if name.endswith(".svgz"):
                    p = os.path.join(root, name)
                    print(p)
                    if process_file(p, accent):
                        changed += 1
    print(f"Accent: {accent} | Files updated: {changed}")


if __name__ == "__main__":
    main()
