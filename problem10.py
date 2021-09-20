"""The sum of the primes below 10 is 2 + 3 + 5 + 7 = 17.

Find the sum of all the primes below two million."""

primeArray = [1]*2000000
for x in range(1,2000000):
    if primeArray[x] == 1:
        iteration = 2
        while iteration*(x+1) <= 2000000:
            primeArray[iteration*(x+1)-1] = 0
            iteration += 1
sumTotal = -1 # One is not a prime number, so we start at -1
for xVal, x in enumerate(primeArray, start = 1):
    if x == 1:
        sumTotal += xVal
print(sumTotal)
            
