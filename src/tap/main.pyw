import atexit
from threading import Event

from tap.menu.main_menu import MainMenu
from tap.daq import DAQ
from tap.classes import Queue, ThreadHandler

thread_handler = ThreadHandler(Queue(), Event(), Event())


def main():
    tk_thread = MainMenu(thread_handler)

    daq_thread = DAQ(thread_handler)
    daq_thread.join()

    tk_thread.join()


def exit():
    print("Setting kill event")
    thread_handler.kill_event.set()


if __name__ == "__main__":
    atexit.register(exit)
    main()
