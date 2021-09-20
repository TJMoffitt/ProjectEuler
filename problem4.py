"""A palindromic number reads the same both ways. The largest palindrome made from the product of two 2-digit numbers is 9009 = 91 × 99.

Find the largest palindrome made from the product of two 3-digit numbers."""

numOne = 999
numTwo = 999
currentLargest = 1

while True:
    if str(numOne * numTwo) == str(numOne * numTwo)[::-1] and numOne * numTwo > currentLargest:     
        currentLargest = numOne * numTwo
    if numOne*999 < currentLargest:
        break
    if numOne == numTwo:
        numOne -= 1
        numTwo = 999
    else:
        numTwo -= 1

    

print(currentLargest)
