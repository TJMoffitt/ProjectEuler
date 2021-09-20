""" The prime factors of 13195 are 5, 7, 13 and 29.

What is the largest prime factor of the number 600851475143 ?"""

import math

def largestPrimeFactor(number):
    primeCheck = 2
    while primeCheck <= int(math.ceil(number**0.5)):
        if isPrime(primeCheck) and number % primeCheck == 0:
            number = number / primeCheck
        else:
            primeCheck += 1
    return int(number)
            

def isPrime(number):
    for x in range(2, int(math.ceil(number**0.5)) ):
        if number % x == 0:
            return False
    return True

print(largestPrimeFactor(13195))
print(largestPrimeFactor(600851475143))
