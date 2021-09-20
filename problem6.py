sumOfSquares = 0
squareOfSums = 0

for x in range(1,101):
    sumOfSquares += x**2
    squareOfSums += x
squareOfSums = squareOfSums**2
print(squareOfSums - sumOfSquares)
