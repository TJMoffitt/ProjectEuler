"""2520 is the smallest number that can be divided by each of the numbers from 1 to 10 without any remainder.

What is the smallest positive number that is evenly divisible by all of the numbers from 1 to 20?"""


 
start = 1*2*3*5*7*11*13*17*19 # LCM of prime factors of our number
solutionFound = False
while solutionFound == False:
    start += 1*2*3*5*7*11*13*17*19 # number must be divisible by all prime numbers under 20 and so must be divisible by its product. This means we must only check those numbers which are a multiple of this product.
    for x in range(2,21):
        if start % x != 0:
            break
        elif x == 20:
            solutionFound = True
print(start)
    
            
