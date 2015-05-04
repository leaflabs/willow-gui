willowGUI:
GUI software for the Willow electrophysiology system
www.leaflabs.com/neuroscience
====================================================

Setup
-----

1. Install dependencies:

    $ sudo apt-get install python-numpy python-matplotlib python-qt4 python-tk
    $ sudo pip install h5py

   Note: Old versions of h5py are known to have bugs which can affect GUI usage. In
     particular, v2.2.1 is known to be buggy. This bug is fixed in v2.5.0. Make sure
     you've got the latest version by installing with pip instead of apt-get.

2. Make sure your system is set up to work with the daemon (see README in the leafysd repo)

3. Modify src/config.json to point to  the location of relevant directories on your system:

    DAEMON_DIR = <location of leafysd repo>
    DATA_DIR = <default location of data files> (can be updated from the GUI)

4. Run:

    $ src/main.py


Usage
----

See the User Guide in docs/user_guide for usage instructions. To compile the user guide:

    $ cd docs/user_guide
    $ pdflatex main

Then open main.pdf
