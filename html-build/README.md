# HTML build for `mdlayout.tex`

Requirements: Pandoc 3.x and Python 3.

Copy this directory next to `mdlayout.tex`, then run:

```sh
make -f html-build/Makefile html
```

Alternatively:

```sh
html-build/build-html.sh mdlayout.tex mdlayout.html
```

## Word/DOCX build

An editable Microsoft Word document can be generated with:

```sh
make -f html-build/Makefile docx
```

The default output is `mdlayout.docx`. A different source, output file, style,
preamble, or Word reference document can be selected through make variables:

```sh
make -f html-build/Makefile docx \
  SOURCE=mdlayout.tex \
  DOCX_OUTPUT=mdlayout.docx \
  REFERENCE_DOC=mdlayout-reference.docx
```

The DOCX build uses the semantic HTML conversion as an intermediate format.
This retains native Word headings, paragraphs, tables, hyperlinks, images, and
OMML equations. The responsive browser geometry is intentionally flattened to
Word's paged document model. A `REFERENCE_DOC` is optional and can be used to
control Word styles, page dimensions, margins, headers, and footers.

The build reads `mdlayout.sty` beside the source automatically. A differently
named package file can be supplied as the third argument. Its `mdDefault...`
constants, version, and date definitions are expanded into the HTML output.
`mdpreamble.tex` is likewise discovered automatically (or supplied as the
fourth argument); its `mdColor...` RGB definitions are used for the wordmark.

The build consists of two deliberate stages. `mdlayout-preprocess.py` protects
verbatim material and converts the line-oriented `ReferenceTable` syntax into
structured data. Pandoc then converts ordinary LaTeX, while `mdlayout.lua`
creates semantic HTML tables and HTML containers for the custom layout areas.
Finally, `mdlayout-postprocess.py` completes source-positioned directories and
local image handling. `\tableofcontents`, `\listoffigures`, and
`\listoftables` are emitted exactly where they occur in the source.

## Conditional PDF and HTML content

Nested target conditionals are supported. In a LaTeX/PDF build,
`mdlayout.sty` sets `\ifPdf` true and `\ifHtml` false. The HTML preprocessor
selects the complementary branches:

```latex
\ifPdf
  Content only for PDF.
\else
  Content only for HTML.
\fi

\ifHtml
  Additional HTML-only content.
\fi
```

On wide browser windows the stylesheet reproduces the asymmetric area model:
ordinary document blocks occupy `--md-text-area`; `HalfArea` and
`DirectoryArea` extend left by half of `--md-wide-offset`; `FullArea` extends
across `MarginArea`, the gutter, and `TextArea`. `MarginFigure`, `MarginArea`,
`SynchronizedMarginAndTextArea`, wide figures, wide tables, and the `area=`
option of `ReferenceTable` use the same geometry. Below the responsive
breakpoint the areas collapse to one column. The dimensions and breakpoint can
be adjusted near the beginning and end of `mdlayout.css`.

Monospaced material uses the bundled `mdlayout Plex Mono 85` TrueType webfont. Its
glyph outlines and advance widths are both scaled horizontally to reproduce
LaTeX's `FakeStretch=0.85` without crowding. Regenerate it from IBM Plex Mono
with `python3 html-build/make-mono-webfont.py IBMPlexMono-Regular.ttf
html-build/fonts/mdlayout-plex-mono-85.ttf`. The original font's SIL Open
Font License metadata is retained in the derivative.

The build script embeds `mdlayout.css` and the scaled monospaced font directly
in `mdlayout.html`; images remain beside it in the `images` directory.
Mathematics is rendered in the browser through MathJax. The named
pages from the project's `images.pdf` are included as optimized WebP files.
Their order is read from `mdlayout-images-pages.tex`; regenerate them with
`html-build/extract-images.sh images.pdf mdlayout-images-pages.tex`.
Other PDF files referenced directly by `\includegraphics`, such as
`mdlayout-margin-logo.pdf`, are converted automatically to responsive SVG
images when `pdftocairo` is available. A matching SVG already included in
`html-build/images` is reused without requiring conversion tools or the source
PDF. The raster fallback is rendered at high resolution. This avoids the
fixed, framed viewport produced by a browser PDF `<embed>` element without
sacrificing vector sharpness.
