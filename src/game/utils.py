import pandas as pd
import numpy as np
from enum import Enum

class GameState(Enum):
    START = 1
    READY = 2
    HOLD = 3
    SHOCK = 4

class ErrorMessage(Enum):
    WAIT_TO_START = "Waited too long to press"
    WAIT_TOO_LONG = "Waited too long"
    RELEASE_TOO_SOON = "Released spacebar too soon"
    WAIT_TO_SHOCK = "Waited too long to shock"
    SHOCK_TOO_LONG = "Held shock button too long"

class Trial(object):
    def __init__(self, wl, shock, feedback):
        self.wl = wl
        self.shock = shock
        self.feedback = feedback

class DataRow(object):
    def __init__(self, trial: int):
        self.trial = trial
        self.wl = ''
        self.shock_intensity = '---'
        self.shock_duration = '-----'
        self.reaction_time = ''
    
    def get_row(self):
        return self.trial, self.wl, self.shock_intensity, self.shock_duration, self.reaction_time

class Error(object):
    def __init__(self, trial: int):
        self.trial = trial
        self.errors = []
    
    def add_error(self, error: ErrorMessage):
        self.errors.append(error)

class Data(object):
    ''' Main data object '''
    def __init__(self, subject_id: int, lower_shock_threshold: float, upper_shock_threshold: float):
        self.subject_id = subject_id
        self.data_headers = ['Trial', 'W/L', 'Shock Intensity', 'Shock Duration', 'Reaction Time']
        self.data_rows = []
        self.lower_shock_threshold = lower_shock_threshold
        self.upper_shock_threshold = upper_shock_threshold
        self.errors = []

        self.current_data_row = None
        self.current_error = None

    def generate_new_data(self, trial: int):
        self.generate_new_data_row(trial)
        self.generate_new_error(trial)

    def save_and_flush_data(self):
        self.save_and_flush_data_row()
        self.save_and_flush_error()

    def generate_new_error(self, trial: int):
        self.current_error = Error(trial)
    
    def save_and_flush_error(self):
        self.append_error(self.current_error)
        self.generate_new_error(self.current_error.trial + 1)
    
    def append_error(self, error: Error):
        self.errors.append(error)
        print(self.errors)

    def generate_new_data_row(self, trial: int):
        self.current_data_row = DataRow(trial)

    def save_and_flush_data_row(self):
        self.append_data_row(self.current_data_row)
        self.generate_new_data_row(self.current_data_row.trial + 1)

    def append_data_row(self, dr: DataRow):
        for item in dr.get_row():
            self.data_rows.append(item)
        print(self.data_rows)

    def get_data_frame(self) -> pd.DataFrame:
        df = np.empty((0,5))
        for i in range(0, len(self.data_rows), 5):
            dr = []
            for j in range(i, i+5):
                dr.append(self.data_rows[j])
            df = np.append(df, np.array([dr]), axis=0)

        return pd.DataFrame(df)
    
    def get_error_data(self):
        error_data = {i.name: 0 for i in ErrorMessage}
        for error_obj in self.errors:
            for error in error_obj.errors:
                if error_data[error]:
                    error_data[error] += 1
        print(error_data)
        return error_data

    def save_data(self, filename: str):
        if not filename: return

        data = self.get_data_frame()
        data.to_csv(filename, sep='\t', encoding='utf-8', index=False)

        errors = self.get_error_data()
        with open(filename, 'w') as file:
            for error_line in errors:
                print(error_line)
                # file.write('%s: %s' % ())