import time
import threading
import queue
import line_profiler
import nidaqmx
from nidaqmx.stream_writers import AnalogSingleChannelWriter, DigitalSingleChannelWriter

from tap.classes import ThreadHandler, ShockTask, Logger


class DAQ(threading.Thread):
    def __init__(
        self,
        thread_handler: ThreadHandler,
        logger: Logger,
        device_name="Dev1",
        pin="ao0",
        debug=False,
    ):
        super(DAQ, self).__init__(target=self.run)
        self.thread_handler = thread_handler
        self.logger = logger

        self.device_name = device_name
        self.pin = pin
        self.analog_output_name = device_name + "/" + pin

        self.debug = debug

        if not self.debug:
            # Configure reusable tasks and stream writers
            self.ao_task, self.ao_writer = self._configure_ao_task()
            self.do_task, self.do_writer = self._configure_do_task()

        self.start()

    def _configure_ao_task(self):
        """Configure and return an analog output task with a stream writer."""
        task = nidaqmx.Task()
        task.ao_channels.add_ao_voltage_chan(
            self.analog_output_name, min_val=0.0, max_val=2.5
        )
        writer = AnalogSingleChannelWriter(task.out_stream)
        return task, writer

    def _configure_do_task(self):
        """Configure and return a digital output task with a stream writer."""
        task = nidaqmx.Task()
        task.do_channels.add_do_chan(f"{self.device_name}/port0/line0:0")
        writer = DigitalSingleChannelWriter(task.out_stream)
        return task, writer

    def write_zeroes(self):
        """Reset both analog and digital outputs to zero or off."""
        self.logger.log("Writing zeroes to DAQ")
        try:
            # Write zeros to analog output using the stream writer
            self.logger.log("Writing AO 0.0")
            self.ao_writer.write_one_sample(0.0)

            # Write False to digital output using the stream writer
            self.logger.log("Writing DO OFF")
            self.do_writer.write_one_sample_one_line(False)
        except Exception as e:
            self.logger.log(f"Error in write_zeroes: {e}")

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
        """Main thread loop for processing tasks."""
        while not self.thread_handler.kill_event.is_set():
            self.watch_queue() if self.debug else self.test_watch_queue()

    def test_watch_queue(self):
        while (
            not self.thread_handler.halt_event.is_set()
            and not self.thread_handler.kill_event.is_set()
        ):
            try:
                shock_task: ShockTask = self.thread_handler.task_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if self.thread_handler.kill_event.is_set():
                self.logger.log("Kill event is set. Exiting watch_queue loop.")
                break
            if self.thread_handler.halt_event.is_set():
                self.logger.log("Halt event is set. Skipping current task.")
                self.thread_handler.task_queue.task_done()
                continue
            if self.thread_handler.task_queue.single_lock:
                self.logger.log("Queue is locked")
                self.thread_handler.task_queue.clear()

            self.logger.log("TASK RECEIVED =========== QUEUE READ")
            self.logger.log(f"Current task: {str(shock_task)}")
            self.logger.log_queue(self.thread_handler.task_queue)
            volts = self.current_to_volts(shock_task.shock)

            try:
                self.logger.log(f"Writing AO {volts}")
                self.logger.log("Writing DO ON")

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

                self.thread_handler.task_done.set()
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

    @line_profiler.profile
    def watch_queue(self):
        while (
            not self.thread_handler.halt_event.is_set()
            and not self.thread_handler.kill_event.is_set()
        ):
            try:
                # Use blocking mode to wait for a task
                shock_task: ShockTask = self.thread_handler.task_queue.get(timeout=1.0)
            except queue.Empty:
                # This block will rarely run unless the queue is improperly configured
                continue

            # Check halt_event and kill_event before proceeding
            if self.thread_handler.kill_event.is_set():
                self.logger.log("Kill event is set. Exiting watch_queue loop.")
                break
            if self.thread_handler.halt_event.is_set():
                self.logger.log("Halt event is set. Skipping current task.")
                self.thread_handler.task_queue.task_done()
                continue
            # This may be unnecessary
            if self.thread_handler.task_queue.single_lock:
                self.logger.log("Queue is locked")
                self.thread_handler.task_queue.clear()

            self.logger.log("TASK RECEIVED =========== QUEUE READ")
            self.logger.log(f"Current task: {str(shock_task)}")
            self.logger.log_queue(self.thread_handler.task_queue)
            volts = self.current_to_volts(shock_task.shock)

            try:
                # Write analog output voltage
                self.logger.log(f"Writing AO {volts}")
                self.ao_writer.write_one_sample(volts, timeout=0)

                # Write digital output ON
                self.logger.log("Writing DO ON")
                self.do_writer.write_one_sample_one_line(True, timeout=0)

                # Wait for the duration of the shock
                self.logger.log(f"Waiting {shock_task.duration}")
                start = time.time()
                self.thread_handler.halt_event.wait(shock_task.duration)
                self.logger.log(f"Shocked for {time.time() - start}s")

                # Reset outputs
                self.write_zeroes()

                # Cooldown period
                self.logger.log(f"Waiting {shock_task.cooldown}")
                start = time.time()
                self.thread_handler.halt_event.wait(shock_task.cooldown)
                self.logger.log(f"Cooled down for {time.time() - start}s")

                self.thread_handler.task_done.set()
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
