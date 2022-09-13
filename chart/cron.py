
from chart.custom import getValues, insertValues, checkExpiredDate, sendMessage

def insert():
    values = getValues()
    insertValues(values) 

def check():
    values = getValues()
    expired_orders = checkExpiredDate(values)
    sendMessage(expired_orders)
