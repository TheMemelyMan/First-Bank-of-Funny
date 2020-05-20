from config import configData
from pymongo import MongoClient

mongoPath = configData["tokens"][0]["mongoPath"]

client = MongoClient(mongoPath)

# database clients
dbDiscord = client["Discord"]
dbFirstBankOfFunny = client["FirstBankOfFunny"]
