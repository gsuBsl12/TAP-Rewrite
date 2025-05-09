import tkinter as tk
from tkinter import ttk, messagebox

from classes import ThreadHandler, ShockTask, Settings, Logger


class SubjectThreshold(tk.Toplevel):
    WINDOW_GEOMETRY = "400x300"
    MIN_SHOCK = 0.0
    MAX_SHOCK = 2.500
    SHOCK_INCREMENT = 0.075
    SHOCK_LABEL = "Current level: {value} mA"
    ADMINISTERING_SHOCK_TEXT = "Administering shocks"
    LOWER_THRESHOLD_LABEL = "Set Lower Level"
    HIGHER_THRESHOLD_LABEL = "Set Higher Level"

    def __init__(
        self, master, thread_handler: ThreadHandler, settings: Settings, logger: Logger
    ):
        self.thread_handler = thread_handler
        self.settings = settings
        self.logger = logger

        self.lower_threshold = settings.lower_threshold
        self.higher_threshold = settings.higher_threshold

        self.window = tk.Toplevel(master)
        self._initialize_window()
        self._initialize_threshold_vars()
        self._build_gui()

    def _initialize_window(self):
        self.window.geometry(self.WINDOW_GEOMETRY)
        self.window.title("Subject Threshold")
        self.window.minsize(400, 300)
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)

    def _initialize_threshold_vars(self):
        self.lower_threshold_var = tk.StringVar(value=f"{str(self.lower_threshold)} mA")
        self.higher_threshold_var = tk.StringVar(
            value=f"{str(self.higher_threshold)} mA"
        )

    def _build_gui(self):
        content = ttk.Frame(self.window, padding=(12, 12, 12, 12))
        content.grid(column=0, row=0, sticky="NEWS")
        self._build_form(content)
        self._build_threshold_controls(content)

    def _build_form(self, parent):
        self._add_label_and_entry(
            parent, "Subject ID", 0, self.settings.subject_id, "subject_id_entry"
        )
        self._add_label_and_entry(
            parent,
            "Minimum shock duration (ms)",
            2,
            self.settings.min_shock_duration,
            "min_shock_duration_entry",
        )
        self._add_label_and_entry(
            parent,
            "Maximum shock duration (ms)",
            4,
            self.settings.max_shock_duration,
            "max_shock_duration_entry",
        )

        ok_button = ttk.Button(parent, text="OK", command=self.write_data)
        cancel_button = ttk.Button(parent, text="Cancel", command=self.window.destroy)

        ok_button.grid(column=0, row=7, pady=5)
        cancel_button.grid(column=1, row=7, pady=5)

    def _add_label_and_entry(self, parent, label_text, row, default_value, entry_attr):
        label = ttk.Label(parent, text=label_text)
        entry = ttk.Entry(parent)
        entry.insert(0, str(default_value))
        setattr(self, entry_attr, entry)

        label.grid(column=0, row=row, columnspan=2, sticky="NW", padx=5)
        entry.grid(column=0, row=row + 1, columnspan=2, sticky="NEW", padx=5)

    def _build_threshold_controls(self, parent):
        frame = ttk.Frame(
            parent, borderwidth=5, relief="ridge", padding=(12, 12, 12, 12)
        )
        frame.grid(column=0, row=6, sticky="NEWS")

        self._add_threshold_control(
            frame,
            self.LOWER_THRESHOLD_LABEL,
            self.lower_threshold_var,
            self.start_low_shock,
            0,
        )
        separator = ttk.Separator(frame, orient=tk.VERTICAL)
        separator.grid(column=1, row=0, rowspan=3, sticky="NS", padx=10)
        self._add_threshold_control(
            frame,
            self.HIGHER_THRESHOLD_LABEL,
            self.higher_threshold_var,
            self.start_high_shock,
            2,
        )

    def _add_threshold_control(self, parent, label_text, var, command, column):
        label = ttk.Label(parent, text=label_text)
        value_label = ttk.Label(parent, textvariable=var)
        button = ttk.Button(parent, text="Start", command=command)

        label.grid(column=column, row=0, sticky="W" if column == 0 else "E")
        value_label.grid(column=column, row=1, sticky="W" if column == 0 else "E")
        button.grid(column=column, row=2, sticky="W" if column == 0 else "E")

    def start_low_shock(self):
        self.logger.log("start_low_shock()")
        self._administer_shock(self.MIN_SHOCK, 1.250, lower=True)

    def start_high_shock(self):
        self.logger.log("start_high_shock()")
        self._administer_shock(self.lower_threshold, self.MAX_SHOCK, lower=False)

    def _administer_shock(self, min: float, max: float, lower: bool):
        self.logger.log(f"administer_shock({min}, {max}, {lower})")

        def put_task():
            nonlocal shock_vals
            current_val = shock_vals.pop(0)
            self.thread_handler.task_queue.put_task(ShockTask(current_val, 1, 3.5))
            self.logger.log(f"{shock_vals}")

            return current_val

        def update():
            nonlocal shock_vals
            self.logger.log(
                f"administer_shock.update() -- thread_handler.task_queue.unfinished_tasks == {self.thread_handler.task_queue.unfinished_tasks}"
            )
            # unfinished = len(shock_vals)
            # if self.thread_handler.task_queue.unfinished_tasks <= 0:
            #     return
            # if self.thread_handler.task_queue.unfinished_tasks > len(shock_vals):
            #     return

            # idx = len(shock_vals) - self.thread_handler.task_queue.unfinished_tasks
            # current_shock = shock_vals[idx]
            if len(shock_vals) <= 0:
                return

            if self.thread_handler.task_done.is_set():
                self.logger.log("task done set")
                self.thread_handler.task_done.clear()
                current_shock = put_task()
                current_shock_text.set(f"Current level: {str(current_shock)} mA")

                if lower:
                    self.lower_threshold = current_shock
                    self.lower_threshold_var.set(f"{str(self.lower_threshold)}mA")
                else:
                    self.higher_threshold = current_shock
                    self.higher_threshold_var.set(f"{str(self.higher_threshold)} mA")

            self.window.after(500, update)

        def stop():
            nonlocal shock_vals
            self.logger.log("====== administer_shock.stop() ======")
            self.thread_handler.halt_event.set()
            self.thread_handler.task_done.clear()
            shock_vals.clear()
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
        print(shock_vals)

        # self.thread_handler.task_queue.unlock()
        # for s in shock_vals:
        #     self.thread_handler.task_queue.put_task(ShockTask(s, 1, 3.5))
        if not self.thread_handler.task_done.is_set():
            self.thread_handler.task_done.set()
        update()

    def write_data(self):
        self.logger.log("write_data()")
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
