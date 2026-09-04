#!/usr/bin/env python3
"""Make the generated semantic HTML suitable as Pandoc DOCX input."""

from pathlib import Path
import re
import sys


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: prepare-docx-html.py INPUT.html OUTPUT.html")

    source = Path(sys.argv[1])
    target = Path(sys.argv[2])
    html = source.read_text(encoding="utf-8")

    # Pandoc's DOCX writer cannot use SVG without an external converter.  The
    # HTML build already provides an equivalent raster fallback for this image.
    html = html.replace(
        "images/mdlayout-margin-logo.svg",
        "images/mdlayout-margin-logo.webp",
    )

    # Apple Pages does not reliably display WebP media embedded in DOCX.
    # Keep WebP for the browser build, but create compact, widely supported
    # JPEG copies in the temporary DOCX workspace.  These illustrations are
    # opaque raster images, so PNG would only make the document much larger.
    image_directory = source.parent / "docx-images"
    raster_sources = sorted(
        set(re.findall(r'(?:src=")[^"]*?([^/" ]+\.(?:webp|png))', html))
    )
    if raster_sources:
        image_directory.mkdir(parents=True, exist_ok=True)
    for filename in raster_sources:
        candidates = (
            source.parent / "images" / filename,
            Path(__file__).resolve().parent / "images" / filename,
            Path.cwd() / "upload" / filename,
            Path.cwd() / "images" / filename,
        )
        raster = next((candidate for candidate in candidates if candidate.is_file()), None)
        if raster is None:
            continue
        jpeg_name = Path(filename).with_suffix(".jpg").name
        jpeg = image_directory / jpeg_name
        try:
            from PIL import Image
        except ImportError as error:
            raise SystemExit(
                "DOCX image conversion requires Python Pillow"
            ) from error

        # Decode the complete raster before conversion so truncated input cannot
        # survive as a partially black image in Pages.
        with Image.open(raster) as image:
            image.load()
            if image.mode != "RGB":
                image = image.convert("RGB")
            image.save(
                jpeg,
                format="JPEG",
                quality=90,
                optimize=True,
                progressive=False,
                subsampling="4:4:4",
            )
        html = re.sub(
            rf'(?<=src=")([^" ]*/)?{re.escape(filename)}',
            f'docx-images/{jpeg_name}',
            html,
        )

    # MathJax understands \class, whereas Pandoc's texmath-to-OMML converter
    # does not.  Keep the Unicode operators and discard only the HTML styling.
    html = html.replace(r"\class{md-oiint}{∯}", "∯")
    html = html.replace(r"\class{md-oiiint}{∰}", "∰")

    # Extra alignment columns before manually supplied equation numbers are
    # meaningful to MathJax but produce stray glyphs in Pandoc's OMML output.
    # A horizontal space retains the separation without leaking an alignment
    # marker into Word.
    html = html.replace(r"&amp;&amp;\text{(", r"\qquad\text{(")
    html = html.replace(r"&&\text{(", r"\qquad\text{(")

    # The browser representation of Printout uses one span per physical line
    # so that line numbers, paper bands, and feed holes can be positioned with
    # CSS.  Word ignores that CSS and consequently concatenates all spans.
    # Reduce the browser structure to a genuine preformatted block for DOCX.
    # A short private marker carries fitcolumns into the OOXML postprocessor;
    # it is removed there before the document is delivered.
    def convert_printout(match: re.Match[str]) -> str:
        attributes, body = match.group(1), match.group(2)
        def css_number(name: str, default: str) -> str:
            found = re.search(rf'--{name}\s*:\s*(\d+)', attributes)
            return found.group(1) if found else default

        fitcolumns = css_number('fit-columns', '132')
        paperheight = css_number('paper-height', '999')
        bandlines = css_number('band-lines', '0')
        feedlines = css_number('feed-lines', '0')
        color_match = re.search(r'\bprintout-(green|blue|none)\b', attributes)
        color = color_match.group(1) if color_match else 'none'
        linenumbers = '1' if 'has-line-numbers' in attributes else '0'
        punchholes = '1' if 'has-punchholes' in attributes else '0'
        lines = re.findall(
            r'<span class="printout-text">(.*?)</span>',
            body,
            flags=re.DOTALL,
        )
        # The line contents are already HTML-escaped by the Lua filter. Keep
        # them escaped when inserting them into <code>.
        contents = '\n'.join(lines)
        return (
            '<pre class="printout-docx"><code>'
            'MDPRINTOUT:'
            f'fit={fitcolumns},paper={paperheight},bands={bandlines},feed={feedlines},'
            f'color={color},numbers={linenumbers},holes={punchholes};{contents}'
            '</code></pre>'
        )

    html = re.sub(
        r'<figure\b([^>]*\bclass="[^"]*\bprintout\b[^"]*"[^>]*)>'
        r'<pre><code>(.*?)</code></pre></figure>',
        convert_printout,
        html,
        flags=re.DOTALL,
    )

    # HTML directories use an ordered list only as a convenient browser-side
    # container. Word would add a second, unrelated 1., 2., 3. counter in
    # front of the actual chapter/figure/table numbers. Convert every entry to
    # an unnumbered paragraph and use Word's TOC styles for level indentation.
    def convert_directory(match: re.Match[str]) -> str:
        directory = match.group(0)
        directory = directory.replace(
            '</span><span class="directory-text">',
            '</span> <span class="directory-text">',
        )
        directory = re.sub(r'<ol\b[^>]*>', '', directory)
        directory = directory.replace('</ol>', '')

        def open_entry(item: re.Match[str]) -> str:
            attrs = item.group(1)
            level_match = re.search(r'toc-level-(\d+)', attrs)
            level = level_match.group(1) if level_match else '1'
            return f'<div custom-style="TOC {level}">'

        directory = re.sub(r'<li\b([^>]*)>', open_entry, directory)
        directory = directory.replace('</li>', '</div>')
        return directory

    html = re.sub(
        r'<nav class="document-directory (?:toc|lof|lot)-directory".*?</nav>',
        convert_directory,
        html,
        flags=re.DOTALL,
    )

    target.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
