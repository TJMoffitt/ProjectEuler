"""By listing the first six prime numbers: 2, 3, 5, 7, 11, and 13, we can see that the 6th prime is 13.

What is the 10 001st prime number?"""

currentlyChecking = 2
primes = [2]; totalPrimes = 1

while True:
    currentlyChecking += 1
    for primeCount, prime in enumerate(primes, start = 1):
        if currentlyChecking % prime == 0:
            break
        elif primeCount == totalPrimes:
            totalPrimes += 1; primes.append(currentlyChecking)
            break
    if totalPrimes == 10001:
        print(primes[10000])
        break

            
