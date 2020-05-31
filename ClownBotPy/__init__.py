import json

with open("config.json") as f:
    configData = json.load(f)

# Default Values
defaultFunnyCreditScore = 500
defaultFunnyTransactions = 5
defaultFunnyWage = 11
account_keys = [
    "_id",
    "User",
    "User ID",
    "Balance",
    "Funny Credit Score",
    "Daily Funny Transactions",
    "Funny Wage",
    "Funny Worked",
]
