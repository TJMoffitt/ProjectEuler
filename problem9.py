"""A Pythagorean triplet is a set of three natural numbers, a < b < c, for which,

a^2 + b^2 = c^2
For example, 3^2 + 4^2 = 9 + 16 = 25 = 5^2.

There exists exactly one Pythagorean triplet for which a + b + c = 1000.
Find the product abc."""


for a in range(1,999):
    for b in range(1,999-a):
        if a**2 + b**2 == (1000-a-b)**2:
            print(str(a)+"^2 +", str(b)+"^2 =", str(1000-a-b)+"^2")
            print(a*b*(1000-a-b))
        
