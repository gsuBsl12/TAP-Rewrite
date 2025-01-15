import threading
import time


def one():
    while True:
        time.sleep(1)
        print("in one")


def two():
    while True:
        time.sleep(0.5)
        print("in two")


t_one = threading.Thread(target=one)
t_one.start()
t_two = threading.Thread(target=two)
t_two.start()
