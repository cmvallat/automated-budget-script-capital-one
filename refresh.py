import mintapi
import pandas as pd
import gspread
from df2gspread import df2gspread as d2g
from oauth2client.service_account import ServiceAccountCredentials
from config import mintUsername, mintPassword
from datetime import datetime as dt

# use creds to create a client to interact with the Google Drive API
# eventually pass in these credentials and other params as inputs when running the script
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials_mint.json', scope)
client = gspread.authorize(creds)

# Setup for google sheets
spreadsheet_key = "1cjuu9-vOJzKbV9sMBtibIfAjKseW8HACmdxa2z_bAdg"
sh = client.open_by_key(spreadsheet_key).sheet1

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

#filtering date here with start_date doesn't work so we do it below
transactions = mint.get_transaction_data()

#check that we recieved the transactions
if(transactions):
    print("\n")
    print("recieved transactions, prepping data and converting to dataframe")
    print("\n")

transformed_transactions_desc = []
transformed_transactions_amt = []
transformed_transactions_date = []
categories = {'rent':0, 'groceries':0}
sh.update('A1', "Transactions since 04/01:")

#take each transaction, get vendor and price and map certain values
transactionCounter = 0
paymentRows = []
for transaction in transactions:
    # print(transaction['date'])
    trans_date = dt.strptime(transaction['date'], "%Y-%m-%d")
    cutoff_date = dt.strptime("2023-04-01", "%Y-%m-%d")
    if trans_date >= cutoff_date:
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
        truncated_date = str(trans_date.month) + "-" + str(trans_date.day) + "-" + str(trans_date.year)
        transformed_transactions_date.append(truncated_date)
        transactionCounter += 1

#format categories
cat_keys = []
cat_values = []
for cat in categories:
   cat_keys.append(cat)
   cat_values.append(categories[cat])

#convert transactions to pandas dataframe so we can write to the Google Sheet
transactions_df = pd.DataFrame(list(zip(transformed_transactions_desc, transformed_transactions_amt, transformed_transactions_date)), columns=['vendor', 'price', 'date'])
if(str(type(transactions_df)) == "<class 'pandas.core.frame.DataFrame'>"):
    print("converted transactions to dataframe correctly, ready to upload")
    print("\n")

#convert categories to pandas dataframe so we can write to the Google Sheet
categories_df = pd.DataFrame(list(zip(cat_keys, cat_values)), columns=['category', 'amount'])
if(str(type(categories_df)) == "<class 'pandas.core.frame.DataFrame'>"):
    print("converted categories to dataframe correctly, ready to upload")
    print("\n")

#insert line here to clear the google sheet first with every refresh

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
sh.format("A2:B" + str(transactionCounter+1), {
         "backgroundColor": {
            "red": float((244/255)),
            "green": float((204/255)),
            "blue": float((204/255))
        }
    })

if not paymentRows:
    print("paymentRows is null")
#make payment transactions green
for row in paymentRows:
    formatString = "A" + str(row+2) + ":B" + str(row+2)
    sh.format(formatString, {
        "backgroundColor": {
            "red": float((217/255)),
            "green": float((234/255)),
            "blue": float((211/255))
        }
    })

print("formatted cells correctly")


#Useful documentation

#how to set a cell value to formula:
# sh.update('E3', "=FILTER(A1:C, DATEVALUE(C1:C) >= DATE(2023,3,24))", raw=False)
