#!/bin/zsh

clear;

basename=$1

for i in $basename*; do \
    tmp="${i}.old"; \
    cp $i $tmp -v; \
    # gzip -d $tmp -c | perl -0 -pe "s/^\{\n,/{\n/g" | gzip > $i; \ too heavy when the file is hundreds of megs...
    uncompressed=${tmp}.uncompressed; \
    echo "Decompressing to ${uncompressed}..."; \
    gzip -d $tmp -c > ${uncompressed}; \
    echo "Converting..."; \
    head $uncompressed -n2 | perl -0 -pe "s/^\{\n,/{\n/g" > temp_blorg; \
    tail $uncompressed -n+3 >> temp_blorg ; \
    rm -vf $uncompressed &; \
    echo "Recompressing..."; \
    gzip -6 -f temp_blorg -c > $i; \
done
rm -vf temp_blorg