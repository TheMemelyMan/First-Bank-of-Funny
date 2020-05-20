import json

with open("config.json") as f:
    configData = json.load(f)
with open("chatlog.json") as g:
    chatData = json.load(g)
