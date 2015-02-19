import json, sys

def split(jDict):
    vDict = {}
    dDict = {}
    for name, (value, description) in jDict.items():
        vDict[name] = value
        dDict[name] = description
    return vDict, dDict

def merge(vDict, dDict):
    jDict = {}
    for key in vDict.keys():
        jDict[key] = (vDict[key], dDict[key])
    return jDict

def loadJSON():
    """
    Reads in config.json, returns jDict
    """
    with open('config.json', 'r') as f:
        jDict = json.load(f)
    return jDict

def saveJSON(jDict):
    """
    Saves jDict to config.json
    """
    with open('config.json', 'w') as f:
        json.dump(jDict, f, indent=4, separators=(',', ' : '))

def updateAttributes(jDict):
    currentModule = sys.modules[__name__]
    for varName, varDict in jDict.items():
        setattr(currentModule, varName, varDict['value']) # TODO implement type-casting?

####

jsonDict = loadJSON()
updateAttributes(jsonDict)

