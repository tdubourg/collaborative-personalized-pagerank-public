#!/usr/bin/python
import sys

""" 
This file is used to be able to manipulate the "number of clicks"
data in a spreadsheet because just having the number of clicks
for every user was killing both LibreOffice and Excel as it was
basically hundreds of thousands of points to plot...

Here instead we display the number of user for every possible "number
of clicks" value. There still are a lot of value but this time it is
acceptable. Moreover, this is what we are interested in in fact in the
end anyway: the distribution of the "number of clicks" values in terms
of number of users

"""

# Here we are converting from a mapping user_id -> number of clicks
# To a mapping number of clicks -> number of users with this number of clicks
f = open(sys.argv[1])
res = [0] * 279431
for l in f:
    a, b = l.strip().split(',')
    res[int(b)] += 1

output_path = 'aggregated.txt' if len(sys.argv) < 3 else sys.argv[2].strip()

o = open(output_path, 'w')
o.writelines('\n'.join(["%s,%s" % (i, res[i]) for i in xrange(0, len(res)) if res[i] is not 0]))