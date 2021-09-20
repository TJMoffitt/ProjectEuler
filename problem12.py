"""The sequence of triangle numbers is generated by adding the natural numbers. So the 7th triangle number would be 1 + 2 + 3 + 4 + 5 + 6 + 7 = 28. The first ten terms would be:

1, 3, 6, 10, 15, 21, 28, 36, 45, 55, ...

Let us list the factors of the first seven triangle numbers:

 1: 1
 3: 1,3
 6: 1,2,3,6
10: 1,2,5,10
15: 1,3,5,15
21: 1,3,7,21
28: 1,2,4,7,14,28
We can see that 28 is the first triangle number to have over five divisors.

What is the value of the first triangle number to have over five hundred divisors?"""

currentTri, iterNext = 1, 1

while True:
    currentTotal = 2
    lastDivisor = 2
    iterNext += 1
    currentTri += iterNext
    triForDecomp = currentTri
    #currentFactors = [1]
##    while True:
##        if triForDecomp == lastDivisor:
##            currentTotal += 2
##            break
##        elif triForDecomp % lastDivisor == 0:
##            currentTotal += 2
##            triForDecomp = int(triForDecomp/lastDivisor)
##            lastDivisor += 1
##        else:
##            lastDivisor += 1
    while triForDecomp**0.5 >= float(lastDivisor):
        if triForDecomp % lastDivisor == 0:
            currentTotal += 2
            #currentFactors.append(lastDivisor)
        lastDivisor += 1
    
        
    if currentTotal > 500:
        print(str(currentTri),":",str(currentTotal),"-----------")
        break
    #else:
        #print(str(currentTri),":",str(currentTotal))
        #print(currentFactors)
        
        
    
    
    
    
    
    