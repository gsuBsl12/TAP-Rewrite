import time
import threading
import nidaqmx
import queue
import sys

import line_profiler

from tap.classes import ThreadHandler, ShockTask, Logger


class DAQ(threading.Thread):
    def __init__(
        self,
        thread_handler: ThreadHandler,
        logger: Logger,
        device_name="Dev1",
        pin="ao0",
    ):
        super(DAQ, self).__init__(target=self.run)
        self.thread_handler = thread_handler
        self.logger = logger

        self.device_name = device_name
        self.pin = pin
        self.analog_ouput_name = device_name + "/" + pin

        self.start()

    def current_to_volts(self, mA: float) -> float:
        self.logger.log(f"Called DAQ.current_to_volts(mA={mA})")
        volts = mA / 2
        # Failsafe for out-of-bounds values
        if volts > 2.5 or volts < 0.0:
            self.logger.log("Returning DAQ.current_to_volts 0.0")
            return 0.0
        self.logger.log(f"Returning DAQ.current_to_volts {volts}")
        return volts

    def run(self):
        while not self.thread_handler.kill_event.is_set():
            self.watch_queue()

    def test_watch_queue(self):
        while (
            not self.thread_handler.halt_event.is_set()
            and not self.thread_handler.kill_event.is_set()
        ):
            try:
                shock_task: ShockTask = self.thread_handler.task_queue.get(timeout=0.1)
            except queue.Empty:
                pass
            else:
                if self.thread_handler.task_queue.single_lock:
                    self.logger.log("Queue is locked")
                    self.thread_handler.task_queue.clear()

                self.logger.log("TASK RECEIVED =========== QUEUE READ")
                self.logger.log(f"Current task: {str(shock_task)}")
                self.logger.log_queue(self.thread_handler.task_queue)
                volts = self.current_to_volts(shock_task.shock)
                self.logger.log(f"Writing AO {volts}")
                self.logger.log("Writing DO ON")
                try:
                    self.logger.log(f"Waiting {shock_task.duration}")
                    start = time.time()
                    self.thread_handler.halt_event.wait(shock_task.duration)
                    self.logger.log(f"Shocked for {time.time() - start}s")

                    self.logger.log("Writing DO OFF")
                    self.logger.log("Writing AO 0.0")

                    self.logger.log(f"Waiting {shock_task.cooldown}")
                    start = time.time()
                    self.thread_handler.halt_event.wait(shock_task.cooldown)
                    self.logger.log(f"Cooled down for {time.time() - start}s")
                except Exception as e:
                    self.logger.log("EXCEPTION %s" % e)
                    self.logger.log("Setting halt event")
                    self.thread_handler.halt_event.set()

                self.logger.log("Setting task done")
                self.thread_handler.task_queue.task_done()
        self.logger.log("Writing DO OFF")
        self.logger.log("Writing AO 0.0")
        self.logger.log("Clearing queue and halt event status")
        self.thread_handler.task_queue.clear()
        self.thread_handler.halt_event.clear()

    def write_zeroes(self, depth=0):
        if depth > 25:
            sys.exit(1)  # Switch this exit
        self.logger.log("Writing zeroes to DAQ")
        try:
            self.logger.log("Writing DO OFF")
            try:
                task = nidaqmx.Task()
                task.do_channels.add_do_chan("Dev1/port0/line0:0")
                task.start()
                task.write(False)
                task.stop()
            except Exception as e:
                self.logger.log("NIDAQMX DO EXCEPTION %s" % e)
                self.write_zeroes(depth + 1)

            self.logger.log("Writing AO 0.0")
            try:
                task = nidaqmx.Task()
                task.ao_channels.add_ao_voltage_chan(
                    "Dev1/ao0", min_val=0.0, max_val=2.5
                )
                task.start()
                task.write(0.0)
                task.stop()
            except Exception as e:
                self.logger.log("NIDAQMX AO EXCEPTION %s" % e)
                self.write_zeroes(depth + 1)

        except Exception as e:
            self.logger.log("EXCEPTION %s" % e)

    @line_profiler.profile
    def watch_queue(self):
        while (
            not self.thread_handler.halt_event.is_set()
            and not self.thread_handler.kill_event.is_set()
        ):
            try:
                # See if there is an event listener
                # Getting rid of timeout and setting block=False results in too much processing in this while loop
                shock_task: ShockTask = self.thread_handler.task_queue.get(timeout=0.1)
            except queue.Empty:
                pass
            else:
                # This may be unnecessary
                if self.thread_handler.task_queue.single_lock:
                    self.logger.log("Queue is locked")
                    self.thread_handler.task_queue.clear()

                self.logger.log("TASK RECEIVED =========== QUEUE READ")
                self.logger.log(f"Current task: {str(shock_task)}")
                self.logger.log_queue(self.thread_handler.task_queue)
                volts = self.current_to_volts(shock_task.shock)

                try:
                    self.logger.log(f"Writing AO {volts}")
                    try:
                        task = nidaqmx.Task()
                        task.ao_channels.add_ao_voltage_chan(
                            "Dev1/ao0", min_val=0.0, max_val=2.5
                        )
                        task.start()
                        task.write(volts)
                        task.stop()
                    except Exception as e:
                        self.logger.log("NIDAQMX DO EXCEPTION %s" % e)
                        self.write_zeroes()

                    self.logger.log("Writing DO ON")
                    try:
                        task = nidaqmx.Task()
                        task.do_channels.add_do_chan("Dev1/port0/line0:0")
                        task.start()
                        task.write(True)
                        task.stop()
                    except Exception as e:
                        self.logger.log("NIDAQMX AO EXCEPTION %s" % e)
                        self.write_zeroes()

                    self.logger.log(f"Waiting {shock_task.duration}")
                    start = time.time()
                    self.thread_handler.halt_event.wait(shock_task.duration)
                    self.logger.log(f"Shocked for {time.time() - start}s")

                    self.write_zeroes()

                    self.logger.log(f"Waiting {shock_task.cooldown}")
                    start = time.time()
                    self.thread_handler.halt_event.wait(shock_task.cooldown)
                    self.logger.log(f"Cooled down for {time.time() - start}s")
                except Exception as e:
                    self.logger.log("EXCEPTION %s" % e)
                    self.logger.log("Setting halt event")
                    self.thread_handler.halt_event.set()

                self.logger.log("Setting task done")
                self.thread_handler.task_queue.task_done()
        # Clean up here
        self.write_zeroes()
        self.logger.log("Clearing queue and halt event status")
        self.thread_handler.task_queue.clear()
        self.thread_handler.halt_event.clear()
