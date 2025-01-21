import os
import typing
import queue

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


# https://stackoverflow.com/questions/6517953/clear-all-items-from-the-queue
class Queue(queue.Queue):
    def clear(self):
        with self.mutex:
            unfinished = self.unfinished_tasks - len(self.queue)
            if unfinished <= 0:
                if unfinished < 0:
                    raise ValueError("task_done() called too many times")
                self.all_tasks_done.notify_all()
            self.unfinished_tasks = unfinished
            self.queue.clear()
            self.not_full.notify_all()


class ThreadHandler(typing.NamedTuple):
    task_queue: Queue
    halt_event: Event
    kill_event: Event
