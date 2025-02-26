import tkinter as tk
from tkinter import ttk, messagebox

from classes import ThreadHandler, ShockTask, Settings


class SubjectThreshold(tk.Toplevel):
    def __init__(self, master, thread_handler: ThreadHandler, settings: Settings):
        self.thread_handler = thread_handler
        self.settings = settings

        self.lower_threshold = settings.lower_threshold
        self.higher_threshold = settings.higher_threshold

        self.window = tk.Toplevel(master)
        self.window.geometry("400x300")
        self.window.title("Subject Threshold")

        content = ttk.Frame(self.window, padding=(12, 12, 12, 12))
        frame = ttk.Frame(
            content,
            borderwidth=5,
            relief="ridge",
            width=400,
            height=300,
            padding=(12, 12, 12, 12),
        )

        subject_id_label = ttk.Label(content, text="Subject ID")
        self.subject_id_entry = ttk.Entry(content)
        self.subject_id_entry.insert(0, str(self.settings.subject_id))

        min_shock_duration = ttk.Label(content, text="Minimum shock duration (ms)")
        self.min_shock_duration_entry = ttk.Entry(content)
        self.min_shock_duration_entry.insert(0, str(self.settings.min_shock_duration))
        max_shock_duration = ttk.Label(content, text="Maximum shock duration (ms)")
        self.max_shock_duration_entry = ttk.Entry(content)
        self.max_shock_duration_entry.insert(0, str(self.settings.max_shock_duration))

        set_lower_level = ttk.Label(frame, text="Set Lower Level")
        self.lower_threshold_var = tk.StringVar(value=f"{str(self.lower_threshold)} mA")
        lower_threshold_label = ttk.Label(frame, textvariable=self.lower_threshold_var)
        start_lower_level = ttk.Button(
            frame,
            text="Start",
            command=lambda: self.start_low_shock(),
        )

        separator = ttk.Separator(frame, orient=tk.VERTICAL)

        set_higher_level = ttk.Label(frame, text="Set Higher Level")
        self.higher_threshold_var = tk.StringVar(
            value=f"{str(self.higher_threshold)} mA"
        )
        higher_threshold_label = ttk.Label(
            frame, textvariable=self.higher_threshold_var
        )
        start_higher_level = ttk.Button(
            frame,
            text="Start",
            command=lambda: self.start_high_shock(),
        )

        ok = ttk.Button(content, text="OK", command=self.write_data)
        cancel = ttk.Button(
            content,
            text="Cancel",
            command=self.window.destroy,
        )

        content.grid(column=0, row=0, sticky="NEWS")
        frame.grid(column=0, row=6, sticky="NEWS")
        subject_id_label.grid(column=0, row=0, columnspan=2, sticky="NW", padx=5)
        self.subject_id_entry.grid(column=0, row=1, columnspan=2, sticky="NEW", padx=5)
        min_shock_duration.grid(column=0, row=2, columnspan=2, sticky="NW", padx=5)
        self.min_shock_duration_entry.grid(
            column=0, row=3, columnspan=2, sticky="NEW", padx=5
        )
        max_shock_duration.grid(column=0, row=4, columnspan=2, sticky="NW", padx=5)
        self.max_shock_duration_entry.grid(
            column=0, row=5, columnspan=2, sticky="NEW", padx=5
        )

        set_lower_level.grid(column=0, row=0, sticky="W")
        lower_threshold_label.grid(column=0, row=1, sticky="W")
        start_lower_level.grid(column=0, row=2, sticky="W")

        separator.grid(column=1, row=0, rowspan=3, sticky="NS", padx=10)

        set_higher_level.grid(column=2, row=0, sticky="E")
        higher_threshold_label.grid(column=2, row=1, sticky="E")
        start_higher_level.grid(column=2, row=2, sticky="E")

        ok.grid(column=0, row=7, pady=5)
        cancel.grid(column=1, row=7, pady=5)

        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        self.window.minsize(400, 300)

        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=3)
        content.columnconfigure(2, weight=3)
        content.rowconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)
        content.rowconfigure(2, weight=1)
        content.rowconfigure(3, weight=1)
        content.rowconfigure(4, weight=1)
        content.rowconfigure(5, weight=1)
        content.rowconfigure(6, weight=1)

    def start_low_shock(self):
        self.administer_shock(0.0, 1.250)

    def start_high_shock(self):
        self.administer_shock(self.lower_threshold, 2.500, False)

    def administer_shock(self, min: float, max: float, lower=True):
        def update():
            if self.thread_handler.task_queue.unfinished_tasks <= 0:
                return
            if self.thread_handler.task_queue.unfinished_tasks > len(shock_vals):
                return

            idx = len(shock_vals) - self.thread_handler.task_queue.unfinished_tasks
            current_shock = shock_vals[idx]
            current_shock_text.set(f"Current level: {str(current_shock)} mA")

            if lower:
                self.lower_threshold = current_shock
                self.lower_threshold_var.set(f"{str(self.lower_threshold)}mA")
            else:
                self.higher_threshold = current_shock
                self.higher_threshold_var.set(f"{str(self.higher_threshold)} mA")

            self.window.after(500, update)

        def stop():
            self.thread_handler.task_queue.lock()
            self.thread_handler.halt_event.set()
            subwindow.destroy()

        if min < 0.0:
            min = 0.0
        if max > 2.500:
            max = 2.500

        subwindow = tk.Toplevel(self.window)
        subwindow.geometry("400x200")
        subwindow.resizable(False, False)
        subwindow.title("Set Threshold")
        subwindow.protocol("WM_DELETE_WINDOW", stop)

        desc = tk.Label(subwindow, text="Administering shocks")
        desc.pack(pady=20)

        current_shock = min
        current_shock_text = tk.StringVar(value=f"Current level: {current_shock} mA")
        current_shock_label = tk.Label(subwindow, textvariable=current_shock_text)
        current_shock_label.pack()
        stop_btn = tk.Button(subwindow, text="Stop", command=stop)
        stop_btn.pack()

        shock_vals = [x / 1000 for x in range(int(min * 1000), int(max * 1000), 75)]

        self.thread_handler.task_queue.unlock()
        for s in shock_vals:
            self.thread_handler.task_queue.put_task(ShockTask(s, 1, 3.5))
        update()

    def write_data(self):
        self.settings.lower_threshold = self.lower_threshold
        self.settings.higher_threshold = self.higher_threshold
        self.settings.subject_id = self.subject_id_entry.get()

        try:
            mn = int(self.min_shock_duration_entry.get())
            mx = int(self.max_shock_duration_entry.get())
            if mn > mx or mn < 0 or mx > 10000:
                messagebox.showinfo("Notification", "Check your values again.")
            else:
                self.settings.min_shock_duration = mn
                self.settings.max_shock_duration = mx

                self.window.destroy()
        except ValueError:
            messagebox.showinfo("Notification", "Check your values again.")
