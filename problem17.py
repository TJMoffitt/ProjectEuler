"""If the numbers 1 to 5 are written out in words: one, two, three, four, five, then there are 3 + 3 + 5 + 4 + 4 = 19 letters used in total.

If all the numbers from 1 to 1000 (one thousand) inclusive were written out in words, how many letters would be used?


NOTE: Do not count spaces or hyphens. For example, 342 (three hundred and forty-two) contains 23 letters and 115 (one hundred and fifteen) contains 20 letters. The use of "and" when writing out numbers is in compliance with British usage.

"""

#thousands = ["","onethousand","twothousand","threethousand","fourthousand","fivethousand","sixthousand","seventhousand","eightthousand","ninethousand"]
hundreds = ["","onehundred","twohundred","threehundred","fourhundred","fivehundred","sixhundred","sevenhundred","eighthundred","ninehundred"]
tens = ["","","twenty","thirty","forty","fifty","sixty","seventy","eighty","ninety"]
teens = ["ten","eleven","twelve","thirteen","fourteen","fifteen","sixteen","seventeen","eighteen","nineteen"]
digits = ["","one","two","three","four","five","six","seven","eight","nine"]

startCount = len("onethousand")

for x in range(0,1000):
    x = str(x).rjust(4,"0")
    string = ""
    string += thousands[int(str(x)[0])]+hundreds[int(str(x)[1])]
    if (int(str(x)[0]) != 0 or int(str(x)[1]) != 0 ) and (int(str(x)[2]) != 0 or int(str(x)[3]) != 0):
        string += "and"
    if int(str(x)[2]) == 1:
        string += teens[int(str(x)[3])]
    else:
        string += tens[int(str(x)[2])]+digits[int(str(x)[3])]
    startCount += len(string)
print(startCount)

