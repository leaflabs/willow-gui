# willowephys
Supplies `willowephys`, a Python library containing resources common to
repositories which provide user-facing applications for controlling Willow
electrophysiology systems and/or examining the data recorded by these systems.

## Installation
Ensure that you have an installation of pip, a Python package manager. To get
pip, you can either follow the instructions
[here](https://packaging.python.org/tutorials/installing-packages/), or, if
appropriate, use a copy of pip supplied by your operating system. (In Debian or
Debian-like operating systems such as Ubuntu or Linux Mint, `apt install
python-pip`)

Navigate to the directory this file is in. Run:

`pip install --user .`

## Uninstallation
Navigate to the directory this file is in. Run:

`pip uninstall .`

## Note to developers
If you create a file that you'd like to use in more than one of the repositories
`willow-gui`, `willow-snapshot-analysis`, or `willow-stream-analysis`, delete it
from those repositories and add it to this library instead.
