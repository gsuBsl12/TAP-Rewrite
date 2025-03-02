import os
import typing
import queue
import datetime

import pandas as pd
import numpy as np

from dataclasses import dataclass, astuple, field
from typing import List
from enum import Enum
from threading import Event


class GameState(Enum):
    START = 1
    READY = 2
    HOLD = 3
    SHOCK = 4


class ErrorMessage(Enum):
    WAIT_TO_START = "Waited too long to press"
    WAIT_TOO_LONG = "Waited too long to release"
    RELEASE_TOO_SOON = "Released spacebar too soon"
    WAIT_TO_SHOCK = "Waited too long to shock"
    SHOCK_TOO_LONG = "Held shock button too long"


class Trial(typing.NamedTuple):
    wl: str
    shock: int
    feedback: int


class ShockTask(typing.NamedTuple):
    shock: float
    duration: float
    cooldown: float


@dataclass
class DataRow:
    trial: int
    wl: str = ""
    shock_intensity: str = "---"
    shock_duration: str = "-----"
    reaction_time: str = ""


class Data:
    def __init__(self):
        self.data_rows: List[DataRow] = []
        self.errors: List[ErrorMessage] = []
        self.current_data_row = DataRow(1)

    def finish_trial(self):
        self.data_rows.append(self.current_data_row)
        self.current_data_row = DataRow(self.current_data_row.trial + 1)

    def add_error(self, error: ErrorMessage):
        self.errors.append(error)

    def get_data_frame(self) -> pd.DataFrame:
        df = np.empty((0, 5))

        for data_row in self.data_rows:
            df = np.append(df, np.array([astuple(data_row)]), axis=0)

        df = pd.DataFrame(df)
        df.columns = [
            "Trial          ",
            "W/L            ",
            "Shock Intensity",
            "Shock Duration ",
            "Reaction Time  ",
        ]

        return df

    def get_error_data(self):
        # Get dict of ErrorMessage enum keys with value set at 0
        error_data = {i.name: 0 for i in ErrorMessage}
        for error in self.errors:
            error_data[error.name] += 1
        return error_data

    def save_data(self, wd: str, subject_id: str):
        if not wd:
            wd = os.path.dirname(os.path.realpath(__file__))

        filename = f"{wd}/{subject_id}.dat"

        data = self.get_data_frame()

        for col in data:
            data[col] = data[col].str[0:].apply("{:15}".format)

        data.to_csv(filename, sep="\t", encoding="utf-8", index=False)

        errors = self.get_error_data()

        with open(filename, "r") as file:
            save = file.read()
        with open(filename, "w") as file:
            file.write(f"Subject: {subject_id}\n\n")
            file.write(save)
            file.write("\n\n")
            for error, count in errors.items():
                file.write(f"{ErrorMessage[error].value}: {count} time(s)\n")


@dataclass(kw_only=True)
class Settings:
    filename: str = ""
    working_directory: str = ""
    subject_id: str = ""
    lower_threshold: float = 0.0
    higher_threshold: float = 0.0
    min_shock_duration: int = 1000
    max_shock_duration: int = 1000
    instruction: str = ""
    intensities: List[int] = field(default_factory=list)
    trials: List[Trial] = field(default_factory=list)

class Logger:
    def __init__(self, debug_on: bool):
        self.debug_on = debug_on

        if not self.debug_on:
            return

        self.wd = os.getcwd()
        timestamp = datetime.datetime.now()
        self.filename = self.wd + "/" + timestamp.strftime("%Y-%m-%d-%H-%M-%S") + ".log"

        try:
            with open(self.filename, "x") as f:
                print("File created")
        except FileExistsError:
            print("Unable to create logger file")

    def log(self, text):
        if not self.debug_on:
            return
        with open(self.filename, "a") as f:
            timestamp = datetime.datetime.now()
            f.write(f"[{timestamp.strftime('%H:%M:%S.%f')}]: ")
            f.write(text)
            f.write("\n\n")

    def log_queue(self, queue):
        if not self.debug_on:
            return
        with open(self.filename, "a") as f:
            timestamp = datetime.datetime.now()
            f.write(f"[{timestamp.strftime('%H:%M:%S.%f')}]: QUEUE state\n")
            for shock_task in list(queue.queue):
                f.write(str(shock_task))
                f.write("\n")
            f.write("\n\n")


# https://stackoverflow.com/questions/6517953/clear-all-items-from-the-queue
class Queue(queue.Queue):
    def __init__(self, logger: Logger):
        self.logger = logger
        # If single lock is enabled, only allow one task
        self.single_lock = True
        super(Queue, self).__init__(maxsize=1)

    def lock(self):
        self.logger.log("Locking queue.")
        if self.single_lock and self.maxsize == 1:
            self.logger.log("Queue already locked.")
            return
        self.clear()
        self.single_lock = True
        self.maxsize = 1
        self.logger.log("Queue locked.")

    def unlock(self):
        self.logger.log("Unlocking queue.")
        if not self.single_lock and self.maxsize == 0:
            self.logger.log("Queue already unlocked.")
            return
        self.clear()
        self.single_lock = False
        self.maxsize = 0
        self.logger.log("Queue unlocked.")

    def put_task(self, item):
        self.logger.log(f"Putting task {item}.")
        try:
            super(Queue, self).put(item)
            self.logger.log("Task put.")
            return True
        except queue.Full:
            self.logger.log("Queue is full!")
        except queue.ShutDown:
            self.logger.log("Queue is shut down!")
        self.logger.log("Unable to put task in queue.")
        return False

    def clear(self):
        self.logger.log("Clearing queue.")
        with self.mutex:
            unfinished = self.unfinished_tasks - len(self.queue)
            if unfinished <= 0:
                if unfinished < 0:
                    self.logger.log("task_done() called too many times.")
                    raise ValueError("task_done() called too many times")
                self.all_tasks_done.notify_all()
            self.unfinished_tasks = unfinished
            self.queue.clear()
            self.not_full.notify_all()


class ThreadHandler(typing.NamedTuple):
    task_queue: Queue
    halt_event: Event
    kill_event: Event
