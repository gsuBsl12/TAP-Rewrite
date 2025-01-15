import tkinter as tk
from tksheet import Sheet
from typing import List

from tap.classes import Trial


class ProfileParameters(tk.Frame):
    def __init__(
        self,
        master,
        rows: int,
        trials: List[Trial] = None,
        intensities: List[int] = None,
        readonly=False,
    ):
        self.rows = rows

        self.notebook = tk.ttk.Notebook(master)

        self.frame1 = tk.ttk.Frame(self.notebook)
        self.frame1.grid_columnconfigure(0, weight=1)
        self.frame1.grid_rowconfigure(0, weight=1)

        self.frame2 = tk.ttk.Frame(self.notebook)
        self.frame2.grid_columnconfigure(0, weight=1)
        self.frame2.grid_rowconfigure(0, weight=1)

        self.sheet = Sheet(
            self.frame1,
            data=[["", "", ""] for r in range(rows)],
            theme="light blue",
            height=520,
            width=480,
        )

        self.sheet.enable_bindings("single_select", "undo", "arrowkeys", "move_columns")
        self.sheet.headers(["Win or Lose", "Shock", "Feedback"])

        self.sheet.dropdown(
            "A",
            values=["Win", "Lose"],
            set_value="",
            selection_function=self.enable_dropdowns,
        )
        self.sheet.dropdown("B", values=list(range(1, 11)), set_value="")
        self.sheet.dropdown("C", values=list(range(1, 11)), set_value="")

        if trials is not None:
            for i, trial in enumerate(trials):
                self.sheet[i].data = [trial.wl, trial.shock, trial.feedback]
                self.enable_dropdowns(
                    # Pass anonymous event object with value and row attributes
                    event=type("", (object,), {"value": trial.wl, "row": i})()
                )

        self.intensities = Sheet(
            self.frame2,
            data=[[i * 5] for i in range(11, 21)],
            theme="light blue",
            height=520,
            width=480,
        )
        self.intensities.enable_bindings(
            "edit_cell", "single_select", "undo", "arrowkeys", "move_columns"
        )
        self.intensities.headers(["Intensity"])
        self.intensities.align_columns(columns=0, align="c")

        if intensities is not None:
            for i, intensity in enumerate(intensities):
                self.intensities[i].data = str(intensity)

        self.frame1.grid(row=0, column=0, sticky="nswe")
        self.frame2.grid(row=0, column=0, sticky="nswe")
        self.sheet.grid(row=0, column=0, sticky="nswe")
        self.intensities.grid(row=0, column=0, sticky="nswe")

        self.notebook.add(self.frame1, text="Trial Data")
        self.notebook.add(self.frame2, text="Corresponding Intensities")
        self.notebook.grid(row=0, column=0, sticky="nswe")

        if readonly:
            self.sheet.disable_bindings()
            self.sheet.readonly(self.sheet["A1"].expand())
            self.intensities.disable_bindings()
            self.intensities.readonly(self.intensities["A1"].expand())

    def enable_dropdowns(self, event=None):
        if event is None:
            return

        is_win = event.value == "Win"
        cells = [[event.row, 1], [event.row, 2]]

        self.sheet.readonly_cells(cells=cells, readonly=is_win)

        if is_win:
            self.sheet.highlight_cells(cells=cells, bg="gray", fg="gray")
        else:
            self.sheet.highlight_cells(cells=cells, bg=None, fg=None)

    def get_data(self):
        if self.rows == 1:
            return (
                [self.sheet["A1"].expand().options(header=False, index=False).data],
                self.intensities["A1"].expand().options(header=False, index=False).data,
            )
        else:
            return (
                self.sheet["A1"].expand().options(header=False, index=False).data,
                self.intensities["A1"].expand().options(header=False, index=False).data,
            )
