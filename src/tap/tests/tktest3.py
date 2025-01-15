import queue
from tkinter import TclError
import weakref


def fancy_bind(widget, callback):
    q = queue.SimpleQueue()
    sequence = f"<<{id(q)}>>"

    def send(obj):
        # in worker thread
        q.put(obj)
        widget.event_generate(sequence)

    def event_handle(event):
        # in tkinter mainloop thread
        obj = q.get()
        callback(obj)

    widget.bind(sequence, event_handle)
    weakref.finalize(send, _finalize, widget, sequence, event_handle)

    return send


def _finalize(widget, sequence, func):
    try:
        widget.unbind(sequence, func)
    except TclError:
        # No need to unbind as application was already destroyed
        pass


if __name__ == "__main__":
    # Simple Demo
    import datetime
    import threading
    import time
    import tkinter as tk

    root = tk.Tk()
    body = tk.Text(root)
    body.pack()

    def handle(result):
        # EXAMPLE: Render data in GUI, on main thread
        body.insert("1.0", f"{result!r}\n")

    send = fancy_bind(root, handle)

    def worker(callback):
        # EXAMPLE: generate data, slowly, on another thread
        while True:
            time.sleep(1)
            callback(f"Hello from the worker at {datetime.datetime.now()}!")

    t = threading.Thread(target=worker, args=[send])

    t.start()
    root.mainloop()
