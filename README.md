# willowGUI
GUI software for the Willow electrophysiology system

www.willowephys.com

![gui_windowtiling](https://github.com/leaflabs/willowgui/blob/master/docs/user_guide/screenshots/gui_windowtiling.png)

## Setup

1. Install dependencies:

    $ sudo apt-get install python-numpy python-matplotlib python-qt4 python-tk python-git python-pip util-linux

    $ pip install pyqtgraph h5py sharedmem

   Note: Old versions of h5py are known to have bugs which can affect GUI
   usage. In particular, v2.2.1 is known to be buggy. This bug is fixed in
   v2.5.0. Make sure you've got the latest version by installing with pip
   instead of apt-get.

2. Make sure your system is set up to work with willow-daemon. For instructions on setting up the
    daemon, refer to the documentation [here](http://docs.willowephys.com/software_user_manual.html#daemon).

3. Install the willowephys library, whose source lives in the `lib/` directory
   of this repository. Follow the instructions in `lib/README.md` to do this.
   Note that this step should be done after each update to the willowephys
   library.

4. Run:

    $ src/main.py


## Usage
For usage instructions, refer to the documentation [here](http://docs.willowephys.com/software_user_manual.html#willowgui).

