#!/usr/bin/env python3
"""Create a horizontally scaled derivative of a TrueType font."""

from __future__ import annotations

import argparse
from pathlib import Path

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--scale", type=float, default=0.85)
    parser.add_argument("--family", default="mdlayout Plex Mono 85")
    args = parser.parse_args()
    if not 0 < args.scale <= 1:
        raise ValueError("scale must be greater than zero and at most one")

    font = TTFont(args.input)
    glyph_set = font.getGlyphSet()
    scaled = {}
    for name in font.getGlyphOrder():
        recording = DecomposingRecordingPen(glyph_set)
        glyph_set[name].draw(recording)
        pen = TTGlyphPen(None)
        recording.replay(TransformPen(pen, (args.scale, 0, 0, 1, 0, 0)))
        scaled[name] = pen.glyph()
    font["glyf"].glyphs = scaled

    for name, (advance, side_bearing) in font["hmtx"].metrics.items():
        font["hmtx"].metrics[name] = (
            round(advance * args.scale), round(side_bearing * args.scale)
        )
    font["hhea"].advanceWidthMax = round(font["hhea"].advanceWidthMax * args.scale)
    font["OS/2"].xAvgCharWidth = round(font["OS/2"].xAvgCharWidth * args.scale)

    # TrueType instructions target the original x coordinates and must not be
    # retained after changing the outlines.
    for table in ("fpgm", "prep", "cvt ", "gasp", "DSIG"):
        if table in font:
            del font[table]

    family = args.family
    postscript = "".join(ch for ch in family if ch.isalnum()) + "-Regular"
    for platform, encoding, language in ((3, 1, 0x409), (1, 0, 0)):
        font["name"].setName(family, 1, platform, encoding, language)
        font["name"].setName("Regular", 2, platform, encoding, language)
        font["name"].setName(family + " Regular", 4, platform, encoding, language)
        font["name"].setName(postscript, 6, platform, encoding, language)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    font.recalcBBoxes = True
    # A .woff2 output uses fontTools' optional Brotli encoder.  A .ttf output
    # needs no extra dependency and is supported directly by all browsers.
    font.flavor = "woff2" if args.output.suffix.lower() == ".woff2" else None
    font.save(args.output)


if __name__ == "__main__":
    main()
