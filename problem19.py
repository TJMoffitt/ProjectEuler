"""You are given the following information, but you may prefer to do some research for yourself.

1 Jan 1900 was a Monday.
Thirty days has September,
April, June and November.
All the rest have thirty-one,
Saving February alone,
Which has twenty-eight, rain or shine.
And on leap years, twenty-nine.
A leap year occurs on any year evenly divisible by 4, but not on a century unless it is divisible by 400.
How many Sundays fell on the first of the month during the twentieth century (1 Jan 1901 to 31 Dec 2000)?"""

daysinmonth = [31,28,31,30,31,30,31,31,30,31,30,31]
daysinmonthLeapYear = [31,29,31,30,31,30,31,31,30,31,30,31]

currentdate = [1901,1,1]
currentDay = 2
totalSundays = 0

#Refactor this...
while currentdate != [2000,12,31]:
    currentDay += 1
    if currentdate[1] == 12 and currentdate[2] == 31:
        currentdate[0] += 1; currentdate[1] = 1; currentdate[2] = 1
    elif currentdate[0]%4 == 0 and currentdate[2] == daysinmonthLeapYear[currentdate[1]-1]:
        currentdate[1] += 1
        currentdate[2] = 1
    elif currentdate[2] == daysinmonth[currentdate[1]-1]:
        currentdate[1] += 1
        currentdate[2] = 1    
    else:
        currentdate[2] += 1
    if currentDay == 7:
        if currentdate[2] == 1:
            totalSundays += 1
        currentDay = 0
print(totalSundays)
        
