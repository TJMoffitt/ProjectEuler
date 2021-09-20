"""Starting in the top left corner of a 2×2 grid, and only being able to move to the right and down, there are exactly 6 routes to the bottom right corner.


How many such routes are there through a 20×20 grid?"""

# Total Number of arrays [R,D,R,D .... D, D, R] of len 40 such that N(R) = N(D) = 20.
# Simple Combinatorics Problem, no code needed.

import math

print(int(math.factorial(40)/math.factorial(20)**2))
