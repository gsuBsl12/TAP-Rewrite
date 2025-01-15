import nidaqmx

from time import sleep

with nidaqmx.Task() as task:
    task.ao_channels.add_ao_voltage_chan("Dev1/ao0")
    task.start()
    task.write(1.0)
    task.stop()

with nidaqmx.Task() as task:
    task.do_channels.add_do_chan("Dev1/port0/line0:0")
    task.start()
    task.write(True)
    task.stop()

sleep(1)

with nidaqmx.Task() as task:
    task.do_channels.add_do_chan("Dev1/port0/line0:0")
    task.start()
    task.write(False)
    task.stop()

with nidaqmx.Task() as task:
    task.ao_channels.add_ao_voltage_chan("Dev1/ao0")
    task.start()
    task.write(0.0)
    task.stop()
