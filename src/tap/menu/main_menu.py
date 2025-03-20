import os
import pathlib
import pickle
import tkinter as tk
import dataclasses
import threading
import webbrowser

import gc
import line_profiler

from tkinter import filedialog, messagebox, simpledialog

from tap.game import game
from tap.menu.profile_parameters import ProfileParameters
from tap.menu.utils import reform_data, reform_intensities
from tap.menu.subject_threshold import SubjectThreshold
from tap.classes import Settings, ThreadHandler, Logger


class MainMenu(threading.Thread):
    @line_profiler.profile
    def __init__(self, thread_handler: ThreadHandler, logger: Logger) -> None:
        super(MainMenu, self).__init__(target=self.run)
        self.start()

        self.thread_handler = thread_handler
        self.logger = logger

        self.settings = Settings()

    def create_new_instruction(self, instruction="Enter instructions here"):
        self.logger.log("create_new_instruction")

        def ok():
            self.logger.log("create_new_instruction.ok()")
            self.settings.instruction = instruction_text.get("1.0", tk.END)
            new_instruction.destroy()

        def cancel():
            self.logger.log("create_new_instruction.cancel()")
            new_instruction.destroy()

        def clear():
            self.logger.log("create_new_instruction.clear()")
            instruction_text.delete("1.0", tk.END)

        new_instruction = tk.Toplevel(self.window)
        new_instruction.title("Instructions")
        new_instruction.resizable(False, False)

        new_instruction.rowconfigure(0, minsize=400, weight=1)
        new_instruction.columnconfigure(0, minsize=200, weight=1)

        instruction_text = tk.Text(new_instruction)
        btn_frame = tk.Frame(new_instruction, bd=2)

        ok_btn = tk.Button(btn_frame, text="Ok", command=ok)
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=cancel)
        clear_btn = tk.Button(btn_frame, text="Clear Text", command=clear)

        ok_btn.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        cancel_btn.grid(row=1, column=0, sticky="ew", padx=5)
        clear_btn.grid(row=3, column=0, sticky="ew", padx=5, pady=20)

        instruction_text.grid(row=0, column=0, sticky="nsew")
        btn_frame.grid(row=0, column=1, sticky="ns")

        instruction_text.insert("1.0", instruction)

    def run_official(self, trials):
        self.logger.log(f"run_official({trials})")
        data = game.play(self.thread_handler, self.logger, self.settings, trials)
        df = data.get_data_frame()
        # throw error here
        if df.empty:
            return
        data.save_data(os.getcwd(), self.settings.subject_id)

    def run_experiment(self):
        if len(self.settings.trials) <= 0:
            self.show_message("You must set the number of trials!")
            return
        if not self.settings.subject_id:
            self.show_message("You must set the subject ID!")
            return

        self.run_official(self.settings.trials)

    def show_about_info(self):
        self.show_message(
            """This is a rewrite of the TAP software in Python using the NI DAQ USB-6001 Module.

To exit the program, press CTRL-C.

Maximum shock intensity is 2.475 mA.
            """
        )

    def set_subject_threshold(self):
        self.logger.log("set_subject_threshold()")
        if not self.settings.trials:
            self.show_message("You must open an experiment first.")
            return
        SubjectThreshold(self.window, self.thread_handler, self.settings, self.logger)

    def get_trial_count(self):
        trial_count = simpledialog.askinteger("Profile Setup", "Number of Trials: ")

        # Fix
        # Checkbox for "Enable RCAP"
        # rcap_checkbox = tk.Checkbutton(window, text='Enable RCAP',variable=var1, onvalue=1, offvalue=0, command=print_selection)
        # rcap_checkbox.grid(row=1, column=4)
        # self.state['trial-count'] = number_of_trials if not None else 0
        # update_variable("trials", number_of_trials, "experiment")

        if trial_count is not None:
            self.profile_parameters(trial_count)

    @line_profiler.profile
    def profile_parameters(self, trial_count: int, edit=False):
        def ok():
            try:
                data = profile_parameters.get_data()
                trials = [reform_data(x) for x in data[0]]
                intensities = [reform_intensities(x) for x in data[1]]

                if None in trials or None in intensities or len(intensities) != 10:
                    raise ValueError("Malformed data.")

                self.settings.trials = trials
                self.settings.intensities = intensities
                profile_parameters_window.destroy()
                self.display_trials()

            except ValueError:
                self.show_message(
                    "There was an error creating the trials. Check your entries again."
                )

        if not trial_count or trial_count <= 0:
            self.show_message("You must first specify trial count!")
            return

        profile_parameters_window = tk.Toplevel(self.window)
        # profile_parameters_window.protocol("WM_DELETE_WINDOW", self.ask_to_exit)
        profile_parameters = ProfileParameters(
            profile_parameters_window,
            trial_count,
            (self.settings.trials if edit else None),
            (self.settings.intensities if edit else None),
        )

        ok_btn = tk.Button(
            profile_parameters_window,
            text="Ok",
            command=ok,
        )
        ok_btn.grid(row=trial_count + 2, column=0)

    def display_trials(self):
        ProfileParameters(
            self.window,
            len(self.settings.trials),
            self.settings.trials,
            self.settings.intensities,
            readonly=True,
        )

    ### File utilities

    def save_experiment(self):
        filetypes = [("TAP files", "*.tap"), ("All files", "*.*")]
        file = filedialog.asksaveasfile(
            mode="wb",
            filetypes=filetypes,
            initialfile=self.settings.filename,
            defaultextension=".tap",
        )
        if not file:
            return
        try:
            self.settings.working_directory = pathlib.Path(file.name).parent.resolve()
            self.settings.filename = file.name
            pickle.dump(dataclasses.asdict(self.settings), file)
        except Exception:
            self.show_message("There was an error saving the file.")
        file.close()

    def open_experiment(self):
        filetypes = [("TAP files", "*.tap"), ("All files", "*.*")]
        file = filedialog.askopenfile(
            mode="rb", filetypes=filetypes, defaultextension=".tap"
        )
        if not file:
            return
        try:
            settings_dict = pickle.load(file)
            self.settings = Settings(**settings_dict)  # Double asterick for kwargs
            self.settings.filename = file.name
            self.settings.working_directory = pathlib.Path(file.name).parent.resolve()
            self.display_trials()
        except Exception:
            self.show_message("There was an error opening the file.")
        file.close()

    def show_message(self, message: str):
        messagebox.showinfo("Notification", message)

    def ask_to_exit(self):
        if messagebox.askyesnocancel("Exit", "Are you sure you want to exit?"):
            self.thread_handler.kill_event.set()
            self.window.destroy()
            # TODO this is probably bad
            self.window = None
            gc.collect()

    @line_profiler.profile
    def run(self):
        window = tk.Tk()
        window.title("TAP Python Edition")
        window.geometry("500x500")
        window.resizable(width=True, height=True)

        self.window = window

        # Cofigure sizing for rows and columns
        self.window.rowconfigure(1, minsize=800, weight=1)
        self.window.columnconfigure(0, minsize=800, weight=1)

        # Menu bar
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)

        # Menu options in menu bar
        experiment_menu = tk.Menu(menubar, tearoff=0)
        create_new_menu = tk.Menu(menubar, tearoff=0)
        edit_current_menu = tk.Menu(experiment_menu, tearoff=0)
        run_menu = tk.Menu(experiment_menu, tearoff=0)

        # Create main menu
        threshold_menu = tk.Menu(menubar, tearoff=0)

        # Main menu options
        menubar.add_cascade(menu=experiment_menu, label="Experiment")
        menubar.add_cascade(menu=threshold_menu, label="Threshold")
        menubar.add_command(label="About", command=self.show_about_info)
        menubar.add_command(
            label="Docs",
            command=lambda: webbrowser.open_new(
                "https://github.com/trexlernoah/TAP-Rewrite/blob/main/README.md"
            ),
        )

        # Experiment dropdown menu options
        experiment_menu.add_cascade(label="Create New", menu=create_new_menu)
        # Open experiment
        experiment_menu.add_command(
            label="Open Experiment", command=self.open_experiment
        )

        # "Create New" dropdown menu options
        create_new_menu.add_command(
            label="Instruction", command=self.create_new_instruction
        )
        create_new_menu.add_command(label="Experiment", command=self.get_trial_count)

        # "Edit Current" dropdown menu options
        experiment_menu.add_cascade(label="Edit Current", menu=edit_current_menu)
        edit_current_menu.add_command(
            label="Instruction",
            command=lambda: self.create_new_instruction(self.settings.instruction),
        )
        edit_current_menu.add_command(
            label="Experiment",
            command=lambda: self.profile_parameters(
                len(self.settings.trials), edit=True
            ),
        )
        experiment_menu.add_separator()

        # "Save Experiment" dropdown menu option
        experiment_menu.add_command(
            label="Save Experiment", command=self.save_experiment
        )
        experiment_menu.add_separator()

        # Run dropdown menu options
        experiment_menu.add_cascade(label="Run", menu=run_menu)
        run_menu.add_command(label="Official", command=self.run_experiment)
        experiment_menu.add_separator()

        # Exit dropdown menu option
        experiment_menu.add_command(label="Exit", command=self.ask_to_exit)

        # Threshold dropdown menu options
        threshold_menu.add_command(
            label="Set Subject Threshold", command=self.set_subject_threshold
        )

        # Ask to close
        self.window.protocol("WM_DELETE_WINDOW", self.ask_to_exit)

        # Start menu
        self.window.mainloop()
