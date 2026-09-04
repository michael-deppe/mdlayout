<!--
%% Copyright 2026 Prof. Dr. Michael Deppe
%%
%%               _ _                         _
%% _ __ ___   __| | | __ _ _   _  ___  _   _| |_
%%| '_ ` _ \ / _` | |/ _` | | | |/ _ \| | | | __|
%%| | | | | | (_| | | (_| | |_| | (_) | |_| | |_
%%|_| |_| |_|\__,_|_|\__,_|\__, |\___/ \__,_|\__|
%%                         |___/
%%
%% mdlayout — Semantic layout framework for technical documentation.
%%
%% This work may be distributed and/or modified under the
%% conditions of the LaTeX Project Public License (LPPL),
%% either version 1.3c of this license or (at your option)
%% any later version.
%%
%% The latest version of this license is available at
%%   https://www.latex-project.org/lppl.txt
%%
%% This work has the LPPL maintenance status `maintained'.
%%
%% The Current Maintainer of this work is
%%   Michael Deppe.
%%
%% This work consists of the files
%%   mdlayout.sty
%%   mdlayout-printout.sty
%%   mdlayout-referencetable.sty
%%   mdpreamble.tex
%%   mdlayout.cwl
%%   mdlayout.md
%%   mdlayout.tex
%%   mdlayout.pdf
%%   mdlayout-margin-logo.pdf
%%   mdlayout.png
%%   images.pdf
%%
-->

<!--
Keep this README intentionally short.

The complete documentation is contained in mdlayout-doc.pdf.
This file should answer only the following questions:

1. What is mdlayout?
2. Why should I use it?
3. How do I start?
-->

# mdlayout

**A semantic layout framework for professional technical documentation with LaTeX.**

`mdlayout` extends LaTeX with semantic layout elements for technical
documentation. Instead of describing *how* document elements should look,
authors describe *what* they represent. The package then chooses an
appropriate visual representation while preserving the logical structure
of the underlying material.

`mdlayout` is intended for manuals, software documentation, technical
reports, system documentation and similar documents containing source
code, terminal sessions, machine-generated output, tables and diagrams.

## Philosophy

Like LaTeX itself, **mdlayout** separates semantics from presentation.

Instead of specifying fonts, widths or formatting details, the author
works with document-oriented building blocks.

For example, a machine printout is fundamentally different from a
source-code listing. Source code may be reformatted to improve
readability, whereas generated output often contains meaningful column
positions and line lengths that should be preserved.

Consequently,

```latex
\begin{Printout}[fitcolumns=132]
	...
\end{Printout}
```

describes the logical width of the output rather than selecting a font
size. The package automatically determines the largest suitable
monospaced font that fits the available print area.

## Features

* Semantic document environments
* Automatic monospaced font scaling
* Machine printouts with configurable forms
* Green-bar and IBM 1403 line-printer layouts
* Plain printouts without graphical decorations
* Full-width layout environments
* Wide tables and wide verbatim areas
* Margin and text synchronization
* Consistent document geometry
* Ready-to-use document preamble (`mdpreamble.tex`)
* Comprehensive documentation with many examples

## Printout Forms

Several predefined printout forms are included.

* `plain` — plain machine output without graphical elements
* `simple` — printout with line bands only
* `green` — classic green-bar paper
* `blue` — blue-bar paper
* `ibm1403` — IBM 1403 continuous stationery

Users may define additional forms using

```latex
\MDDeclarePrintoutForm{<name>}{...}
```

and override individual parameters whenever required.

## Example

```latex
\begin{Printout}[form=green,fitcolumns=132]
	000001  Hello World
	000002  This is a machine printout.
\end{Printout}
```

or

```latex
\begin{Printout}[form=plain,fitcolumns=160]
	...
\end{Printout}
```

## Included Files

The distribution contains

* `mdlayout.sty`
* `mdpreamble.tex`
* complete package documentation
* numerous examples

The documentation itself is produced using **mdlayout** and serves as a
reference implementation for writing larger technical documents.

## Requirements

* LuaLaTeX or XeLaTeX
* KOMA-Script recommended

## Documentation

The complete user manual is provided as `mdlayout-Documentation.pdf` which
can be generated as an example directly from `mdlayout.tex` as `mdlayout.pdf`.

## License

See the LICENSE file included in this distribution.

## Author

Michael Deppe

---

*The goal of **mdlayout** is not to provide another collection of layout
macros. It provides semantic document elements that allow technical
information to be presented in a form that naturally reflects its origin
and purpose.*
