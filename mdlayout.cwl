# ============================================================

# mdlayout.cwl

## Copyright 2026 Prof. Dr. Michael Deppe
##
##               _ _                         _
## _ __ ___   __| | | __ _ _   _  ___  _   _| |_
##| '_ ` _ \ / _` | |/ _` | | | |/ _ \| | | | __|
##| | | | | | (_| | | (_| | |_| | (_) | |_| | |_
##|_| |_| |_|\__,_|_|\__,_|\__, |\___/ \__,_|\__|
##                         |___/
##
## mdlayout — Semantic layout framework for technical documentation.
##
## This work may be distributed and/or modified under the
## conditions of the LaTeX Project Public License (LPPL),
## either version 1.3c of this license or (at your option)
## any later version.
##
## The latest version of this license is available at
##   https://www.latex-project.org/lppl.txt
##
## This work has the LPPL maintenance status `maintained'.
##
## The Current Maintainer of this work is
##   Michael Deppe.
##
## This work consists of the files
##   mdlayout.sty
##   mdlayout-printout.sty
##   mdlayout-referencetable.sty
##   mdpreamble.tex
##   mdlayout.cwl
##   mdlayout.md
##   mdlayout.tex
##   mdlayout.pdf
##   mdlayout-margin-logo.pdf
##   mdlayout.png
##   images.pdf
##

# ============================================================

# Version
\mdlayoutVersion
\mdlayoutRevisionNumber
\mdlayoutPrintoutVersion
\mdlayoutReferenceTableVersion
\mdlayout{}

# ------------------------------------------------------------
# Package
# ------------------------------------------------------------

\usepackage{mdlayout}
\usepackage[marginwidth=•]{mdlayout}
\usepackage[gutter=•]{mdlayout}
\usepackage[rightmargin=•]{mdlayout}
\usepackage[bottommargin=•]{mdlayout}
\usepackage[wideheadings=•]{mdlayout}
\usepackage[wideheadfoot=•]{mdlayout}
\usepackage[headsepline=•]{mdlayout}
\usepackage[plainheadsepline=•]{mdlayout}

\usepackage[chapterrule=•]{mdlayout}
\usepackage[sectionrule=•]{mdlayout}
\usepackage[headingrulecolor=•]{mdlayout}
\usepackage[chapterrulegap=•]{mdlayout}
\usepackage[showlayout=•]{mdlayout}
\usepackage[articletitlerule=•]{mdlayout}
\usepackage[articletitlerulegap=•]{mdlayout}
\usepackage[widetitle=•]{mdlayout}

# ------------------------------------------------------------
# Public dimensions
# ------------------------------------------------------------

\mdTextWidth
\mdFullWidth
\mdMarginWidth
\mdGutterWidth
\mdWideOffset
\mdRightMargin
\mdBottomMargin
\mdHalfOffset
\mdHalfWidth

\mdFullLeft
\mdFullRight
\mdMarginLeft
\mdMarginRight
\mdTextLeft
\mdTextRight

# Compatibility dimensions

\fullwidth
\marginwidth
\gutterwidth
\wideoffset
\megatextindent
\textindent

# ------------------------------------------------------------
# signs
# ------------------------------------------------------------

\mdSeeRight

# ------------------------------------------------------------
# Area environments
# ------------------------------------------------------------

\begin{FullArea}
\end{FullArea}

\begin{HalfArea}
\end{HalfArea}

\begin{widearea}
\end{widearea}

\begin{MarginArea}
\end{MarginArea}

\begin{marginarea}
\end{marginarea}

\begin{DirectoryArea}
\end{DirectoryArea}

# ------------------------------------------------------------
# Wide longtable context
# ------------------------------------------------------------

\begin{widelongtable}
\end{widelongtable}

# ------------------------------------------------------------
# Centering environments
# ------------------------------------------------------------

\begin{FullCenter}
\end{FullCenter}

\begin{widecenter}
\end{widecenter}

\begin{MarginCenter}
\end{MarginCenter}

\begin{margincenter}
\end{margincenter}

# ------------------------------------------------------------
# Wide floats
# ------------------------------------------------------------

\begin{widefigure}
\end{widefigure}

\begin{widefigure}[•]
\end{widefigure}

\begin{widetable}
\end{widetable}

\begin{widetable}[•]
\end{widetable}

# ------------------------------------------------------------
# MarginFigure
# ------------------------------------------------------------

\begin{MarginFigure}
\end{MarginFigure}

\begin{MarginFigure}[•]
\end{MarginFigure}

# ------------------------------------------------------------
# SyncMarginAndTextArea
# ------------------------------------------------------------

\SyncMarginAndTextArea

# ------------------------------------------------------------
# Printout
# ------------------------------------------------------------

\begin{Printout}#V
\end{Printout}#V

\begin{Printout}[•]#V
\end{Printout}#V

# Printout option templates
\begin{Printout}[form=•]#V
\begin{Printout}[paperheight=•]#V
\begin{Printout}[bandlines=•]#V
\begin{Printout}[bandcolor=•]#V
\begin{Printout}[feedlines=•]#V
\begin{Printout}[fitcolumns=•]#V
\begin{Printout}[punchholes=•]#V
\begin{Printout}[linenumbers=•]#V
\begin{Printout}[fontsize=•]#V

# Common Printout values
\begin{Printout}[form=green]#V
\begin{Printout}[form=blue]#V
\begin{Printout}[punchholes=true]#V
\begin{Printout}[punchholes=false]#V
\begin{Printout}[linenumbers=true]#V
\begin{Printout}[linenumbers=false]#V


# ------------------------------------------------------------
# ReferenceTable
# ------------------------------------------------------------

\begin{ReferenceTable}[•]
\end{ReferenceTable}

# ReferenceTable option templates
\begin{ReferenceTable}[area=•]
\begin{ReferenceTable}[caption={•}]
\begin{ReferenceTable}[label={•}]
\begin{ReferenceTable}[columns=•]
\begin{ReferenceTable}[headers=•]
\begin{ReferenceTable}[header=•]
\begin{ReferenceTable}[xcolumn=•]
\begin{ReferenceTable}[xcolumns=•]
\begin{ReferenceTable}[typewritercolumn=•]
\begin{ReferenceTable}[typewritercolumns=•]
\begin{ReferenceTable}[verbatimcolumn=•]
\begin{ReferenceTable}[verbatimcolumns=•]
\begin{ReferenceTable}[leftcolumn=•]
\begin{ReferenceTable}[leftcolumns=•]
\begin{ReferenceTable}[centercolumn=•]
\begin{ReferenceTable}[centercolumns=•]
\begin{ReferenceTable}[rightcolumn=•]
\begin{ReferenceTable}[rightcolumns=•]
\begin{ReferenceTable}[trimleadingspaces=•]
\begin{ReferenceTable}[tabspaces=•]

# Common ReferenceTable values
\begin{ReferenceTable}[area=full]
\begin{ReferenceTable}[area=half]
\begin{ReferenceTable}[area=text]
\begin{ReferenceTable}[headers=arguments]
\begin{ReferenceTable}[headers=row]
\begin{ReferenceTable}[headers=none]
\begin{ReferenceTable}[headers=false]
\begin{ReferenceTable}[header=true]
\begin{ReferenceTable}[header=false]
\begin{ReferenceTable}[trimleadingspaces=true]
\begin{ReferenceTable}[trimleadingspaces=false]
\begin{ReferenceTable}[tabspaces=1]

# ------------------------------------------------------------
# Public commands
# ------------------------------------------------------------

\fullcenter{•}
\marginbox{•}

\fullrule
\fullrule[•]

\mdlayoutrecalculate
\ShowMDLayout

\company{•}

# ------------------------------------------------------------
# Useful length operations
# ------------------------------------------------------------

\setlength{\fullwidth}{•}
\setlength{\marginwidth}{•}
\setlength{\gutterwidth}{•}
\setlength{\wideoffset}{•}
\setlength{\megatextindent}{•}
\setlength{\textindent}{•}

\the\mdTextWidth
\the\mdFullWidth
\the\mdMarginWidth
\the\mdGutterWidth
\the\mdWideOffset
\the\mdRightMargin
\the\mdBottomMargin
\the\mdHalfOffset
\the\mdHalfWidth

\the\mdFullLeft
\the\mdFullRight
\the\mdMarginLeft
\the\mdMarginRight
\the\mdTextLeft
\the\mdTextRight

\the\fullwidth
\the\marginwidth
\the\gutterwidth
\the\wideoffset
\the\megatextindent
\the\textindent

# ------------------------------------------------------------
# Other area environments
# ------------------------------------------------------------

\begin{wideverbatim}#V
\end{wideverbatim}#V

\begin{grayverbatim}#V
\end{grayverbatim}#V

\begin{graywideverbatim}#V
\end{graywideverbatim}#V

\begin{listing}#V
\end{listing}#V

\code{verbatimSymbol}#S

\begin{licensedisplay}
\end{licensedisplay}

\begin{licensedisplayVerbatim}#V
\end{licensedisplayVerbatim}#V

