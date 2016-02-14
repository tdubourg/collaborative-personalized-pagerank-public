#!/bin/bash

f=`find . -name '*.md' | head -n1`
echo "Found file $f to compile..."

# MMD_TEXT_FILES_DIR is where you downloaded https://github.com/fletcher/peg-multimarkdown-latex-support
dir=$MMD_TEX_FILES_DIR
orig=`pwd`

echo "Switching to compilation dir $dir"
cp $f $dir
cp *.png $dir -v
cp *.jpg $dir -v
cp *.gif $dir -v
cp *.tex $dir -v
cd $dir

echo "Compiling to TeX..."
multimarkdown --to=latex $f > "$f.tex"

# Generate a file with line returns, that we will use as stdin input
# to pdflatex to tell him go fuck itself
echo "" > /tmp/lines.txt
for i in `seq 200`; do \
echo "" >> /tmp/lines.txt; \
done

echo "Compiling to PDF..."
if pdflatex "$f.tex" < /tmp/lines.txt; then
	echo "PDF compiled with success. "
else
	echo "PDF Compilation failed"
fi

echo "Opening PDF..."
cp "${f}.pdf" "${orig}/"

echo "Switching back to original directory $orig"
cd $orig

evince "$f.pdf" & 

