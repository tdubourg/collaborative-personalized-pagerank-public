#!/usr/bin/python

pages_in_color = [89, 90, 91, 94, 95, 104, 105, 107, 108]

tot_pages = 122

# Recto pages are the odd-numbered pages
recto_pages = [i for i in xrange(1, tot_pages + 1) if i % 2 and i not in pages_in_color]


print "Recto pages:\n", recto_pages
print "\n/!\\ /!\\ Before printing verso. Do not forget to check if you need to add" + \
        "blank sheets for pages on same paper sheet as:\n", pages_in_color
print "\nVerso pages:\n", [_ for _ in range(1, tot_pages + 1) if _ not in (recto_pages + pages_in_color)]
