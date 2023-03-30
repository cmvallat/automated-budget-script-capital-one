import mintapi
import pandas as pd
import gspread
from df2gspread import df2gspread as d2g
from oauth2client.service_account import ServiceAccountCredentials
from config import mintUsername, mintPassword

# def next_available_row(worksheet):
#     str_list = list(filter(None, worksheet.col_values(1)))
#     return str(len(str_list)+1)

def colorTextGreen():

    print("hello")

mint = mintapi.Mint(
    email = mintUsername,  # Email used to log in to Mint
    password = mintPassword,  # Your password used to log in to mint
 
    # Optional parameters
    # mfa_method='sms',  # Can be 'sms' (default), 'email', or 'soft-token'.
    #                    # if mintapi detects an MFA request, it will trigger the requested method
    #                    # and prompt on the command line.
    # headless=False,  # Whether the chromedriver should work without opening a
    #                  # visible window (useful for server-side deployments)
    # mfa_input_callback=None,  # A callback accepting a single argument (the prompt)
    #                           # which returns the user-inputted 2FA code. By default
    #                           # the default Python `input` function is used.
    # session_path=None, # Directory that the Chrome persistent session will be written/read from.
    #                    # To avoid the 2FA code being asked for multiple times, you can either set
    #                    # this parameter or log in by hand in Chrome under the same user this runs
    #                    # as.
    # imap_account=None, # account name used to log in to your IMAP server
    # imap_password=None, # account password used to log in to your IMAP server
    # imap_server=None,  # IMAP server host name
    # imap_folder='INBOX',  # IMAP folder that receives MFA email
    wait_for_sync=True,  # do not wait for accounts to sync
    # wait_for_sync_timeout=300,  # number of seconds to wait for sync
)

#change date range each time to only get newest posted transactions
transactions = mint.get_transaction_data(start_date = "03-20-23", end_date = "03-22-23")

#check that we recieved the transactions
if(transactions):
    print("\n")
    print("recieved transactions, prepping data and converting to dataframe")
    print("\n")

transformed_transactions_desc = []
transformed_transactions_amt = []
categories = {'rent':0, 'groceries':0}

#take each transaction, get vendor and price and map certain values
transactionCounter = 1
paymentRows = []
for transaction in transactions:

    #map common transactions and add to known categories
    if "king soopers" in transaction['description'].lower():
        transaction['description'] = "KS"
        categories["groceries"] += round((transaction['amount'] * -1),2)
    if "hellolanding.com" in transaction['description'].lower():
        transaction['description'] = "Rent"
        categories["rent"] += round((transaction['amount'] * -1),2)
    if( (transaction['amount'] * -1) < 0):
            paymentRows.append(transactionCounter)

    transformed_transactions_desc.append(transaction['description'].title())
    transformed_transactions_amt.append(str(round((transaction['amount'] * -1),2)))
    transactionCounter += 1

#format categories
cat_keys = []
cat_values = []
for cat in categories:
   cat_keys.append(cat)
   cat_values.append(categories[cat])

#convert transactions to pandas dataframe so we can write to the Google Sheet
transactions_df = pd.DataFrame(list(zip(transformed_transactions_desc, transformed_transactions_amt)), columns=['vendor', 'price'])
if(str(type(transactions_df)) == "<class 'pandas.core.frame.DataFrame'>"):
    print("converted transactions to dataframe correctly, ready to upload")
    print("\n")

#convert categories to pandas dataframe so we can write to the Google Sheet
categories_df = pd.DataFrame(list(zip(cat_keys, cat_values)), columns=['category', 'amount'])
if(str(type(categories_df)) == "<class 'pandas.core.frame.DataFrame'>"):
    print("converted categories to dataframe correctly, ready to upload")
    print("\n")

# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials_mint.json', scope)
client = gspread.authorize(creds)

#next_row = next_available_row(worksheet)x

# Setup for google sheets
spreadsheet_key = "1cjuu9-vOJzKbV9sMBtibIfAjKseW8HACmdxa2z_bAdg"
sh = client.open_by_key(spreadsheet_key).sheet1

#write transaction rows to google sheets
trans_values = transactions_df.values.tolist()
sh.append_rows(trans_values)
print("uploaded transactions, check Google Sheet")
print("\n")

#write category rows to google sheets
cat_values = categories_df.values.tolist()
sh.append_rows(cat_values)
print("uploaded categories, check Google Sheet")
print("\n")

#make all cells red as default
sh.format("A1:B" + str(transactionCounter), {
        "textFormat": {
        "foregroundColor": {
            "red": 1.0,
            "green": 0.0,
            "blue": 0.0
        },
        }
    })

if not paymentRows:
    print("paymentRows is null")
#make payment transactions green
for row in paymentRows:
    formatString = "A" + str(row) + ":B" + str(row)
    print(formatString)
    sh.format(formatString, {
        "textFormat": {
        "foregroundColor": {
            "red": 0.0,
            "green": 11.0,
            "blue": 0.0
        },
        }
    })





#d2g.upload(transactions_df,spreadsheet_key,"Sheet1",credentials=creds,row_names=True)
#.format(next_row)



# gc = gspread.service_account()
#df = pd.DataFrame({'Name': ['Bea', 'Andrew', 'Mike'], 'Age': [20, 19, 23]})


# worksheet = client.open("Testing Budget API").sheet1

#insert on the next available row

#worksheet.update_acell("B{}".format(next_row), "rent")
# worksheet.update_acell("C{}".format(next_row), 56)

# d2g.upload(categories_df,spreadsheet_key,"Sheet1",credentials=creds,row_names=True, start_cell="A170")
# print("uploaded categories, check Google Sheet")
# print("\n")