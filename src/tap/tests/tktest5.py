import tkinter as tk
from tkinter import ttk


class Example(tk.Toplevel):
    def __init__(self, parent):
        self.lower_threshold = 1000
        self.higher_threshold = 1000

        self.window = tk.Toplevel(parent)
        self.window.geometry("500x300")
        self.window.title("Subject Threshold")

        content = ttk.Frame(self.window, padding=(12, 12, 12, 12))
        frame = ttk.Frame(
            content,
            borderwidth=5,
            relief="ridge",
            width=300,
            height=300,
            padding=(12, 12, 12, 12),
        )

        subject_id_label = ttk.Label(content, text="Subject ID")
        self.subject_id_entry = ttk.Entry(content)

        set_lower_level = ttk.Label(frame, text="Set Lower Level")
        self.lower_threshold_var = tk.StringVar(
            value=f"{str(self.lower_threshold / 1000)} mA"
        )
        lower_threshold_label = ttk.Label(frame, textvariable=self.lower_threshold_var)
        start_lower_level = ttk.Button(
            frame,
            text="Start",
            command=None,
        )

        separator = ttk.Separator(frame, orient=tk.VERTICAL)

        set_higher_level = ttk.Label(frame, text="Set Higher Level")
        self.higher_threshold_var = tk.StringVar(
            value=f"{str(self.higher_threshold / 1000)} mA"
        )
        higher_threshold_label = ttk.Label(
            frame, textvariable=self.higher_threshold_var
        )
        start_higher_level = ttk.Button(
            frame,
            text="Start",
            command=None,
        )

        ok = ttk.Button(content, text="OK", command=None)
        cancel = ttk.Button(
            content,
            text="Cancel",
            command=self.window.destroy,
        )

        content.grid(column=0, row=0, sticky="NEWS")
        frame.grid(column=0, row=0, columnspan=3, rowspan=3, sticky="NEWS")
        subject_id_label.grid(column=3, row=0, columnspan=2, sticky="NW", padx=5)
        self.subject_id_entry.grid(
            column=3, row=1, columnspan=2, sticky="NEW", pady=5, padx=5
        )

        set_lower_level.grid(column=0, row=0, sticky="W")
        lower_threshold_label.grid(column=0, row=1, sticky="W")
        start_lower_level.grid(column=0, row=2, sticky="W")

        separator.grid(column=1, row=0, rowspan=3, sticky="NS", padx=10)
        # separator.place(relx=0.5, rely=0, relwidth=0.2, relheight=1)

        set_higher_level.grid(column=2, row=0, sticky="E")
        higher_threshold_label.grid(column=2, row=1, sticky="E")
        start_higher_level.grid(column=2, row=2, sticky="E")

        ok.grid(column=3, row=2)
        cancel.grid(column=4, row=2)

        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        self.window.minsize(500, 300)

        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=3)
        content.columnconfigure(2, weight=3)
        content.columnconfigure(3, weight=1)
        content.columnconfigure(4, weight=1)
        content.rowconfigure(1, weight=1)


if __name__ == "__main__":
    root = tk.Tk()
    Example(root)
    root.mainloop()
