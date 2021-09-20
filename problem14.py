"""The following iterative sequence is defined for the set of positive integers:

n → n/2 (n is even)
n → 3n + 1 (n is odd)

Using the rule above and starting with 13, we generate the following sequence:

13 → 40 → 20 → 10 → 5 → 16 → 8 → 4 → 2 → 1
It can be seen that this sequence (starting at 13 and finishing at 1) contains 10 terms. Although it has not been proved yet (Collatz Problem), it is thought that all starting numbers finish at 1.

Which starting number, under one million, produces the longest chain?

NOTE: Once the chain starts the terms are allowed to go above one million."""

totalLengths = [False]*1000000
totalLengths[0] = 1
for n in range(0,1000000):
    iterations = 0
    nTemp = n + 1
    while totalLengths[nTemp] == False and nTemp != 1:
        if nTemp%2 == 0:
            nTemp = int(nTemp/2)
            iterations += 1
        else:
            nTemp = 3*nTemp + 1
            iterations += 1
    totalLengths[n] = totalLengths[nTemp] + iterations
    print(n)
    print(totalLengths[0:20])
