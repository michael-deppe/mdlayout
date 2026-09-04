.PHONY: html docx clean

SOURCE ?= mdlayout.tex
OUTPUT ?= mdlayout.html
DOCX_OUTPUT ?= mdlayout.docx
STYLE ?= $(firstword $(wildcard $(dir $(SOURCE))mdlayout.sty))
PREAMBLE ?= $(firstword $(wildcard $(dir $(SOURCE))mdpreamble.tex))
REFERENCE_DOC ?=

html:
	./html-build/build-html.sh "$(SOURCE)" "$(OUTPUT)"
	cp html-build/mdlayout.css "$(dir $(OUTPUT))mdlayout.css"
	cp -R html-build/images "$(dir $(OUTPUT))"

docx:
	./html-build/build-docx.sh "$(SOURCE)" "$(DOCX_OUTPUT)" "$(STYLE)" "$(PREAMBLE)" "$(REFERENCE_DOC)"

clean:
	rm -f "$(OUTPUT)" "$(DOCX_OUTPUT)"
