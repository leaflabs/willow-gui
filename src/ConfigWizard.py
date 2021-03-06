"""
This wizard appears if config.json does not exist - e.g. upon starting the
application for the first time.
"""


from PyQt4 import QtGui, QtCore
from os.path import expanduser
import config

class IntroPage(QtGui.QWizardPage):

    def __init__(self):
        QtGui.QWizardPage.__init__(self)

        self.setTitle('WillowGUI Configuration Wizard')
        label = QtGui.QLabel("WillowGUI has detected that config.json is missing. "
            "Probably this means that you are starting the application for the "
            "first time on this system. This wizard will help you configure your " 
            "setup. You only need to do this once per installation.")
        label.setWordWrap(True)
        label.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)

class DaemonDirPage(QtGui.QWizardPage):

    def __init__(self):
        QtGui.QWizardPage.__init__(self)

        self.setTitle('Daemon Location')

        self.label1 = QtGui.QLabel("First, select the location of the top-level directory "
            "for leafysd, the LeafLabs ephys daemon:")
        self.label1.setWordWrap(True)
        self.label1.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)

        self.dirLine = QtGui.QLineEdit()
        self.dirLine.setDisabled(True)
        self.registerField('daemonDir*', self.dirLine)
        self.browseButton = QtGui.QPushButton('Browse')
        self.browseButton.clicked.connect(self.browse)

        self.label2 = QtGui.QLabel("If leafysd is not installed on this system, "
            "please download and install it by following the instructions in "
            "the Willow 1.0 user guide.")
        self.label2.setWordWrap(True)
        self.label2.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        
        layout = QtGui.QGridLayout()
        layout.addWidget(self.label1, 0,0)
        layout.addWidget(self.dirLine, 1,0)
        layout.addWidget(self.browseButton, 1,1)
        layout.addWidget(self.label2, 2,0)
        self.setLayout(layout)

    def browse(self):
        dirName = QtGui.QFileDialog.getExistingDirectory(self, 'Select Daemon Directory', expanduser("~"))
        if dirName:
            self.dirLine.setText(dirName)

class DataDirPage(QtGui.QWizardPage):

    def __init__(self):
        QtGui.QWizardPage.__init__(self)

        self.setTitle('Default Data Directory')

        self.label1 = QtGui.QLabel("Now, select the location of the directory "
            "where data files will be stored by default. Note that you will have "
            "the option to specify the path of data files as you create them, if you wish.")
        self.label1.setWordWrap(True)
        self.label1.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)

        self.dirLine = QtGui.QLineEdit()
        self.dirLine.setDisabled(True)
        self.registerField('dataDir*', self.dirLine)
        self.browseButton = QtGui.QPushButton('Browse')
        self.browseButton.clicked.connect(self.browse)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.label1, 0,0)
        layout.addWidget(self.dirLine, 1,0)
        layout.addWidget(self.browseButton, 1,1)
        self.setLayout(layout)

    def browse(self):
        dirName = QtGui.QFileDialog.getExistingDirectory(self, 'Select Data Directory', expanduser("~"))
        if dirName:
            self.dirLine.setText(dirName)

class SnapshotAnalysisDirPage(QtGui.QWizardPage):

    def __init__(self):
        QtGui.QWizardPage.__init__(self)

        self.setTitle('Snapshot Analysis Directory')

        self.label1 = QtGui.QLabel("WillowGUI allows you to automatically run "
            "custom analysis scripts on your snapshots. Select the location of "
            "your analysis scripts here.")
        self.label1.setWordWrap(True)
        self.label1.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)

        self.dirLine = QtGui.QLineEdit()
        self.dirLine.setDisabled(True)
        self.registerField('analysisDirSnapshot*', self.dirLine)
        self.browseButton = QtGui.QPushButton('Browse')
        self.browseButton.clicked.connect(self.browse)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.label1, 0,0)
        layout.addWidget(self.dirLine, 1,0)
        layout.addWidget(self.browseButton, 1,1)
        self.setLayout(layout)

    def browse(self):
        dirName = QtGui.QFileDialog.getExistingDirectory(self, 'Select Snapshot Analysis Directory', expanduser("~"))
        if dirName:
            self.dirLine.setText(dirName)

class StreamingAnalysisDirPage(QtGui.QWizardPage):

    def __init__(self):
        QtGui.QWizardPage.__init__(self)

        self.setTitle('Streaming Analysis Directory')

        self.label1 = QtGui.QLabel("WillowGUI allows you to automatically run "
            "custom analysis scripts on streaming data. Select the location of "
            "your analysis scripts here.")
        self.label1.setWordWrap(True)
        self.label1.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)

        self.dirLine = QtGui.QLineEdit()
        self.dirLine.setDisabled(True)
        self.registerField('analysisDirStreaming*', self.dirLine)
        self.browseButton = QtGui.QPushButton('Browse')
        self.browseButton.clicked.connect(self.browse)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.label1, 0,0)
        layout.addWidget(self.dirLine, 1,0)
        layout.addWidget(self.browseButton, 1,1)
        self.setLayout(layout)

    def browse(self):
        dirName = QtGui.QFileDialog.getExistingDirectory(self, 'Select Streaming Analysis Directory', expanduser("~"))
        if dirName:
            self.dirLine.setText(dirName)

class NetworkInterfacePage(QtGui.QWizardPage):

    def __init__(self):
        QtGui.QWizardPage.__init__(self)

        self.setTitle('Network Interface')

        self.textLabel = QtGui.QLabel("What is the name of your network interface? "
            "eth0 is typical, but your system may be set up differently. Enter "
            "the name of your networking interface below.")
        self.textLabel.setWordWrap(True)
        self.textLabel.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)

        self.interfaceLabel = QtGui.QLabel('<b>Network Interface:</b>')
        self.interfaceLine = QtGui.QLineEdit()
        self.registerField('networkInterface*', self.interfaceLine)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.textLabel, 0,0)
        layout.addWidget(self.interfaceLabel, 1,0)
        layout.addWidget(self.interfaceLine, 1,1)
        self.setLayout(layout)

    def initializePage(self):
        self.interfaceLine.setText('eth0')

    def browse(self):
        dirName = QtGui.QFileDialog.getExistingDirectory(self, 'Select Data Directory', expanduser("~"))
        if dirName:
            self.dirLine.setText(dirName)

class StorageCapacityPage(QtGui.QWizardPage):

    def __init__(self):
        QtGui.QWizardPage.__init__(self)

        self.setTitle('Datanode Storage Capacity')

        self.textLabel = QtGui.QLabel("What is the storage capacity of your Willow datanode? "
            "Willow ships with a 1000 GB drive inside, but you or someone in your "
            "lab may have swapped out the drive at some point. This parameter is "
            "used by the software to gauge disk usage. Enter your storage capacity "
            "in gigabytes (GB) below.")
        self.textLabel.setWordWrap(True)
        self.textLabel.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)

        self.storageCapacityLabel = QtGui.QLabel('<b>Storage Capacity (GB):</b>')
        self.storageCapacityLine = QtGui.QLineEdit()
        self.registerField('storageCapacity*', self.storageCapacityLine)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.textLabel, 0,0)
        layout.addWidget(self.storageCapacityLabel, 1,0)
        layout.addWidget(self.storageCapacityLine, 1,1)
        self.setLayout(layout)

    def initializePage(self):
        self.storageCapacityLine.setText('1000')

    def browse(self):
        dirName = QtGui.QFileDialog.getExistingDirectory(self, 'Select Data Directory', expanduser("~"))
        if dirName:
            self.dirLine.setText(dirName)

class ConclusionPage(QtGui.QWizardPage):

    def __init__(self, jsonDict):
        QtGui.QWizardPage.__init__(self)
        self.jsonDict = jsonDict


        self.setTitle('All done!')
        self.mainLabel = QtGui.QLabel('Here are the parameters you selected.')
        self.mainLabel.setWordWrap(True)
        self.mainLabel.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)

        self.daemonDirLabel = QtGui.QLabel()
        self.dataDirLabel = QtGui.QLabel()
        self.analysisDirSnapshotLabel = QtGui.QLabel()
        self.analysisDirStreamingLabel = QtGui.QLabel()
        self.networkInterfaceLabel = QtGui.QLabel()
        self.storageCapacityLabel = QtGui.QLabel()
        self.initializeLabels()

        self.finalLabel = QtGui.QLabel('Click "Finished" to save these settings and '
            'start the GUI. You can change the configuration at any time from '
            'within the GUI by clicking the "Configure Settings" button (gear icon) on '
            'the main control panel.')
        self.finalLabel.setWordWrap(True)
        self.finalLabel.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.mainLabel)
        layout.addWidget(self.daemonDirLabel)
        layout.addWidget(self.dataDirLabel)
        layout.addWidget(self.analysisDirSnapshotLabel)
        layout.addWidget(self.analysisDirStreamingLabel)
        layout.addWidget(self.networkInterfaceLabel)
        layout.addWidget(self.storageCapacityLabel)
        layout.addWidget(self.finalLabel)
        self.setLayout(layout)

    def initializeLabels(self):
        self.daemonDirLabel.setText('<b>daemonDir: </b>')
        self.dataDirLabel.setText('<b>dataDir: </b>')
        self.analysisDirSnapshotLabel.setText('<b>analysisDirSnapshot: </b>')
        self.analysisDirStreamingLabel.setText('<b>analysisDirStreaming: </b>')
        self.networkInterfaceLabel.setText('<b>networkInterface: </b>')
        self.storageCapacityLabel.setText('<b>storageCapacity_GB: </b>')

    def initializePage(self):
        self.initializeLabels()
        self.daemonDir = self.field('daemonDir').toString()
        self.daemonDirLabel.setText(self.daemonDirLabel.text().append(self.daemonDir))
        self.dataDir = self.field('dataDir').toString()
        self.dataDirLabel.setText(self.dataDirLabel.text().append(self.dataDir))
        self.analysisDirSnapshot = self.field('analysisDirSnapshot').toString()
        self.analysisDirStreaming = self.field('analysisDirStreaming').toString()
        self.analysisDirSnapshotLabel.setText(self.analysisDirSnapshotLabel.text().append(self.analysisDirSnapshot))
        self.analysisDirStreamingLabel.setText(self.analysisDirStreamingLabel.text().append(self.analysisDirStreaming))
        self.networkInterface = self.field('networkInterface').toString()
        self.networkInterfaceLabel.setText(self.networkInterfaceLabel.text().append(self.networkInterface))
        self.storageCapacity = self.field('storageCapacity').toString()
        self.storageCapacityLabel.setText(self.storageCapacityLabel.text().append(self.storageCapacity))

    def validatePage(self):
        self.jsonDict['daemonDir']['value'] = str(self.daemonDir)
        self.jsonDict['dataDir']['value'] = str(self.dataDir)
        self.jsonDict['analysisDirSnapshot']['value'] = str(self.analysisDirSnapshot)
        self.jsonDict['analysisDirStreaming']['value'] = str(self.analysisDirStreaming)
        self.jsonDict['networkInterface']['value'] = str(self.networkInterface)
        self.jsonDict['storageCapacity_GB']['value'] = int(self.storageCapacity)
        ###
        config.saveJSON(self.jsonDict)
        config.updateAttributes(self.jsonDict)
        # now create the main window as an attribute of the wizard
        # TODO: clean this up, it's a hack
        from MainWindow import MainWindow
        self.wizard().mainWindow = MainWindow(self.wizard().debugFlag)
        self.wizard().mainWindow.show()
        return True

class ConfigWizard(QtGui.QWizard):

    def __init__(self, debugFlag):
        QtGui.QWizard.__init__(self)

        self.debugFlag = debugFlag

        # initialize jsonDict with missing values
        self.jsonDict = {}
        self.jsonDict['daemonDir'] = {'type': 'str', 'description': 'Daemon Directory'}
        self.jsonDict['dataDir'] = {'type': 'str', 'description': 'Data Directory'}
        self.jsonDict['analysisDirSnapshot'] = {'type': 'str', 'description': 'Snapshot Analysis Directory'}
        self.jsonDict['analysisDirStreaming'] = {'type': 'str', 'description': 'Streaming Analysis Directory'}
        self.jsonDict['networkInterface'] = {'type': 'str', 'description': 'Network Interface Name'}
        self.jsonDict['storageCapacity_GB'] = {'type': 'float', 'description': 'Datanode Storage Capacity (GB)'}

        self.mainWindow = None

        self.setWindowTitle("WillowGUI Configuration Wizard")
        self.addPage(IntroPage())
        self.addPage(DaemonDirPage())
        self.addPage(DataDirPage())
        self.addPage(SnapshotAnalysisDirPage())
        self.addPage(StreamingAnalysisDirPage())
        self.addPage(NetworkInterfacePage())
        self.addPage(StorageCapacityPage())
        self.addPage(ConclusionPage(self.jsonDict))

