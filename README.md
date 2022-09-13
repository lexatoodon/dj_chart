# dj_chart
A simple webpage that parses google sheets and displays graph with Chart.js.
google sheets: https://docs.google.com/spreadsheets/d/1CgMurPJ3lz4e9R7JyAdfCgh9z3MHP8_X1ZM2Z7sQBbY
The custom script is located in custom.py.
The job scheduler is django-crontab. (If django-crontab is not working, use "sudo service crontab start"). 
The main script works every 2 minutes. The message sender works every day at 00:01.

How the script works:
1) Getting values from sheets,
2) Adding new column "price in ruble"(the exchange rate is taken from https://www.cbr.ru/currency_base/daily/),
3) Saving everything in the PostgreSQL database.

Message sender:
1) If column "срок поставки" is expired, the script sends a message to telegram chat
