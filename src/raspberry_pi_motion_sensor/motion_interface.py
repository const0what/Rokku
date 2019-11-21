import logging
import os
from collections import deque
from logging import config
from multiprocessing import Process
from time import sleep, time

import RPi.GPIO as GPIO
import yaml


def led_on():
    while True:
        GPIO.output(12, GPIO.HIGH)
        sleep(0.1)


class MotionPir:
    """Class implemented to interact with a PIR motion sensor.

    Object will act as a 'mini-alarm system' where it can be 'armed' and
    'disarmed'. Functions set_armed() and set_disarmed() should be used to
    modify object and motion_callback() will allow for object to communicate to
    other objects. when armed.
    """

    def __init__(self, queue, channel_num, motion_sensor_config):
        """ When MotionPir is created it will be inactive, self.armed set to
        false.

        Queue from main is given to object for passing of events happening in
        second thread.
        channel_num is the Broadcom SOC channel number used for input from the
        PIR sensor.

        :param queue:       Notify rpi_out that a real motion trigger has been
                            sensed.
        :param channel_num: The GPIO pin connected to the PIR sensor.
        :param config:      Configuration for motion sensor
        """

        self.armed = False
        self.queue = queue
        self.channel_num = channel_num
        GPIO.setup(self.channel_num, GPIO.IN)
        GPIO.setup(12, GPIO.OUT)

        self.interval = int(motion_sensor_config["INTERVAL"])
        self.trig_thresh = int(motion_sensor_config["TRIG_THRESH"])
        # data structure to compute the time period needed to produce the
        # most recent `self.trig_thresh` number of triggers. If the time period
        # is smaller than `self.interval`, we consider that as a real trigger.
        self.trigger_times = deque([-1.0] * (self.trig_thresh - 1))

        # set up logger
        with open(
            f"{os.path.dirname(__file__)}/../../logger_config.yaml", "r"
        ) as f_obj:
            log_config = yaml.safe_load(f_obj.read())
            config.dictConfig(log_config)
        self.logger = logging.getLogger("MOTION_SENSOR")

        self.led_proc = Process(target=led_on, args=())  # turn on LED

    def motion_callback(self, channel):
        """channel argument is for receiving GPIO input.

        Function runs on different thread than main.
        When object (self.armed) is 'armed' / True, this function will be
        called anytime the Pir sensor is activated. Gives main driver ability
        to see callback from different thread.
        """
        curr_time = time()
        earliest_time = self.trigger_times.popleft()
        self.trigger_times.append(curr_time)
        print("*** PIR Triggered ***")
        if earliest_time > 0 and curr_time - earliest_time < self.interval:
            # Considered a real trigger
            self.logger.info("Motion Detected")
            self.led_proc.start()
            self.queue.put(True)
            self.queue.join()  # block until user acknowledges it

        if self.led_proc is not None:
            self.led_proc.terminate()
        GPIO.output(12, GPIO.LOW)  # turn off LED

    def set_armed(self):
        """Sets Object state to True 'armed'.

        and calls monitor() to initialize GPIO input. Also, GPIO is set up to
        manage callback on second thread to run motion_callback() in response
        to a rising edge
        """
        self.armed = True
        GPIO.add_event_detect(
            self.channel_num, GPIO.RISING, callback=self.motion_callback
        )
        self.logger.info("Rokku ARMED: motion sensor ON")

    def set_disarmed(self):
        """Sets Object state to False 'disarmed'.

        and will stop callbacks from motion_pir by removing event detection.
        """
        self.armed = False
        GPIO.remove_event_detect(self.channel_num)
        self.logger.info("Rokku DISARMED: motion sensor OFF")

    def get_state(self):
        """Return the state of armed / 'alarm system' """
        return self.armed


# TODO Decide where board mode setup belongs
