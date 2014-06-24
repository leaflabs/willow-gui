from PyQt4 import QtCore, QtGui
import subprocess, os

from parameters import DAEMON_DIR, DATA_DIR

class RegisterTab(QtGui.QWidget):

    def __init__(self, parent):
        super(RegisterTab, self).__init__(None)
        self.parent = parent

        self.reglists = {}
        self.reglists['Error'] = ['00 Individual Module Error Flags (1B)']
        self.reglists['Central'] = [
            '00 Central Module Error Flags (1B)',
            '01 Central Module State (1B)',
            '02 Experiment cookie, top 4 bytes',
            '03 Experiment cookie, bottom 4 bytes',
            '04 Git commit of FPGA HDL firmware (4B)',
            '05 FPGA HDL Parameters (4B)',
            '06 FPGA HDL Build Unix Time (4B)',
            '07 Board Identifier (4B)']
        self.reglists['SATA'] = [
            '00 SATA Module Error Flags',
            '01 SATA Module Mode (0=wait 1=read 2=write) (1B)',
            '02 SATA Module Status (3B)',
            '03 Disk Identifier',
            '04 Disk I/O parameters',
            '05 Next Read Index (4B)',
            '06 Read Length (4B)',
            '07 Last Write Index (4B)',
            '08 SATA Read FIFO Reset',
            '09 SATA Read FIFO Status',
            '10 SATA Read FIFO Count',
            '11 UDP FIFO Reset',
            '12 UDP FIFO Status',
            '13 UDP FIFO Count',
            '14 Current Disk Sector, High Bytes (2B)',
            '15 Current Disk Sector, Low Bytes (4B)',
            '16 DelayClock Freq in Hz (4B)',
            '17 SATA Read Slowdown in Clock Cycles (4B)',
            '18 SATA Write Delay Cycles (3B)',
            '19 DAQ-SATA FIFO Count for Feedback (2B)',
            '20 Write Starting Sample Index (4B)']
        self.reglists['DAQ'] = [
            '00 DAQ Module Error Flags',
            '01 DAQ Module Acquire Enable (1 B)',
            '02 Desired Start Board Sample Number (4 B)',
            '03 Current Board Sample Number (4 B)',
            '04 Chip alive bitmask (4 B)',
            '05 CMD Write Enable (1 B) | CMD Chip Address (1 B) | CMD Command (2 B)',
            '06 Synchronous Sampling Mode (TBD)',
            '07 DAQ FIFO Read Count ("byte in FIFO")',
            '08 DAQ FIFO flags (TBD; bit[0] is reset line)',
            '09 UDP Output Enable (1 B)',
            '10 Unused (3 B) | UDP Output Mode (0=sub, 1=full) (1 B)',
            '11 Unused (3 B) | DAQ SATA Output Enable (1 B)',
            '12 DAQ SATA FIFO read count ("words in FIFO")',
            '13 DAQ SATA FIFO flags (TBD, but bit[0] is reset line)',
            '128 SubSample #0 Chip (1B) | SubSample #0 Channel (1B)',
            '129 SubSample #1 Chip (1B) | SubSample #1 Channel (1B)',
            '130 SubSample #2 Chip (1B) | SubSample #2 Channel (1B)',
            '131 SubSample #3 Chip (1B) | SubSample #3 Channel (1B)',
            '132 SubSample #4 Chip (1B) | SubSample #4 Channel (1B)',
            '133 SubSample #5 Chip (1B) | SubSample #5 Channel (1B)',
            '134 SubSample #6 Chip (1B) | SubSample #6 Channel (1B)',
            '135 SubSample #7 Chip (1B) | SubSample #7 Channel (1B)',
            '136 SubSample #8 Chip (1B) | SubSample #8 Channel (1B)',
            '137 SubSample #9 Chip (1B) | SubSample #9 Channel (1B)',
            '138 SubSample #10 Chip (1B) | SubSample #10 Channel (1B)',
            '139 SubSample #11 Chip (1B) | SubSample #11 Channel (1B)',
            '140 SubSample #12 Chip (1B) | SubSample #12 Channel (1B)',
            '141 SubSample #13 Chip (1B) | SubSample #13 Channel (1B)',
            '142 SubSample #14 Chip (1B) | SubSample #14 Channel (1B)',
            '143 SubSample #15 Chip (1B) | SubSample #15 Channel (1B)',
            '144 SubSample #16 Chip (1B) | SubSample #16 Channel (1B)',
            '145 SubSample #17 Chip (1B) | SubSample #17 Channel (1B)',
            '146 SubSample #18 Chip (1B) | SubSample #18 Channel (1B)',
            '147 SubSample #19 Chip (1B) | SubSample #19 Channel (1B)',
            '148 SubSample #20 Chip (1B) | SubSample #20 Channel (1B)',
            '149 SubSample #21 Chip (1B) | SubSample #21 Channel (1B)',
            '150 SubSample #22 Chip (1B) | SubSample #22 Channel (1B)',
            '151 SubSample #23 Chip (1B) | SubSample #23 Channel (1B)',
            '152 SubSample #24 Chip (1B) | SubSample #24 Channel (1B)',
            '153 SubSample #25 Chip (1B) | SubSample #25 Channel (1B)',
            '154 SubSample #26 Chip (1B) | SubSample #26 Channel (1B)',
            '155 SubSample #27 Chip (1B) | SubSample #27 Channel (1B)',
            '156 SubSample #28 Chip (1B) | SubSample #28 Channel (1B)',
            '157 SubSample #29 Chip (1B) | SubSample #29 Channel (1B)',
            '158 SubSample #30 Chip (1B) | SubSample #30 Channel (1B)',
            '159 SubSample #31 Chip (1B) | SubSample #31 Channel (1B)']

        self.reglists['UDP'] = [
            '00 UDP Module Error Flags',
            '01 UDP Module Enable (1 B)',
            '02 Source MAC-48 Address Top bytes (2 B)',
            '03 Source MAC-48 Address Bottom bytes (4 B)',
            '04 Destination MAC-48 Address Top bytes (2 B)',
            '05 Destination MAC-48 Address Bottom bytes (4 B)',
            '06 Source IPv4 Address (4 B)',
            '07 Destination IPv4 Address (4 B)',
            '08 Source IPv4 Port (2 B)',
            '09 Destination IPv4 Port (2 B)',
            '10 Unused (2 B) | Packet TX Count (2 B)',
            '11 Ethernet Packet Length (2 B)',
            '12 Payload Length (2 B)',
            '13 UDP Module Mode (0=daq, 1=sata) (1 B)',
            '14 GigE Status (1 B)',
            '15 GigE PHY MIIM Enable (1 bit)',
            '16 GigE PHY MIIM Address (5 bits)',
            '17 GigE PHY MIIM Data (17 bit)']

        self.reglists['GPIO'] = [
            '00 GPIO Module Error Flags',
            '01 (no state machine for GPIO pins)',
            '02 GPIO read mask (2B)',
            '03 GPIO write mask (2B)',
            '04 GPIO state (2B)']

        self.moduleDropdown = QtGui.QComboBox()
        self.moduleDropdown.addItem('Error')
        self.moduleDropdown.addItem('Central')
        self.moduleDropdown.addItem('SATA')
        self.moduleDropdown.addItem('DAQ')
        self.moduleDropdown.addItem('UDP')
        self.moduleDropdown.addItem('GPIO')
        self.moduleDropdown.activated.connect(self.populateRegisterDropdown)

        self.registerDropdown = QtGui.QComboBox()
        for reg in self.reglists['Error']:
            self.registerDropdown.addItem(reg)

        self.valueLine = QtGui.QLineEdit()

        self.readButton = QtGui.QPushButton('Read')
        self.readButton.clicked.connect(self.read)
        self.writeButton = QtGui.QPushButton('Write')
        self.writeButton.clicked.connect(self.write)
        ##
        self.buttonLayout = QtGui.QHBoxLayout()
        self.buttonLayout.addWidget(self.readButton)
        self.buttonLayout.addWidget(self.writeButton)
        self.buttons = QtGui.QWidget()
        self.buttons.setLayout(self.buttonLayout)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(QtGui.QLabel('Select Module:'))
        self.layout.addWidget(self.moduleDropdown)
        self.layout.addWidget(QtGui.QLabel('Select Register:'))
        self.layout.addWidget(self.registerDropdown)
        self.layout.addWidget(QtGui.QLabel('Enter Value to Write:'))
        self.layout.addWidget(self.valueLine)
        self.layout.addSpacing(100)
        self.layout.addWidget(self.buttons)
        self.setLayout(self.layout)

        self.debugToolDotPy = os.path.join(DAEMON_DIR, 'util/debug_tool.py')

    def populateRegisterDropdown(self):
        self.registerDropdown.clear()
        reglist = self.reglists[str(self.moduleDropdown.currentText())]
        for reg in reglist:
            self.registerDropdown.addItem(reg)

    def read(self):
        if self.parent.isDaemonRunning:
            pipeObject = subprocess.Popen([self.debugToolDotPy, 'read', str(self.moduleDropdown.currentText()).lower(), str(self.registerDropdown.currentIndex())], stdout=subprocess.PIPE)
            result = pipeObject.stdout.readline()
            self.parent.statusBox.append(result[:-1])
        else:
            self.parent.statusBox.append('Daemon is not running!')

    def write(self):
        if self.parent.isDaemonRunning:
            pipeObject = subprocess.Popen([self.debugToolDotPy, 'write', str(self.moduleDropdown.currentText()).lower(), str(self.registerDropdown.currentIndex()), self.valueLine.text()], stdout=subprocess.PIPE)
            result = pipeObject.stdout.readline()
            self.parent.statusBox.append(result[:-1])
        else:
            self.parent.statusBox.append('Daemon is not running!')

