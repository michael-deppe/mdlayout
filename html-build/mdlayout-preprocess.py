#!/usr/bin/env python3
"""Prepare mdlayout.tex for Pandoc without executing TeX package code."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

VERBATIM_ENVS = ("verbatim", "Verbatim", "wideverbatim", "grayverbatim",
                 "graywideverbatim", "listing", "Printout", "licensedisplayVerbatim",
                 "VerbatimInTextArea")

SIZE_NAMES = ("Huge", "huge", "LARGE", "Large", "large", "normalsize",
              "small", "footnotesize", "scriptsize", "tiny")


def evaluate_html_conditionals(text: str) -> str:
    """Select HTML branches of nested \\ifPdf/\\ifHtml conditionals."""
    token = re.compile(r"\\if[A-Za-z@]+|\\else\b|\\fi\b")
    values = {r"\ifPdf": False, r"\ifHtml": True}
    out: list[str] = []
    stack: list[dict[str, object]] = []
    active, pos = True, 0
    for match in token.finditer(text):
        if active:
            out.append(text[pos:match.start()])
        value = match.group(0)
        if value.startswith(r"\if"):
            known = value in values
            frame = {"known": known, "parent": active,
                     "condition": values.get(value, True)}
            stack.append(frame)
            if known:
                active = active and bool(frame["condition"])
            elif active:
                out.append(value)
        elif value == r"\else" and stack:
            frame = stack[-1]
            if frame["known"]:
                active = bool(frame["parent"]) and not bool(frame["condition"])
            elif active:
                out.append(value)
        elif value == r"\fi" and stack:
            frame = stack.pop()
            if not frame["known"] and active:
                out.append(value)
            active = bool(frame["parent"])
        elif active:
            out.append(value)
        pos = match.end()
    if active:
        out.append(text[pos:])
    return "".join(out)


def transform_font_groups(text: str) -> str:
    """Turn scoped LaTeX font declarations into filter-visible commands."""
    size_re = re.compile(r"^\\(" + "|".join(SIZE_NAMES) + r")\b")
    fontsize_re = re.compile(r"^\\fontsize\{([^{}]+)\}\{([^{}]+)\}\\selectfont")
    decl_re = re.compile(r"^\\(bfseries|itshape|slshape|ttfamily|sffamily|rmfamily)\b")

    def walk(value: str) -> str:
        out, pos = [], 0
        while pos < len(value):
            if value[pos] != "{" or (pos and value[pos-1] == "\\"):
                out.append(value[pos]); pos += 1; continue
            depth, end = 1, pos + 1
            while end < len(value) and depth:
                if value[end] == "{" and value[end-1] != "\\": depth += 1
                elif value[end] == "}" and value[end-1] != "\\": depth -= 1
                end += 1
            if depth:
                out.append(value[pos:]); break
            content = walk(value[pos+1:end-1])
            rest, classes = content.lstrip(), []
            while True:
                m = fontsize_re.match(rest)
                if m:
                    classes.append("tex-fontsize-" + re.sub(r"[^0-9a-zA-Z_-]", "-", m.group(1)))
                    rest = rest[m.end():].lstrip(); continue
                m = size_re.match(rest)
                if m:
                    classes.append("tex-size-" + m.group(1))
                    rest = rest[m.end():].lstrip(); continue
                m = decl_re.match(rest)
                if m:
                    classes.append("tex-" + m.group(1))
                    rest = rest[m.end():].lstrip(); continue
                break
            if classes:
                rest = re.sub(r"\\par\s*$", "", rest)
                out.append(r"\MDStyle{" + ",".join(classes) + "}{" + rest + "}")
            else:
                out.append("{" + content + "}")
            pos = end
        return "".join(out)
    return walk(text)


def extract_env(text: str, env: str):
    # Verbatim examples frequently contain literal \begin/\end strings.  Only
    # physical end-marker lines terminate the surrounding environment.
    pattern = re.compile(r"^[ \t]*\\begin\{" + re.escape(env) +
                         r"\}(?:\[[^]]*\])?[ \t]*\n(.*?)"
                         r"^[ \t]*\\end\{" + re.escape(env) + r"\}[ \t]*$",
                         re.S | re.M)
    return pattern


def protect_verbatim(text: str, codeblocks: list[str],
                     listings: dict[str, str] | None = None,
                     printouts: dict[str, dict] | None = None) -> str:
    # Select the first physical verbatim-like environment in the document,
    # irrespective of its name.  This protects an outer `listing` as a whole
    # before an inner `verbatim` can be extracted and lose its delimiters.
    names = "|".join(re.escape(env) for env in VERBATIM_ENVS)
    pattern = re.compile(
        r"^[ \t]*\\begin\{(" + names + r")\}(?:\[[^]]*\])?[ \t]*\n(.*?)"
        r"^[ \t]*\\end\{\1\}[ \t]*$",
        re.S | re.M,
    )

    def repl(match: re.Match[str]) -> str:
        n = len(codeblocks)
        codeblocks.append(match.group(2).strip("\n"))
        # Blank lines force Pandoc to create a separate paragraph.  The Lua
        # filter can then replace it with a real <pre><code> block.
        environment = match.group(1).lower()
        if environment == "verbatimintextarea":
            marker = "MDTextAreaCodeBlock"
        elif environment == "printout":
            marker = "MDPrintoutCodeBlock"
            if printouts is not None:
                option_match = re.search(r"\\begin\{Printout\}\[([^]]*)\]", match.group(0), re.S)
                supplied = parse_options(option_match.group(1) if option_match else "")
                forms = {
                    "green": {"color": "green", "paperheight": "999", "bandlines": "2", "feedlines": "3", "fitcolumns": "132", "linenumbers": "true", "punchholes": "true", "fontsize": r"\footnotesize"},
                    "blue": {"color": "blue", "paperheight": "999", "bandlines": "2", "feedlines": "3", "fitcolumns": "132", "linenumbers": "true", "punchholes": "true", "fontsize": r"\footnotesize"},
                    "ibm1403": {"color": "green", "paperheight": "60", "bandlines": "3", "feedlines": "3", "fitcolumns": "132", "linenumbers": "true", "punchholes": "true", "fontsize": r"\scriptsize"},
                    "simple": {"color": "blue", "paperheight": "999", "bandlines": "2", "feedlines": "0", "fitcolumns": "132", "linenumbers": "true", "punchholes": "false", "fontsize": r"\normalsize"},
                    "plain": {"color": "none", "paperheight": "999", "bandlines": "0", "feedlines": "0", "fitcolumns": "132", "linenumbers": "false", "punchholes": "false", "fontsize": r"\normalsize"},
                }
                spec = dict(forms.get(supplied.get("form", "plain"), forms["plain"]))
                spec.update(supplied)
                printouts[str(n)] = spec
        elif environment == "listing":
            marker = "MDListingCodeBlock"
            if listings is not None:
                option_match = re.search(r"\\begin\{listing\}\[([^]]*)\]", match.group(0))
                label_match = re.search(r"(?:^|,)\s*label\s*=\s*\{([^}]*)\}",
                                        option_match.group(1) if option_match else "")
                listings[str(n)] = label_match.group(1) if label_match else "Listing"
        elif environment in {"wideverbatim", "graywideverbatim"}:
            marker = "MDWideCodeBlock"
        elif environment == "verbatim":
            marker = "MDPlainCodeBlock"
        else:
            marker = "MDCodeBlock"
        return "\n\n" + rf"\{marker}{{{n}}}" + "\n\n"

    return pattern.sub(repl, text)


def protect_typewriter(text: str, codeblocks: list[str]) -> str:
    def repl(match: re.Match[str]) -> str:
        body = match.group(1).strip("\n")
        body = re.sub(r"\\verb(.)(.*?)\1", lambda m: m.group(2), body)
        body = re.sub(r"(?m)^(\s*)\\ ", r"\1", body)
        n = len(codeblocks); codeblocks.append(body)
        return "\n\n" + rf"\MDCodeBlock{{{n}}}" + "\n\n"
    return extract_env(text, "typewriter").sub(repl, text)


def protect_command_syntax(text: str, codeinlines: list[str]) -> str:
    # Both commands use \detokenize-like semantics in the LaTeX source.  Pandoc
    # does not expand that definition, so preserve their balanced argument here.
    for command in ("cmdsyntax", "latex"):
        needle, pos = rf"\{command}{{", 0
        while True:
            start = text.find(needle, pos)
            if start < 0: break
            content_start = start + len(needle)
            depth, end = 1, content_start
            while end < len(text) and depth:
                if text[end] == "{" and (end == 0 or text[end-1] != "\\"): depth += 1
                elif text[end] == "}" and (end == 0 or text[end-1] != "\\"): depth -= 1
                end += 1
            if depth: break
            codeinlines.append(text[content_start:end-1])
            marker_name = "MDLatexInline" if command == "latex" else "MDCodeInline"
            marker = rf"\{marker_name}{{{len(codeinlines)-1}}}"
            text = text[:start] + marker + text[end:]
            pos = start + len(marker)

    def protect_verb(match: re.Match[str]) -> str:
        codeinlines.append(match.group(2))
        return rf"\MDCodeInline{{{len(codeinlines)-1}}}"

    text = re.sub(r"\\verb(.)(.*?)\1", protect_verb, text)
    return text


def expand_sync_margin_command(text: str) -> str:
    """Turn the two-argument command form into the equivalent environments."""
    needle, pos = r"\SyncMarginAndTextArea", 0

    def argument_at(value: str, start: int) -> tuple[str, int] | None:
        while start < len(value) and value[start].isspace(): start += 1
        if start >= len(value) or value[start] != "{": return None
        depth, end = 1, start + 1
        while end < len(value) and depth:
            if value[end] == "{" and value[end-1] != "\\": depth += 1
            elif value[end] == "}" and value[end-1] != "\\": depth -= 1
            end += 1
        if depth: return None
        return value[start+1:end-1], end

    while True:
        start = text.find(needle, pos)
        if start < 0: break
        first = argument_at(text, start + len(needle))
        if first is None:
            pos = start + len(needle); continue
        second = argument_at(text, first[1])
        if second is None:
            pos = first[1]; continue
        replacement = (
            "\\begin{SynchronizedMarginAndTextArea}\n"
            "\\begin{TextInMarginArea}\n" + first[0] + "\n\\end{TextInMarginArea}\n"
            "\\begin{TextInTextArea}\n" + second[0] + "\n\\end{TextInTextArea}\n"
            "\\end{SynchronizedMarginAndTextArea}"
        )
        text = text[:start] + replacement + text[second[1]:]
        pos = start + len(replacement)
    return text


def protect_marginpars(text: str) -> str:
    """Preserve conventional LaTeX margin notes, including nested commands."""
    needle, pos = r"\marginpar", 0
    while True:
        start = text.find(needle, pos)
        if start < 0:
            break
        arg_start = start + len(needle)
        while arg_start < len(text) and text[arg_start].isspace():
            arg_start += 1
        if arg_start >= len(text) or text[arg_start] != "{":
            pos = arg_start
            continue
        depth, end = 1, arg_start + 1
        while end < len(text) and depth:
            if text[end] == "{" and text[end - 1] != "\\":
                depth += 1
            elif text[end] == "}" and text[end - 1] != "\\":
                depth -= 1
            end += 1
        if depth:
            pos = arg_start + 1
            continue
        replacement = r"\MDMarginPar{" + text[arg_start + 1:end - 1] + "}"
        text = text[:start] + replacement + text[end:]
        pos = start + len(replacement)
    return text


def split_top_level(value: str, separator: str) -> list[str]:
    fields, start, depth, escaped = [], 0, 0, False
    for pos, char in enumerate(value):
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth = max(0, depth - 1)
        elif char == separator and depth == 0:
            fields.append(value[start:pos].strip())
            start = pos + 1
    fields.append(value[start:].strip())
    return fields


def parse_options(value: str) -> dict[str, str]:
    result = {}
    for item in split_top_level(value, ","):
        if not item:
            continue
        key, sep, val = item.partition("=")
        val = val.strip()
        if len(val) >= 2 and val[0] == "{" and val[-1] == "}":
            val = val[1:-1]
        result[key.strip()] = val if sep else "true"
    return result


def parse_groups(value: str) -> tuple[list[str], str]:
    groups, pos = [], 0
    while True:
        while pos < len(value) and value[pos].isspace(): pos += 1
        if pos >= len(value) or value[pos] != "{": break
        start, depth, pos = pos + 1, 1, pos + 1
        while pos < len(value) and depth:
            if value[pos] == "{" and (pos == 0 or value[pos-1] != "\\"): depth += 1
            elif value[pos] == "}" and (pos == 0 or value[pos-1] != "\\"): depth -= 1
            pos += 1
        groups.append(value[start:pos-1])
    return groups, value[pos:]


def split_rows(body: str) -> list[list[str]]:
    rows, current, depth, pos = [], [], 0, 0
    while pos < len(body):
        ch = body[pos]
        if ch == "%":
            end = body.find("\n", pos)
            pos = len(body) if end < 0 else end + 1
            continue
        if ch == "{" and (pos == 0 or body[pos-1] != "\\"): depth += 1
        elif ch == "}" and (pos == 0 or body[pos-1] != "\\"): depth = max(0, depth - 1)
        if ch == "&" and depth == 0:
            current.append(body[:pos].strip()); body = body[pos+1:]; pos = 0; continue
        if ch == "\\" and pos + 1 < len(body) and body[pos+1] == "\\" and depth == 0:
            current.append(body[:pos].strip()); rows.append(current)
            current, body, pos = [], body[pos+2:], 0; continue
        pos += 1
    if body.strip() or current:
        current.append(body.strip()); rows.append(current)
    return [row for row in rows if any(cell for cell in row)]


def protect_tables(text: str, tables: list[dict]) -> str:
    begin = re.compile(r"\\begin\{ReferenceTable\}\s*(?:\[(.*?)\])?", re.S)
    while True:
        match = begin.search(text)
        if not match: break
        end = text.find(r"\end{ReferenceTable}", match.end())
        if end < 0: raise ValueError("ReferenceTable without matching end")
        options = parse_options(match.group(1) or "")
        headers, body = parse_groups(text[match.end():end])
        rows = split_rows(body)
        columns = int(options.get("columns", len(headers) or max((len(r) for r in rows), default=1)))
        header_mode = options.get("headers", "arguments").strip().lower()
        if header_mode == "row":
            headers = rows.pop(0) if rows else []
        elif header_mode in ("none", "false", "no", "off"):
            headers = []
        verbatim = options.get("verbatimcolumns", options.get("verbatimcolumn", ""))
        verbatim_cols = sorted({int(x) for x in re.findall(r"\d+", verbatim)})
        typewriter = options.get("typewritercolumns", options.get("typewritercolumn", ""))
        typewriter_cols = sorted({int(x) for x in re.findall(r"\d+", typewriter)})
        left = options.get("leftcolumns", options.get("leftcolumn", ""))
        center = options.get("centercolumns", options.get("centercolumn", ""))
        right = options.get("rightcolumns", options.get("rightcolumn", ""))
        left_cols = sorted({int(x) for x in re.findall(r"\d+", left)})
        center_cols = sorted({int(x) for x in re.findall(r"\d+", center)})
        right_cols = sorted({int(x) for x in re.findall(r"\d+", right)})
        tables.append({"options": options, "headers": headers[:columns],
                       "rows": [r[:columns] + [""] * max(0, columns-len(r)) for r in rows],
                       "columns": columns, "verbatim_columns": verbatim_cols,
                       "typewriter_columns": typewriter_cols,
                       "left_columns": left_cols, "center_columns": center_cols,
                       "right_columns": right_cols})
        text = text[:match.start()] + rf"\MDReferenceTable{{{len(tables)-1}}}" + text[end+len(r"\end{ReferenceTable}"):]
    return text


def protect_tabulars(text: str, tabulars: list[dict]) -> str:
    begin = re.compile(r"\\begin\{tabular\}")
    while True:
        match = begin.search(text)
        if not match: break
        groups, body_start = parse_groups(text[match.end():])
        if not groups: break
        consumed = len(text[match.end():]) - len(body_start)
        content_start = match.end() + consumed
        end = text.find(r"\end{tabular}", content_start)
        if end < 0: break
        rows = split_rows(text[content_start:end])
        columns = max((len(row) for row in rows), default=1)
        tabulars.append({"column_spec": groups[0], "columns": columns,
                         "rows": [r + [""] * (columns-len(r)) for r in rows]})
        marker = rf"\MDTabular{{{len(tabulars)-1}}}"
        text = text[:match.start()] + marker + text[end+len(r"\end{tabular}"):]
    return text


def collect_references(text: str) -> dict[str, dict[str, object]]:
    text = re.sub(r"(?m)(?<!\\)%.*$", "", text)
    events: list[tuple[int, str, str]] = []
    for m in re.finditer(r"\\(chapter|section|subsection)(\*)?\{", text):
        events.append((m.start(), "heading", m.group(1) + (m.group(2) or "")))
    for m in re.finditer(r"\\label\{((?:fig|tab|chap|sec):[^}]+)\}", text):
        events.append((m.start(), "label", m.group(1)))
    for m in re.finditer(r"\blabel\s*=\s*\{((?:fig|tab):[^}]+)\}", text):
        events.append((m.start(), "label", m.group(1)))
    counters = {"fig": 0, "tab": 0, "chapter": 0, "section": 0, "subsection": 0}
    refs = {}
    previous_float_label = 0
    for position, event, value in sorted(events):
        if event == "heading":
            if value.endswith("*"): continue
            if value == "chapter":
                counters["chapter"] += 1; counters["section"] = counters["subsection"] = 0
            elif value == "section":
                counters["section"] += 1; counters["subsection"] = 0
            else:
                counters["subsection"] += 1
            continue
        label = value
        if label in refs: continue
        kind = label.split(":", 1)[0]
        if kind in {"fig", "tab"}:
            segment = text[previous_float_label:position]
            if re.search(r"\\caption\s*\{|\bcaption\s*=\s*\{", segment):
                counters[kind] += 1
            number = str(counters[kind])
            previous_float_label = position
        elif kind == "chap":
            number = str(counters["chapter"])
        else:
            number = f'{counters["chapter"]}.{counters["section"]}'
            if counters["subsection"]: number += f'.{counters["subsection"]}'
        refs[label] = {"kind": kind, "number": number}
    return refs


def collect_directory_entries(text: str, refs: dict[str, dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    """Collect captions in source order for HTML lists of figures and tables."""
    text = re.sub(r"(?m)(?<!\\)%.*$", "", text)
    result: dict[str, list[dict[str, object]]] = {"lof": [], "lot": []}

    def braced_at(start: int) -> str | None:
        while start < len(text) and text[start].isspace():
            start += 1
        if start >= len(text) or text[start] != "{":
            return None
        depth, end = 1, start + 1
        while end < len(text) and depth:
            if text[end] == "{" and text[end - 1] != "\\": depth += 1
            elif text[end] == "}" and text[end - 1] != "\\": depth -= 1
            end += 1
        return None if depth else text[start + 1:end - 1]

    labels = list(re.finditer(r"\\label\{((?:fig|tab):[^}]+)\}|\blabel\s*=\s*\{((?:fig|tab):[^}]+)\}", text))
    previous = 0
    for match in labels:
        label = match.group(1) or match.group(2)
        reference = refs.get(label)
        if not reference:
            previous = match.end(); continue
        segment = text[previous:match.start()]
        standard = segment.rfind(r"\caption")
        option = segment.rfind("caption=")
        caption = None
        if standard >= option and standard >= 0:
            caption = braced_at(previous + standard + len(r"\caption"))
        elif option >= 0:
            caption = braced_at(previous + option + len("caption="))
        if caption:
            kind = "lof" if reference["kind"] == "fig" else "lot"
            result[kind].append({"label": label, "number": reference["number"], "caption": caption})
        previous = match.end()
    return result


def read_simple_definitions(style: Path | None) -> dict[str, str]:
    if not style or not style.is_file(): return {}
    source = style.read_text(encoding="utf-8")
    definitions = {}
    for name, value in re.findall(
            r"\\newcommand\*?\{\\([A-Za-z@]+)\}\{([^{}]*)\}", source):
        definitions[name] = value.strip()
    for name, value in re.findall(r"\\def\\([A-Za-z@]+)\{([^{}]*)\}", source):
        definitions[name] = value.strip()
    # Resolve simple definitions which refer to another captured constant.
    for _ in range(10):
        changed = False
        for name, value in list(definitions.items()):
            expanded = re.sub(r"\\([A-Za-z@]+)",
                              lambda m: definitions.get(m.group(1), m.group(0)), value)
            if expanded != value:
                definitions[name], changed = expanded, True
        if not changed: break
    return definitions


def expand_definitions(text: str, definitions: dict[str, str]) -> str:
    wanted = {k: v for k, v in definitions.items()
              if k.startswith("mdDefault") or k in
              {"mdlayoutVersion", "mdlayoutDate", "mdlayoutPackageName"}}
    for name in sorted(wanted, key=len, reverse=True):
        # A replacement string such as ``0.55\baselineskip`` must be returned
        # by a callable; otherwise Python's regex engine turns ``\b`` into a
        # backspace character.
        text = re.sub(
            r"(?<!\\string)\\" + re.escape(name) + r"\b",
            lambda _match, value=wanted[name]: value,
            text,
        )
    return text


def evaluate_dimensions(text: str, source: str) -> str:
    """Evaluate the simple baseline-relative dimexpr forms used by mdlayout."""
    documentclass = re.search(r"\\documentclass\[([^]]*)\]", source, re.S)
    size = "10"
    if documentclass:
        match = re.search(r"(?:^|,)\s*(10|11|12)pt\s*(?:,|$)", documentclass.group(1))
        if match:
            size = match.group(1)
    baseline = {"10": 12.0, "11": 13.6, "12": 14.5}[size]

    def baseline_dimension(match: re.Match[str]) -> str:
        value = float(match.group(1)) * baseline
        return f"{value:.5f}".rstrip("0").rstrip(".") + "pt"

    return re.sub(
        r"\\the\s*\\dimexpr\s*([0-9]*\.?[0-9]+)"
        r"\s*\\baselineskip\s*\\relax",
        baseline_dimension,
        text,
    )


def number_display_math(text: str) -> str:
    """Add book-style chapter.equation numbers before Pandoc drops labels."""
    token = re.compile(r"\\chapter(\*)?\{|\\begin\{(equation|align)\}(.*?)\\end\{\2\}", re.S)
    chapter = equation = 0
    out, pos = [], 0
    for match in token.finditer(text):
        out.append(text[pos:match.start()])
        if match.group(0).startswith(r"\chapter"):
            if not match.group(1): chapter += 1; equation = 0
            out.append(match.group(0))
        else:
            env, body = match.group(2), match.group(3)
            if env == "equation":
                equation += 1
                number = f"{chapter}.{equation}"
                body = re.sub(r"\\label\{eq:[^}]+\}", rf"\\tag{{{number}}}", body, count=1)
            else:
                def align_label(label_match: re.Match[str]) -> str:
                    nonlocal equation
                    equation += 1
                    return rf"&&\text{{({chapter}.{equation})}}"
                body = re.sub(r"\\label\{eq:[^}]+\}", align_label, body)
            out.append(r"\begin{" + env + "}" + body + r"\end{" + env + "}")
        pos = match.end()
    out.append(text[pos:])
    return "".join(out)


def read_colors(preamble: Path | None) -> dict[str, str]:
    if not preamble or not preamble.is_file(): return {}
    source = preamble.read_text(encoding="utf-8")
    return {name: f"rgb({rgb})" for name, rgb in re.findall(
        r"\\definecolor\{(mdColor[A-Za-z]+)\}\{RGB\}\{([0-9, ]+)\}", source)}


def expand_lipsum(text: str) -> str:
    """Expand lipsum paragraph/sentence selections from TeX Live's source."""
    try:
        found = subprocess.run(["kpsewhich", "lipsum.ltd.tex"], check=True,
                               capture_output=True, text=True).stdout.strip()
        source = Path(found).read_text(encoding="utf-8")
    except (OSError, subprocess.SubprocessError):
        return text
    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in
                  re.findall(r"\\NewLipsumPar\{%.*?\n(.*?)\}\s*%", source, re.S)]

    def select(match: re.Match[str]) -> str:
        parspec, sentencespec = match.group(1) or "1", match.group(2)
        pstart, _, pend = parspec.partition("-")
        selected = paragraphs[int(pstart)-1:int(pend or pstart)]
        value = "\n\n".join(selected)
        if sentencespec and len(selected) == 1:
            sentences = re.findall(r".*?(?:\.)(?=\s|$)", value)
            sstart, _, send = sentencespec.partition("-")
            value = " ".join(s.strip() for s in sentences[int(sstart)-1:int(send or sstart)])
        return value
    return re.sub(r"\\lipsum(?:\[([^]]+)\])?(?:\[([^]]+)\])?", select, text)


def protect_images(text: str, images: list[dict]) -> str:
    """Preserve each image's LaTeX width as a container-relative CSS width."""
    pattern = re.compile(
        r"\\(PDFImage|includegraphics)(?:\[([^]]*)\])?\{([^}]+)\}"
    )

    def css_width(options: str) -> str | None:
        found = re.search(r"(?:^|,)\s*width\s*=\s*([^,]+)", options)
        if not found:
            return None
        value = found.group(1).strip().replace(" ", "")
        relative = re.fullmatch(
            r"([0-9]*\.?[0-9]+)?\\(?:mdTextWidth|mdMarginWidth|"
            r"mdFullWidth|linewidth|textwidth|fullwidth)", value
        )
        if relative:
            factor = float(relative.group(1) or "1")
            return f"{factor * 100:g}%"
        if re.fullmatch(r"[0-9]*\.?[0-9]+(?:pt|mm|cm|in|em|ex)", value):
            return value
        return None

    def replace(match: re.Match[str]) -> str:
        command, options, source = match.groups()
        if command == "PDFImage":
            source = f"images/{source}.webp"
        images.append({"source": source, "width": css_width(options or "")})
        return rf"\MDImage{{{len(images)-1}}}"

    return pattern.sub(replace, text)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("data", type=Path)
    ap.add_argument("--style", type=Path)
    ap.add_argument("--preamble", type=Path)
    args = ap.parse_args()
    text = args.source.read_text(encoding="utf-8")
    scan = protect_command_syntax(protect_verbatim(text, []), [])
    scan = evaluate_html_conditionals(scan)
    refs = collect_references(scan)
    directories = collect_directory_entries(scan, refs)
    codes: list[str] = []
    codeinlines: list[str] = []
    images: list[dict] = []
    listings: dict[str, str] = {}
    printouts: dict[str, dict] = {}
    text = protect_verbatim(text, codes, listings, printouts)
    text = protect_command_syntax(text, codeinlines)
    text = evaluate_html_conditionals(text)
    # A standalone \latex fragment is documentation source, not prose.  Drop
    # presentation-only \noindent/vertical-spacing commands so Pandoc sees a
    # real block on both the opening and closing lines.
    text = re.sub(
        r"(?m)^[ \t]*\\noindent[ \t]*(\\MDLatexInline\{\d+\})"
        r"(?:\\\\\[[^]]+\])?[ \t]*$",
        r"\n\n\1\n\n",
        text,
    )
    text = re.sub(
        r"\\mdSeeRight(?:\[([0-9]+(?:\.[0-9]+)?)\])?",
        lambda match: rf"\MDSeeRight{{{match.group(1) or '1'}}}",
        text,
    )
    text = expand_sync_margin_command(text)
    text = protect_marginpars(text)
    text = re.sub(r"\\tableofcontents\b", r"\\MDDirectory{toc}", text)
    text = re.sub(r"\\listoffigures\b", r"\\MDDirectory{lof}", text)
    text = re.sub(r"\\listoftables\b", r"\\MDDirectory{lot}", text)
    definitions = read_simple_definitions(args.style)
    colors = read_colors(args.preamble)
    text = expand_definitions(text, definitions)
    text = evaluate_dimensions(text, args.source.read_text(encoding="utf-8"))
    text = re.sub(r"\\currenttime\b", datetime.now().strftime("%H:%M:%S"), text)
    text = expand_lipsum(text)
    text = number_display_math(text)
    text = re.sub(r"\\string\\\\", r"\\textbackslash{}\\textbackslash{}", text)
    text = re.sub(r"\\string\\([A-Za-z@]+)",
                  lambda m: r"\textbackslash{}" + m.group(1), text)
    text = protect_typewriter(text, codes)
    text = re.sub(r"\\mdlayout(?:\{\})?", r"\\MDWordmark", text)
    text = re.sub(r"\\(?:page)?ref\{((?:fig|tab|chap|sec):[^}]+)\}",
                  lambda m: rf"\MDRef{{{m.group(1)}}}{{{refs.get(m.group(1), {}).get('number', '?')}}}", text)
    text = re.sub(r"\\label\{((?:fig|tab):[^}]+)\}",
                  lambda m: rf"\MDLabel{{{m.group(1)}}}", text)
    # Preserve width information before Pandoc discards package dimensions
    # such as \mdTextWidth and \mdMarginWidth.
    text = protect_images(text, images)
    tables: list[dict] = []
    tabulars: list[dict] = []
    text = protect_tables(text, tables)
    text = protect_tabulars(text, tabulars)
    text = re.sub(r"\{\s*\\small\s*\\MDReferenceTable\{(\d+)\}\s*\}",
                  lambda m: rf"\MDStyledTable{{tex-size-small}}{{{m.group(1)}}}", text)
    text = transform_font_groups(text)
    marker = re.compile(r"\\MD(?:Plain|Wide|Listing|Printout|TextArea)?CodeBlock\{(\d+)\}")
    inline_marker = re.compile(r"\\MD(?:Code|Latex)Inline\{(\d+)\}")
    # If one displayed verbatim environment contained another one, protection
    # happened inside-out. Expand such internal placeholders before serializing.
    for i, code in enumerate(codes):
        for _ in range(10):
            expanded = marker.sub(lambda m: codes[int(m.group(1))], code)
            expanded = inline_marker.sub(
                lambda m: codeinlines[int(m.group(1))], expanded
            )
            if expanded == code: break
            code = expanded
        codes[i] = code
    args.output.write_text(text, encoding="utf-8")
    for table in tables:
        label = table.get("options", {}).get("label")
        if label in refs: table["number"] = refs[label]["number"]
    args.data.write_text(json.dumps({"codeblocks": codes, "codeinlines": codeinlines,
                                     "tables": tables, "tabulars": tabulars, "images": images,
                                     "listings": listings,
                                     "printouts": printouts,
                                     "directories": directories,
                                     "refs": refs,
                                     "definitions": definitions, "colors": colors}, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__": main()
