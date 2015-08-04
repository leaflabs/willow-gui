import json, sys

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
    # just treat these as non-configurable global parameters for now
    setattr(currentModule, 'defaultForwardAddr', '127.0.0.1')
    setattr(currentModule, 'defaultForwardPort', 7654)
    # finally, save jsonDict itself:
    setattr(currentModule, 'jsonDict', jDict)
####

#jsonDict = loadJSON()
#updateAttributes(jsonDict)

