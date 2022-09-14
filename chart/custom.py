from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
import psycopg2 
import requests
from datetime import datetime
from bs4 import BeautifulSoup as Bs
import os
from graph.settings import BASE_DIR
from telebot import TeleBot

SAMPLE_SPREADSHEET_ID = ''
SAMPLE_RANGE_NAME = 'ClassData!B2:D'
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR,'chart/token.json')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


TOKEN_TG = ''
CHAT_ID = ''

HOST = ""
DATABASE = ""
USER = ""
PASSWORD = ""



# today's date))
def getTodaysDate() -> str:
    now = datetime.now()
    return now.strftime(r'%d/%m/%Y')

# get price of one dollar in ruble
def getRuble() -> float:
    response = requests.get(f"https://www.cbr.ru/scripts/XML_daily.asp?date_req={getTodaysDate()}")
    soup = Bs(response.content, features='xml')
    ruble = soup.find("Valute", attrs={"ID":"R01235"})
    return float(ruble.find("Value").string.replace(',', '.'))

# get values from google sheet
def getValues() -> list:
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    except:
        creds = None
    if creds != None:
        try:
            service = build('sheets', 'v4', credentials=creds)

            # Call the Sheets API
            sheet = service.spreadsheets()
            result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                        range=SAMPLE_RANGE_NAME).execute()
            data = result.get('values', [])

            if not data:
                print('No data found.')
                return None
            
            # adding new element price_ruble that populates from price_dollar * ruble
            # and check if data is valid
            values = []
            ruble = getRuble()
            for i in data:
                try:
                    #trash check
                    int(i[0])
                    if len(i) == 3 :
                        i.insert(2, round(int(i[1])*ruble, 3))
                        values.append(i)
                except ValueError:
                    continue
            # change each row in list into tuple for further addition to database
            tupled_values = [tuple(x) for x in values]
            return tupled_values
        except HttpError as err:
            raise err
    return None

# to get rows to be deleted from db. working with nested data types.
def format_values(response: list, values: list) -> set:
    if len(response) > 0 and len(values) > 0:

        # getting order_number
        x = [x[0] for x in values]
        # converting str in tuple in list into int in set
        formatted_values = set([int(y) for y in x])

        # converting int in tuple in list into int in set
        formatted_response = set(list(map(list, zip(*response)))[0])

        to_be_deleted = formatted_response.difference(formatted_values)
        return to_be_deleted

# check if date of delivery is expired 
def checkExpiredDate(values: list)  -> list:
    try:
        if values != None:
            current_date = getTodaysDate()
            # convert str into datetime object
            current_date_obj = datetime.strptime(current_date.replace('/', '.'), r'%d.%m.%Y')
            # list of expired orders 
            expired_orders = [value[0] for value in values 
                                    if datetime.strptime(value[3], r'%d.%m.%Y') <= current_date_obj]
            return expired_orders
    except ValueError:
        return None

# send message to telegram chat
def sendMessage(expired_orders: list):
    if expired_orders:
        message = "Expired orders: "
        orders = ', '.join(expired_orders)
        bot = TeleBot(TOKEN_TG)
        bot.send_message(CHAT_ID ,text=message+orders)

# insert values into db
def insertValues(values: list):
    # connecting to db
    connection = psycopg2.connect(
        host = HOST,
        database = DATABASE,
        user = USER,
        password = PASSWORD
    )
    try:
        if values != None:
            with connection.cursor() as cursor:
                # delete function
                #
                # logic is that if some data is stored in db, but not in sheet, 
                # it means that we no longer need to store it
                cursor.execute('SELECT order_number FROM chart_order;')
                response = cursor.fetchall()
                to_be_deleted = format_values(response, values)
                if to_be_deleted:
                    for delete in to_be_deleted:
                        cursor.execute(f"DELETE FROM chart_order WHERE order_number = {delete}")
                        connection.commit()

                # update and insert functions
                #
                # if data exists in db and sheet, just update this particular data
                # if not, insert it
                for value in values:
                    cursor.execute(f"SELECT EXISTS(SELECT order_number FROM chart_order where order_number = {value[0]});")
                    a = cursor.fetchone()
                    if True in a:
                        cursor.execute(f"""UPDATE chart_order SET 
                        price_dollar = {value[1]}, 
                        price_ruble = {value[2]}, 
                        delivery_time = '{value[3]}'
                        WHERE order_number = {value[0]};
                        """)
                        connection.commit()
                    if False in a:
                        cursor.execute(f"INSERT INTO chart_order(order_number, price_dollar, price_ruble, delivery_time) VALUES {value};")
                        connection.commit()
                print(100*'-')
    except Exception as error:
        raise error
    connection.close()
