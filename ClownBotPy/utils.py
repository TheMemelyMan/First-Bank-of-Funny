from ClownBotPy.db import dbFirstBankOfFunny
from ClownBotPy import (
    defaultFunnyWage,
    defaultFunnyCreditScore,
    defaultFunnyTransactions,
    account_keys,
)


def getAccount(userID, serverID):
    queueUp = dbFirstBankOfFunny[str(serverID)]
    account = queueUp.find_one({"User ID": userID})
    if account:
        checkIfAccountHasAllFields(serverID, account)
    return account


def checkIfAccountExists(userID, serverID):
    return getAccount(userID, serverID) is not None


def updateBalance(
    serverID, account, balanceDiff: int, countsAsTransaction: bool
):
    queueUp = dbFirstBankOfFunny[str(serverID)]

    balance = int(account["Balance"])
    trans = int(account["Daily Funny Transactions"])
    query = {"_id": account["_id"]}
    newBalance = {"$set": {"Balance": balance + balanceDiff}}

    if countsAsTransaction:
        newTrans = {"$set": {"Daily Funny Transactions": trans - 1}}
        queueUp.find_one_and_update(query, newTrans)

    queueUp.find_one_and_update(query, newBalance)


def updateTransactions(serverID, account):
    queueUp = dbFirstBankOfFunny[str(serverID)]

    query = {"_id": account["_id"]}
    newTrans = {"$set": {"Daily Funny Transactions": 5}}

    queueUp.find_one_and_update(query, newTrans)


def updateFunnyWorked(serverID, account, funnyWorked: int):
    queueUp = dbFirstBankOfFunny[str(serverID)]

    query = {"_id": account["_id"]}
    worked = int(account["Funny Worked"])
    newWorked = {"$set": {"Funny Worked": worked + funnyWorked}}

    try:
        queueUp.find_one_and_update(query, newWorked)
    except Exception as e:
        print(e)


def checkIfAccountHasAllFields(serverID, account):
    cursor = dbFirstBankOfFunny[str(serverID)]
    keys = account_keys
    query = {"_id": account["_id"]}
    to_add = {}
    for key in keys:
        if key not in account.keys():
            to_add[str(key)] = calcNewDefaultForMissingField(
                account, keys.index(key)
            )
    if to_add is not {}:
        try:
            newValue = {"$set": to_add}
            cursor.find_one_and_update(query, newValue)
        except Exception as e:
            print(e)


def calcNewDefaultForMissingField(account, key):
    # print("Got to calcNewDefaultForMissingField with:" + str(key))
    defaults = {
        0: account["_id"],
        1: account["User"],
        2: account["User ID"],
        3: account["Balance"],
        4: defaultFunnyCreditScore,
        5: defaultFunnyTransactions,
        6: defaultFunnyWage,
        7: 0,
    }
    return defaults[key]
