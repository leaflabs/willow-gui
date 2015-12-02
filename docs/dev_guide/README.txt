CONFIG SYSTEM
-------------

willowgui features a system for saving, loading, and setting global config
parameters which is designed to be easily extensible. to introduce a new
parameter, just add it to config.json in this format*:

    "daemonDir" : {
        "type" : "str",
        "description" : "Daemon Directory",
        "value" : "/home/chrono/daemon"
    }

* you'll also probably want to add a new page to the ConfigWizard, which
explains the meaning of the parameter, and maybe suggests a default value.

if config.json exists on startup, willowgui imports and initializes config.py
as a module:

    import config
    config.updateAttributes(config.loadJSON())

what's going on here?
    loadJSON() returns a dict of dicts from config.json
    updateAttributes() uses this structure to set the attributes in the module

the settings can be changed during runtime from the SettingsWindow. when the
user clicks 'save', it takes the strings from the QLabels, casts them to their
type listed in config.json, composes them into a dict, calls updateAttributes()
on this dict, and finally, calls saveJSON() to save to the JSON file.

if config.json does NOT exist on startup, main.py will launch the ConfigWizard,
which walks the user through the initial setting of the config parameters. each
config parameter should have a page in ConfigWizard.py dedicated to its
initialization. 

Chris Chronopoulos, 20151202

