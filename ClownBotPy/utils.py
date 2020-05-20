from db import dbFirstBankOfFunny


# defaults
defaultFunnyCreditScore = 500
defaultFunnyTransactions = 5
defaultFunnyWage = 11


def getAccount(userID, serverID):
    queueUp = dbFirstBankOfFunny[str(serverID)]
    inDb = queueUp.find()

    for account in inDb:
        if account["User ID"] == int(userID):
            checkIfAccountHasAllFields(serverID, account)

    queueUp = dbFirstBankOfFunny[str(serverID)]
    inDbAfterCheck = queueUp.find()
    for account in inDbAfterCheck:
        if account["User ID"] == int(userID):
            return account


def checkIfAccountExists(userID, serverID):
    queueUp = dbFirstBankOfFunny[str(serverID)]
    inDb = queueUp.find()
    exists = False
    for entry in inDb:
        if entry["User ID"] == int(userID):
            return True
    return exists


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
    queueUp = dbFirstBankOfFunny[str(serverID)].find(account)
    cursor = dbFirstBankOfFunny[str(serverID)]
    keys = getAccountKeys()
    query = {"_id": account["_id"]}
    for document in queueUp:
        for key in keys:
            if key not in document.keys():
                try:
                    # print("Got to checkIfAccountHasAllFields where"
                    # + " key was not in document.keys(). Key:  " + str(key))
                    newValue = {
                        "$set": {
                            str(key): calcNewDefaultForMissingField(
                                account, keys.index(key)
                            )
                        }
                    }
                    cursor.find_one_and_update(query, newValue)
                except Exception as e:
                    print(e)


# Field Updater Methods
def getAccountKeys():
    return [
        "_id",
        "User",
        "User ID",
        "Balance",
        "Funny Credit Score",
        "Daily Funny Transactions",
        "Funny Wage",
        "Funny Worked",
    ]


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
