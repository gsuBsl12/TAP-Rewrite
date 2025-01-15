# TAP-GUI

[Taylor Aggression Paradigm](https://en.wikipedia.org/wiki/Taylor_Aggression_Paradigm) (TAP) GUI

This is a Windows GUI written entirely in Python for conducting TAP experiments. This software uses the following resources:

- [Tkinter](https://docs.python.org/3/library/tkinter.html) for menus and interfaces
- [Pygame](https://www.pygame.org/) for subject interaction interface
- [Pandas](https://pandas.pydata.org/) & [NumPy](https://numpy.org/) for data collection and formatting
- [nidaqmx](https://nidaqmx-python.readthedocs.io/en/stable/) for interfacing with DAQ card

The software is built to interface with the [NI-DAQ USB-6001](https://www.ni.com/en-us/shop/model/usb-6001.html). This DAQ card serves as an electrical signal processor and sends a digital and analog signal to the [Coulbourn Precision-Regulated Programmable Shocker](https://www.harvardapparatus.com/media/manuals/Product%20Manuals/H13-15,%20-16%20Aninal%20Shocker%20Manual.pdf).

## Installation

First, download and install the latest [NI-DAQmx Drivers](https://www.ni.com/en/support/downloads/drivers/download.ni-daq-mx.html#549669). These are required for connecting to the DAQ card.

The `tap.exe` executable is included in this repository.

To download the repository from GitHub, you can (1) click `<> Code` > `Download ZIP` and extract the .zip folder

or (2) press `Windows + R` > `Type 'cmd'` > `Enter` to bring up Command Prompt and run the following commands (requires git in $PATH):

```bash
git clone https://github.com/trexlernoah/TAP-Rewrite.git
```

The .exe is located in `/dist/tap/tap.exe`. If you move the .exe, you must move the `_internal` folder containing the .dll's to the same directory.

## Build

To build the .exe from source, run the following in the root directory:

```bash
python -m pip install ./src
python -m pip install -U pyinstaller
python -m PyInstaller --recursive-copy-metadata nidaqmx ./src/tap/main.pyw
```

Find the tap.exe in the dist/ folder.

## Hardware

To run the software, ensure that the DAQ card is plugged in to the computer via USB. Then, ensure that the DAQ card is electrically connected to the Coulbourn Shocker. See `/diagrams/wire-diagram.png` as a reference.

## Usage

Ensure that the DAQ card is accessible to the computer running the GUI. You can verify this using NI software that is installed along with the NI-DAQmx driver.

To create a new experiment:

- From the GUI, create a new experiment from `Experiment` > `Create New` > `Experiment`.
- Then, enter the number of trials for the experiment.
- Input the pre-determined `Win/Loss`, `Shock`, & `Feedback` for each trial on the `Trial Data` tab.
- Adjust intensities on the `Corresponding Intensities` tab.
- Click `Ok` to return to the main menu.
- Click `Threshold` > `Set Subject Threshold`.
- Input `Subject ID`.
- Run the shock threshold for both the lower level and higher level, then click `Ok`.

To run the experiment:

- Click `Experiment` > `Run` > `Official`.
- To exit the experiment while in-progress, use `Ctrl-Alt-Del` to kill the program.
- To exit the experiment once finished, press `Ctrl-C`.

## Documentation

The software is comprised of one top-level module which makes use of two submodules. The submodules are `/tap/game`, which holds the logic for the subject experiment written in PyGame, and `/tap/menu`, which holds the logic for the menu GUI written in Tkinter.

The top-level scripts include `/tap/daq.py`, which contains the logic for interfacing with the DAQ card, and `/tap/classes.py`, which holds all `class`, `enum`, and `tuple` definitions.

The Tkinter menu, PyGame experiment, and DAQ interface all communicate via a shared `ThreadHandler` object, which is a wrapper around a `Queue` and two thread `Event`s. The main program is divided into two threads -- one for the Tk menu and PyGame experiment, and one for the DAQ shocker -- because the [Tkinter event loop](https://tkdocs.com/tutorial/eventloop.html#threads) does not provide an interface for non-blocking asynchronous events. See `/diagrams/threading.png` as a visual reference. The `Queue` is an event queue onto which `ShockTasks` are pushed from the Tk/PyGame thread, and read and processed continuously.

The `ShockTask` contains 3 float variables: the shock value in milliamps, the duration of shock in seconds, and the cooldown of shock in seconds. The two `Event`s register a halt event and a kill event for handling programmed exits during a `ShockTask` execution.
