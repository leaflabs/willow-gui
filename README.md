# willowGUI
GUI software for the Willow electrophysiology system

www.leaflabs.com/willow

![gui_windowtiling](https://github.com/leaflabs/willowgui/blob/master/docs/user_guide/screenshots/gui_windowtiling.png)

## Setup

1. Install dependencies:

    $ sudo apt-get install python-numpy python-matplotlib python-qt4 python-tk python-git python-pip python-pyqtgraph

    $ pip install h5py

   Note: Old versions of h5py are known to have bugs which can affect GUI
   usage. In particular, v2.2.1 is known to be buggy. This bug is fixed in
   v2.5.0. Make sure you've got the latest version by installing with pip
   instead of apt-get.

2. Make sure your system is set up to work with the daemon. Refer to the
    "Willow 1.0 User Guide", available [here](docs/user_guide/willowgui_userguide.pdf).

3. Run:

    $ src/main.py


## Usage

See the User Guide in docs/user_guide for usage instructions. A compiled
version is distributed with this repo as willowgui_userguide.pdf.

To compile the user guide yourself:

    $ cd docs/user_guide
    $ pdflatex main

