"""Let d(n) be defined as the sum of proper divisors of n (numbers less than n which divide evenly into n).
If d(a) = b and d(b) = a, where a ≠ b, then a and b are an amicable pair and each of a and b are called amicable numbers.

For example, the proper divisors of 220 are 1, 2, 4, 5, 10, 11, 20, 22, 44, 55 and 110; therefore d(220) = 284. The proper divisors of 284 are 1, 2, 4, 71 and 142; so d(284) = 220.

Evaluate the sum of all the amicable numbers under 10000."""

dOfN = [[] for _ in range(10000)]

def dFunction(n, firstRun = True):
    total = -n
    for lowerNumber in range(1,int(n**0.5)+2):
        if n/lowerNumber == float(int(n/lowerNumber)):
            total += int(lowerNumber)
            total += int(n/lowerNumber)
    if firstRun == False:
        return total
    else:
        iteratedTotal = dFunction(total,False)
        if iteratedTotal == n and n != total: 
            return n
        else:
            return 0

totalOfamicable = 0
for x in range(0,10000):
    totalOfamicable += dFunction(x)
print(totalOfamicable)


