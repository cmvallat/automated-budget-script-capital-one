from datetime import datetime as dt

date = dt.now()

print(date)

truncated_date = str(date.month) + "-" + str(date.day) + "-" + str(date.year)

print(truncated_date)

