
import json

def GetConfigFromFile():
    try:
        with open('Config.json') as json_file:
            data = json.load(json_file)
            return data
    except BaseException as e:
        return None