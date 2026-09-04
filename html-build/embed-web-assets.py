#!/usr/bin/env python3
"""Embed mdlayout CSS and its local webfont in a standalone HTML file."""

from __future__ import annotations

import argparse
import base64
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("html", type=Path)
    parser.add_argument("css", type=Path)
    args = parser.parse_args()

    html = args.html.read_text(encoding="utf-8")
    css = args.css.read_text(encoding="utf-8")
    font_path = args.css.parent / "fonts" / "mdlayout-plex-mono-85.ttf"
    font_data = base64.b64encode(font_path.read_bytes()).decode("ascii")
    css = css.replace(
        'url("fonts/mdlayout-plex-mono-85.ttf")',
        f'url("data:font/ttf;base64,{font_data}")',
    )

    link = f'<link rel="stylesheet" href="{args.css.name}" />'
    if link not in html:
        raise RuntimeError(f"stylesheet link not found: {link}")
    html = html.replace(link, f"<style>\n{css}\n</style>", 1)
    args.html.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
