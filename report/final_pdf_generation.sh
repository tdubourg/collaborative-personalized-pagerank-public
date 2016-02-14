#!/bin/bash

# Note: We first remove all files related to the report, bibliography, TOC, etc...
# Then we run the compilation twice, so that references and ToC are generated
# But not a single more time! Indeed, starting at the 3rd compilation, LateX will add
# stupid weird wtf numbers at the end of the bibliography that are suppsoed to be the
# backreferences to where the bib references have been quoted by LateX puts them all
# at the end and in the end (pun?) it's just a complete mess, so we do not want that
rm -vf $MMD_TEX_FILES_DIR/CPPR.md* && ./compile.sh&& ./compile.sh

