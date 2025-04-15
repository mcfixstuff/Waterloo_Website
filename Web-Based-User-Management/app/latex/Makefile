# List all the .tex files to compile.
TEXFILES = course_drop.tex special_circumstance.tex

# Automatically derive the PDF file names from the TEX files.
PDFFILES = $(TEXFILES:.tex=.pdf)

# The default target "all" depends on all the PDF files.
all: $(PDFFILES)

# Pattern rule: For any .tex file, run pdflatex twice to generate the corresponding .pdf.
%.pdf: %.tex
	pdflatex -interaction=nonstopmode -halt-on-error $<
	pdflatex -interaction=nonstopmode -halt-on-error $<

# Clean up generated files.
clean:
	rm -f $(PDFFILES) *.aux *.log *.out

