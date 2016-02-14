#!/bin/bash

gzip -d top_300_queries_with_non_null_clustering.lst.gz -c | grep -vE \
"( girls|girls |sex | sex| teen|teen | nude|nude |porn| cams? |blow job| suck.?|suck.? |^suck.?$| \
penis|penis |^penis$|clitoris?| gay|masturbation|bea?stiality|vaginas? | vaginas?|^vaginas?\$|erection|naturist\
|escorts|beautiful agony|bang.+wife|glory hole|sexual|^rape$| rape|rape | incest|incest |pussy|lolita| ass(es)?|\
ass(es)? |^ass(es)?$|^escorts?$| butts?$| butts? |butts? |hot.+wife|up skirt| mature|mature )\
"\
 > top_300_queries_with_non_null_clustering_filtered_manually.lst
