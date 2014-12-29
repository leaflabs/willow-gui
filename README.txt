This repository contains source code for the WiredLeaf GUI software.
====================================================================

Setup
-----

Install dependencies:

    $ sudo apt-get install python-numpy python-matplotlib python-qt4 python-h5py python-progressbar

Modify src/parameters.py to store the location of relevant directories on your system:

    DAEMON_DIR = <location of leafysd repo>
    DATA_DIR = <default location of data files> (can be updated from the GUI)

Run:

    $ src/main.py


Usage
----

Before starting the GUI:

    - make sure your system is set up to work with the daemon (see section 3
        of the wired-leaf-docs User Guide for directions)
    - change the DAEMON_DIR string variable in src/parameters.py to point to the
        location of the sng-daemon repo on your system


============================
Chris Chronopoulos, 20141229
