#!/usr/bin/env python3
"""Apply Word-specific layout details that Pandoc cannot express in HTML."""

from pathlib import Path
import math
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"
DOCUMENT_MAIN_FONT: str | None = None
DOCUMENT_MONO_FONT = "Courier New"
ET.register_namespace("w", W_NS)
ET.register_namespace("m", "http://schemas.openxmlformats.org/officeDocument/2006/math")
ET.register_namespace("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")
ET.register_namespace("o", "urn:schemas-microsoft-com:office:office")
ET.register_namespace("v", "urn:schemas-microsoft-com:vml")
ET.register_namespace("w10", "urn:schemas-microsoft-com:office:word")
ET.register_namespace("a", "http://schemas.openxmlformats.org/drawingml/2006/main")
ET.register_namespace("pic", "http://schemas.openxmlformats.org/drawingml/2006/picture")
ET.register_namespace("wp", "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing")


def format_styles(xml: bytes) -> bytes:
    root = ET.fromstring(xml)
    replace_nonportable_fonts(root)
    if DOCUMENT_MAIN_FONT:
        defaults = root.find(f"{W}docDefaults")
        if defaults is None:
            defaults = ET.Element(f"{W}docDefaults")
            root.insert(0, defaults)
        run_default = defaults.find(f"{W}rPrDefault")
        if run_default is None:
            run_default = ET.SubElement(defaults, f"{W}rPrDefault")
        run_properties = run_default.find(f"{W}rPr")
        if run_properties is None:
            run_properties = ET.SubElement(run_default, f"{W}rPr")
        fonts = run_properties.find(f"{W}rFonts")
        if fonts is None:
            fonts = ET.SubElement(run_properties, f"{W}rFonts")
        for attribute in ("ascii", "hAnsi", "cs"):
            fonts.set(f"{W}{attribute}", DOCUMENT_MAIN_FONT)
    indents = {"TOC1": "0", "TOC2": "360", "TOC3": "720"}

    for style in root.findall(f"{W}style"):
        style_id = style.get(f"{W}styleId")
        style_type = style.get(f"{W}type")
        if style_type in {"paragraph", "character"}:
            font_name = (
                DOCUMENT_MONO_FONT
                if style_id in {"SourceCode", "VerbatimChar"}
                else DOCUMENT_MAIN_FONT
            )
            if font_name:
                run_properties = style.find(f"{W}rPr")
                if run_properties is None:
                    run_properties = ET.SubElement(style, f"{W}rPr")
                fonts = run_properties.find(f"{W}rFonts")
                if fonts is None:
                    fonts = ET.SubElement(run_properties, f"{W}rFonts")
                for attribute in ("ascii", "hAnsi", "cs"):
                    fonts.set(f"{W}{attribute}", font_name)
        if style_id == "Heading1":
            ppr = style.find(f"{W}pPr")
            if ppr is None:
                ppr = ET.SubElement(style, f"{W}pPr")
            if ppr.find(f"{W}pageBreakBefore") is None:
                ET.SubElement(ppr, f"{W}pageBreakBefore")
        if style_id not in indents:
            continue
        ppr = style.find(f"{W}pPr")
        if ppr is None:
            ppr = ET.SubElement(style, f"{W}pPr")
        ind = ppr.find(f"{W}ind")
        if ind is None:
            ind = ET.SubElement(ppr, f"{W}ind")
        ind.set(f"{W}left", indents[style_id])

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def heading_sizes(styles_xml: bytes) -> dict[str, str]:
    root = ET.fromstring(styles_xml)
    sizes: dict[str, str] = {}
    for style in root.findall(f"{W}style"):
        style_id = style.get(f"{W}styleId", "")
        if not style_id.startswith("Heading"):
            continue
        size = style.find(f"{W}rPr/{W}sz")
        if size is not None and size.get(f"{W}val"):
            sizes[style_id] = size.get(f"{W}val", "")
    return sizes


def page_usable_width(root: ET.Element) -> int:
    section = root.find(f".//{W}sectPr")
    usable_twips = 9360  # 6.5 in: safe Word default when geometry is absent.
    if section is not None:
        page = section.find(f"{W}pgSz")
        margins = section.find(f"{W}pgMar")
        if page is not None and margins is not None:
            width = int(page.get(f"{W}w", "12240"))
            left = int(margins.get(f"{W}left", "1440"))
            right = int(margins.get(f"{W}right", "1440"))
            usable_twips = max(1440, width - left - right)

    return usable_twips


def printout_font_size(print_width: int, fitcolumns: int) -> str:
    points = (print_width / 20) / (max(1, fitcolumns) * 0.62)
    points = max(5.0, min(9.0, points * 0.97))
    return str(max(10, round(points * 2)))


def add_word(parent: ET.Element, name: str, **attrs: str) -> ET.Element:
    element = ET.SubElement(parent, f"{W}{name}")
    for key, value in attrs.items():
        element.set(f"{W}{key}", value)
    return element


def replace_nonportable_fonts(root: ET.Element) -> None:
    """Avoid font substitution warnings and metric changes in Apple Pages."""
    for fonts in root.iter(f"{W}rFonts"):
        for attribute in ("ascii", "hAnsi", "cs", "eastAsia"):
            key = f"{W}{attribute}"
            if fonts.get(key) == "Consolas":
                fonts.set(key, DOCUMENT_MONO_FONT)
            elif fonts.get(key) in {"Aptos", "Aptos Display"} and DOCUMENT_MAIN_FONT:
                fonts.set(key, DOCUMENT_MAIN_FONT)


def make_plain_printout(root: ET.Element, spec: dict[str, str],
                        lines: list[str]) -> ET.Element:
    """Create the borderless paragraph used by form=plain."""
    usable = page_usable_width(root)
    calculated = int(printout_font_size(usable, int(spec.get("fit", "132"))))
    size = str(max(12, calculated))  # plain has no side columns: prefer 6 pt.
    paragraph = ET.Element(f"{W}p")
    properties = add_word(paragraph, "pPr")
    add_word(properties, "pStyle", val="SourceCode")
    add_word(properties, "spacing", before="0", after="0",
             line="140", lineRule="exact")
    run = add_word(paragraph, "r")
    run_properties = add_word(run, "rPr")
    add_word(run_properties, "rFonts", ascii=DOCUMENT_MONO_FONT,
             hAnsi=DOCUMENT_MONO_FONT, cs=DOCUMENT_MONO_FONT)
    add_word(run_properties, "sz", val=size)
    add_word(run_properties, "szCs", val=size)
    for index, line in enumerate(lines):
        if index:
            add_word(run, "br")
        text = add_word(run, "t")
        if line.startswith(" ") or line.endswith(" "):
            text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        text.text = line
    return paragraph


def make_printout_table(root: ET.Element, spec: dict[str, str],
                        lines: list[str]) -> ET.Element:
    usable = page_usable_width(root)
    holes = spec.get("holes") == "1"
    numbers = spec.get("numbers") == "1"
    # Keep the combined side reservation unchanged: the wider hole strip gives
    # the perforation visual breathing room, while the narrower number strip
    # moves both vertical rules closer to the digits.
    hole_width = 220 if holes else 30
    number_width = 220 if numbers else 30
    text_width = usable - 2 * (hole_width + number_width)
    widths = [hole_width, number_width, text_width, number_width, hole_width]
    size = printout_font_size(text_width, int(spec.get("fit", "132")))
    paperheight = min(999, max(1, int(spec.get("paper", "999"))))
    bandlines = max(0, int(spec.get("bands", "0")))
    feedlines = max(0, int(spec.get("feed", "0")))
    light, dark = {
        "green": ("DBF0DB", "63B663"),
        "blue": ("D6EFFF", "41B6FF"),
        "none": ("FFFFFF", "BFBFBF"),
    }.get(spec.get("color", "none"), ("FFFFFF", "BFBFBF"))

    table = ET.Element(f"{W}tbl")
    properties = add_word(table, "tblPr")
    add_word(properties, "tblW", w=str(usable), type="dxa")
    add_word(properties, "tblLayout", type="fixed")
    # Pages otherwise applies its own generous default cell padding.  Declare
    # zero table-level margins as well as the per-cell margins below.
    table_margins = add_word(properties, "tblCellMar")
    for side in ("top", "left", "bottom", "right"):
        add_word(table_margins, side, w="0", type="dxa")
    borders = add_word(properties, "tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        add_word(borders, edge, val="nil")
    grid = add_word(table, "tblGrid")
    for width in widths:
        add_word(grid, "gridCol", w=str(width))

    for index, line in enumerate(lines, 1):
        paperline = ((index - 1) % paperheight) + 1
        shaded = bandlines > 0 and ((paperline - 1) // bandlines) % 2 == 0
        punched = holes and feedlines > 0 and (paperline - 1) % feedlines == 0
        values = [
            "●" if punched else "",
            str(paperline).zfill(2) if numbers else "",
            line,
            str(paperline).zfill(2) if numbers else "",
            "●" if punched else "",
        ]
        row = add_word(table, "tr")
        row_properties = add_word(row, "trPr")
        add_word(row_properties, "cantSplit")
        # Do not write w:trHeight here.  Apple Pages imports even a small exact
        # Word height as a fixed 0.71 cm row; its "Fit" operation instead
        # computes the desired 0.43 cm from the content.  With zero cell and
        # paragraph spacing, omitting trHeight selects that automatic mode at
        # import time as well.
        for column, (width, value) in enumerate(zip(widths, values)):
            cell = add_word(row, "tc")
            cell_properties = add_word(cell, "tcPr")
            add_word(cell_properties, "tcW", w=str(width), type="dxa")
            add_word(cell_properties, "vAlign", val="center")
            margins = add_word(cell_properties, "tcMar")
            for side in ("top", "left", "bottom", "right"):
                add_word(margins, side, w="16" if column == 2 else "0", type="dxa")
            if column == 2 and shaded:
                add_word(cell_properties, "shd", val="clear", color="auto", fill=light)
            # Explicitly suppress inherited horizontal rules (in particular
            # Word's default first-row separator), then add only the vertical
            # paper/number boundaries required by the Printout design.
            cell_borders = add_word(cell_properties, "tcBorders")
            for edge in ("top", "bottom"):
                add_word(cell_borders, edge, val="nil")
            if column in (0, 1, 2, 3):
                add_word(cell_borders, "right", val="single", sz="4", color=dark)
            if column in (1, 2, 3, 4):
                add_word(cell_borders, "left", val="single", sz="4", color=dark)

            paragraph = add_word(cell, "p")
            paragraph_properties = add_word(paragraph, "pPr")
            add_word(paragraph_properties, "spacing", before="0", after="0",
                     line="100", lineRule="exact")
            if column != 2:
                add_word(paragraph_properties, "jc", val="center")
            run = add_word(paragraph, "r")
            run_properties = add_word(run, "rPr")
            # U+25CF has markedly different metrics in IBM Plex Mono and in
            # the fallback fonts selected by Word/OnlyOffice.  The punch holes
            # are graphical marks rather than printout text, so use the
            # document's portable main font and avoid renderer-specific glyph
            # fallback.  All other Printout cells remain monospaced.
            run_font = ((DOCUMENT_MAIN_FONT or "Arial")
                        if column in (0, 4) else DOCUMENT_MONO_FONT)
            add_word(run_properties, "rFonts", ascii=run_font,
                     hAnsi=run_font, cs=run_font, eastAsia=run_font)
            # Keep the holes prominent, but 0.5 pt smaller than the former
            # 140-percent marker so OnlyOffice has sufficient glyph clearance.
            run_size = str(max(1, round(int(size) * 1.4) - 1)) if column in (0, 4) else size
            add_word(run_properties, "sz", val=run_size)
            add_word(run_properties, "szCs", val=run_size)
            if column in (0, 4):
                # The enlarged punch-hole glyph has a small ascender overhang.
                # Word displays that overhang, while OnlyOffice clips it at the
                # top edge of the first table row.  Lowering only the marker by
                # half a point keeps the compact automatic row height intact
                # while leaving equal clearance above and below in OnlyOffice.
                add_word(run_properties, "position", val="-1")
            if column in (1, 3):
                add_word(run_properties, "color", val=dark)
            elif column in (0, 4):
                add_word(run_properties, "color", val="D9D9D9")
            text = add_word(run, "t")
            if value.startswith(" ") or value.endswith(" "):
                text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            text.text = value
    return table


def format_document(xml: bytes, sizes: dict[str, str]) -> bytes:
    root = ET.fromstring(xml)
    replace_nonportable_fonts(root)
    parents = {child: parent for parent in root.iter() for child in parent}
    for paragraph in list(root.iter(f"{W}p")):
        paragraph_text = ''.join(
            node.text or '' for node in paragraph.iter(f"{W}t")
        )
        paragraph_style = paragraph.find(f"{W}pPr/{W}pStyle")
        style_id = (paragraph_style.get(f"{W}val", "")
                    if paragraph_style is not None else "")
        if paragraph_text.strip() == "Contents" and style_id == "Heading2":
            paragraph_properties = paragraph.find(f"{W}pPr")
            if paragraph_properties is None:
                paragraph_properties = ET.Element(f"{W}pPr")
                paragraph.insert(0, paragraph_properties)
            if paragraph_properties.find(f"{W}pageBreakBefore") is None:
                add_word(paragraph_properties, "pageBreakBefore")

        marker = re.match(r'MDPRINTOUT:([^;]+);', paragraph_text)
        if marker:
            spec = dict(item.split("=", 1) for item in marker.group(1).split(","))
            lines = [""]
            marker_remaining = len(marker.group(0))
            for element in paragraph.iter():
                if element.tag == f"{W}br":
                    lines.append("")
                elif element.tag == f"{W}t":
                    value = element.text or ""
                    if marker_remaining:
                        count = min(marker_remaining, len(value))
                        value = value[count:]
                        marker_remaining -= count
                    lines[-1] += value
            parent = parents.get(paragraph)
            if parent is not None:
                position = list(parent).index(paragraph)
                parent.remove(paragraph)
                is_plain = (
                    spec.get("color") == "none"
                    and spec.get("numbers") == "0"
                    and spec.get("holes") == "0"
                    and int(spec.get("bands", "0")) == 0
                )
                replacement = (make_plain_printout(root, spec, lines) if is_plain
                               else make_printout_table(root, spec, lines))
                parent.insert(position, replacement)
            continue

        paragraph_style = paragraph.find(f"{W}pPr/{W}pStyle")
        if paragraph_style is None:
            continue
        style_id = paragraph_style.get(f"{W}val", "")
        size = sizes.get(style_id)
        if not size:
            continue

        for run in paragraph.iter(f"{W}r"):
            run_properties = run.find(f"{W}rPr")
            if run_properties is None:
                continue
            run_style = run_properties.find(f"{W}rStyle")
            if run_style is None or run_style.get(f"{W}val") != "VerbatimChar":
                continue
            for element_name in ("sz", "szCs"):
                element = run_properties.find(f"{W}{element_name}")
                if element is None:
                    element = ET.SubElement(run_properties, f"{W}{element_name}")
                element.set(f"{W}val", size)

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def format_font_references(xml: bytes) -> bytes:
    root = ET.fromstring(xml)
    if DOCUMENT_MAIN_FONT:
        # A Word reference document can carry many unused fonts (notably Aptos
        # and Aptos Display).  Pages reports every such font as missing even
        # when no run uses it.  Rebuild the declaration from the fonts the
        # generated document really needs.
        for child in list(root):
            root.remove(child)
        for name, family, pitch in (
            (DOCUMENT_MAIN_FONT, "swiss", "variable"),
            (DOCUMENT_MONO_FONT, "modern", "fixed"),
            ("Cambria Math", "roman", "variable"),
        ):
            font = ET.SubElement(root, f"{W}font")
            font.set(f"{W}name", name)
            add_word(font, "charset", val="00")
            add_word(font, "family", val=family)
            add_word(font, "pitch", val=pitch)
        return ET.tostring(root, encoding="utf-8", xml_declaration=True)

    replace_nonportable_fonts(root)
    for font in root.iter(f"{W}font"):
        if font.get(f"{W}name") in {"Consolas", "Courier New"}:
            font.set(f"{W}name", DOCUMENT_MONO_FONT)
        elif (font.get(f"{W}name") in {"Aptos", "Aptos Display"}
              and DOCUMENT_MAIN_FONT):
            font.set(f"{W}name", DOCUMENT_MAIN_FONT)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def latex_fonts(preamble: Path | None) -> tuple[str | None, str]:
    """Read portable fontspec selections, retaining Word defaults otherwise."""
    if preamble is None or not preamble.is_file():
        return None, "Courier New"
    source = re.sub(r"(?m)(?<!\\)%.*$", "", preamble.read_text(encoding="utf-8"))

    def selected(command: str) -> str | None:
        match = re.search(rf"\\{command}\s*\{{([^}}]+)\}}", source)
        if not match:
            return None
        name = match.group(1).strip()
        tex_only = (
            r"^(?:cmr|cmss|cmtt)\d*$",
            r"^Computer Modern(?: .*)?$",
            r"^Latin Modern(?: .*)?$",
            r"^CMU(?: .*)?$",
            r"^TeX Gyre(?: .*)?$",
        )
        return None if any(re.match(pattern, name, re.I) for pattern in tex_only) else name

    return selected("setmainfont"), selected("setmonofont") or "Courier New"


def main() -> None:
    if len(sys.argv) not in (2, 3):
        raise SystemExit("usage: format-docx.py DOCUMENT.docx [PREAMBLE.tex]")

    document = Path(sys.argv[1])
    preamble = Path(sys.argv[2]) if len(sys.argv) == 3 and sys.argv[2] else None
    global DOCUMENT_MAIN_FONT, DOCUMENT_MONO_FONT
    DOCUMENT_MAIN_FONT, DOCUMENT_MONO_FONT = latex_fonts(preamble)
    print(
        "DOCX fonts: "
        f"main={DOCUMENT_MAIN_FONT or 'reference-document default'}, "
        f"mono={DOCUMENT_MONO_FONT}"
    )
    fd, temporary_name = tempfile.mkstemp(
        prefix=f"{document.stem}-", suffix=".docx", dir=document.parent
    )
    os.close(fd)
    temporary = Path(temporary_name)

    try:
        with zipfile.ZipFile(document, "r") as source:
            entries = [(info, source.read(info.filename)) for info in source.infolist()]

        styles = next(data for info, data in entries if info.filename == "word/styles.xml")
        formatted_styles = format_styles(styles)
        sizes = heading_sizes(formatted_styles)

        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as target:
            for info, contents in entries:
                if info.filename == "word/styles.xml":
                    contents = formatted_styles
                elif info.filename == "word/document.xml":
                    contents = format_document(contents, sizes)
                elif info.filename == "word/fontTable.xml":
                    contents = format_font_references(contents)
                # Aptos names can also occur in the Office theme rather than
                # in Word's w:rFonts elements.  Pages reports those theme
                # references as missing even when no visible run uses them.
                if info.filename.endswith(".xml") and DOCUMENT_MAIN_FONT:
                    encoded_main = DOCUMENT_MAIN_FONT.encode("utf-8")
                    contents = contents.replace(
                        b'="Aptos Display"', b'="' + encoded_main + b'"'
                    ).replace(
                        b'="Aptos"', b'="' + encoded_main + b'"'
                    )
                    if info.filename.startswith("word/theme/"):
                        contents = re.sub(
                            rb'(<a:latin\s+typeface=")[^"]*(")',
                            lambda match: match.group(1) + encoded_main + match.group(2),
                            contents,
                        )
                target.writestr(info, contents)
        temporary.replace(document)
    finally:
        if temporary.exists():
            temporary.unlink()


if __name__ == "__main__":
    main()
