This repository contains source code for the WiredLeaf GUI software.
====================================================================

Setup
-----

Install dependencies:

    $ sudo apt-get install python-numpy python-matplotlib python-pyqt4

Run:

    $ ./wiredLeaf.py 


Usage
----

Before starting the GUI:

    - make sure your system is set up to work with the daemon (see section 3
        of the wired-leaf-docs User Guide for directions)
    - change the DAEMON_DIR string variable near the top of wiredLeafy.py to
        point to the location of the sng-daemon repo on your system
    - make sure there isn't an instance of the daemon running before you start
        the GUI (to be sure, you can run $ killall leafysd)


Notes
-----

Currently (as of 20140618) this version is regarded as a prototype, to get
something working quickly, try out ideas, and identify potential difficulties
early on. As such, it is built using tools that are familiar to me, like
matplotlib, which only has backend support for Qt4. Eventually, we'd like to
move to Qt5, and a compatible plotting tool like QCustomPlot, which would also
mean porting to C++.

The GUI is organized as a collection of tabs, each serving a single purpose. In
the source code, each tab is its own module, imported by the main script,
wiredLeaf.py.


============================
Chris Chronopoulos, 20140618
