#!/usr/bin/env python3
"""Apply document-order corrections that belong to the HTML presentation."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def matching_div_end(html: str, start: int) -> int:
    token = re.compile(r"<div\b[^>]*>|</div\s*>", re.I)
    depth = 0
    for match in token.finditer(html, start):
        depth += -1 if match.group(0).lower().startswith("</") else 1
        if depth == 0:
            return match.end()
    raise ValueError("unclosed titlepage div")


def convert_embedded_pdfs(html: str, source: Path, output: Path) -> str:
    """Rasterize local single-page PDF figures and replace browser embeds."""
    source_dir = source.resolve().parent
    image_dir = output.resolve().parent / "images"
    converter = shutil.which("magick") or shutil.which("convert")
    renderer = shutil.which("pdftoppm")
    vector_renderer = shutil.which("pdftocairo")

    def replace(match: re.Match[str]) -> str:
        tag, src = match.group(0), match.group(1)
        candidate = (source_dir / src).resolve()
        if source_dir != candidate.parent and source_dir not in candidate.parents:
            return tag
        svg_target = image_dir / (candidate.stem + ".svg")
        webp_target = image_dir / (candidate.stem + ".webp")
        if svg_target.is_file():
            target = svg_target
        elif candidate.is_file() and vector_renderer:
            image_dir.mkdir(parents=True, exist_ok=True)
            subprocess.run([vector_renderer, "-svg", str(candidate),
                            str(svg_target)], check=True)
            target = svg_target
        elif webp_target.is_file():
            target = webp_target
        else:
            if not candidate.is_file() or not converter or not renderer:
                return tag
            image_dir.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory() as temporary:
                prefix = Path(temporary) / candidate.stem
                subprocess.run([renderer, "-f", "1", "-l", "1", "-singlefile",
                                "-png", "-r", "600", str(candidate), str(prefix)],
                               check=True)
                command = [converter, str(prefix) + ".png", "-strip", "-resize",
                           "1100x1100>", "-quality", "95", str(webp_target)]
                subprocess.run(command, check=True)
            target = webp_target
        element_id = re.search(r'\bid="([^"]+)"', tag, re.I)
        id_attr = f' id="{element_id.group(1)}"' if element_id else ""
        style = re.search(r'\bstyle="([^"]+)"', tag, re.I)
        style_attr = f' style="{style.group(1)}"' if style else ""
        classes = re.search(r'\bclass="([^"]+)"', tag, re.I)
        class_attr = f' class="{classes.group(1)}"' if classes else ""
        return (f'<img src="images/{target.name}" alt="image"{class_attr}'
                f'{style_attr}{id_attr} />')

    return re.sub(r'<embed\b[^>]*\bsrc="([^"]+\.pdf)"[^>]*>', replace, html,
                  flags=re.I)


def main() -> None:
    path = Path(sys.argv[1])
    html = path.read_text(encoding="utf-8")
    if len(sys.argv) > 2:
        html = convert_embedded_pdfs(html, Path(sys.argv[2]), path)
    # Some labels live inside deeply nested custom LaTeX environments. Attach
    # their HTML ids directly to the corresponding visual element.
    def set_id_on_occurrence(pattern: str, element_id: str, occurrence: int = 1) -> None:
        nonlocal html
        matches = list(re.finditer(pattern, html, re.I))
        if not matches: return
        match = matches[occurrence-1] if occurrence > 0 and len(matches) >= occurrence else matches[-1]
        tag = match.group(0)
        if ' id=' not in tag:
            tag = re.sub(r'\s*/?>$', f' id="{element_id}" />' if tag.rstrip().endswith('/>') else f' id="{element_id}">', tag)
            html = html[:match.start()] + tag + html[match.end():]

    set_id_on_occurrence(r'<img\b[^>]*src="mdlayout\.png"[^>]*>', 'fig:Layout', 2)
    set_id_on_occurrence(r'<(?:img|embed)\b[^>]*src="(?:images/)?mdlayout-margin-logo\.(?:svg|webp|pdf)"[^>]*>',
                         'fig:margin-logo')
    set_id_on_occurrence(r'<img\b[^>]*src="images/mdlayout-tixi-measuring\.webp"[^>]*>',
                         'fig:mdlayout-tixi-measuring')
    set_id_on_occurrence(r'<img\b[^>]*src="images/mdlayout-tixi-juggling\.webp"[^>]*>',
                         'fig:mdlayout-tixi-juggling', -1)
    headings = []
    for match in re.finditer(
            r'<h([1-3])\s+data-number="([^"]+)"\s+id="([^"]+)"[^>]*>(.*?)</h\1>',
            html, re.S | re.I):
        level, number, target, title = match.groups()
        title = re.sub(
            r'<span\s+class="header-section-number"[^>]*>.*?</span>\s*',
            '', title, flags=re.S | re.I).strip()
        headings.append((level, number, target, title))
    toc = ['<nav class="document-directory toc-directory" aria-label="Contents">',
           '<h2 class="directory-title">Contents</h2>',
           '<ol class="directory-list">']
    for level, number, target, title in headings:
        toc.append(f'<li class="toc-level-{level}"><a href="#{target}">'
                   f'<span class="directory-number">{number}</span>'
                   f'<span class="directory-text">{title}</span></a></li>')
    toc.append('</ol></nav>')
    html = re.sub(
        r'<nav\s+class="document-directory toc-directory"\s+data-md-directory="toc"></nav>',
        lambda _: '\n'.join(toc), html, flags=re.I)
    path.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
