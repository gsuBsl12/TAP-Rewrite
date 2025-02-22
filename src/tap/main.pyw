import atexit
from threading import Event

from tap.menu.main_menu import MainMenu
from tap.daq import DAQ
from tap.classes import Queue, ThreadHandler, Logger

thread_handler = ThreadHandler(Queue(), Event(), Event())

logger = Logger(True)


def main():
    logger.log("Creating menu thread")
    tk_thread = MainMenu(thread_handler, logger)

    logger.log("Creating DAQ thread")
    daq_thread = DAQ(thread_handler, logger)

    daq_thread.join()
    logger.log("Joined DAQ thread")

    tk_thread.join()
    logger.log("Joined menu thread")


def exit():
    logger.log("Setting kill event")
    thread_handler.kill_event.set()


if __name__ == "__main__":
    atexit.register(exit)
    main()
