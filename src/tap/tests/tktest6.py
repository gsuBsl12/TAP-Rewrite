import tkinter as tk
from tkinter import messagebox


class Example(tk.Toplevel):
    def __init__(self, parent):
        self.lower_threshold = 1000
        self.higher_threshold = 1000

        self.window = tk.Toplevel(parent)
        self.window.geometry("500x300")
        self.window.title("Subject Threshold")

        msg = messagebox.Message(icon=messagebox.WARNING)
        msg.show()


if __name__ == "__main__":
    root = tk.Tk()
    Example(root)
    root.mainloop()
