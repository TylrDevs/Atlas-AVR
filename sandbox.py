# Team Atlas 78867A AVR 23'
import json, time, math, base64
from bell.avr.mqtt.client import MQTTModule
from bell.avr.mqtt.payloads import *
from bell.avr.utils import decorators
from loguru import logger
from threading import Thread

class Sandbox(MQTTModule):
    def __init__(self) -> None:
        super().__init__()  

    ##### Variable Setup #####

        self.topic_map = {
            "avr/thermal/reading": self.process_thermal_payload,
            "avr/apriltags/visible": self.process_apriltag_payload,
            "avr/autonomous/enable": self.process_autonomous_payload,
            "avr/pcm/set_base_color": self.led_flash,
        }

        self.thermal_grid = [[0 for _ in range(8)] for _ in range(8)]
        self.thermal_ideal_coords = None

        self.laza_state = None
        self.autonomous_state = None

        self.first_boot = True

        self.apriltag = None
        self.flashing = False

    ##### Utilities #####

    def led_flash(self, tupleCol) -> None:
        if self.flashing:
            return

        topic = "avr/pcm/set_base_color"
        payload = AvrPcmSetBaseColorPayload(wrgb=tupleCol)
        empty_payload = AvrPcmSetBaseColorPayload(wrgb=[255, 0, 0, 0])
        self.flashing = True

        for i in range(3):
            self.send_message(topic, payload)
            time.sleep(.15)
            self.send_message(topic, empty_payload)
            time.sleep(.1)  

        self.flashing = False

    def calc_highest_temp(self, grid):
        max_temp = 0
        max_coords = [0, 0]

        for i in range(len(grid)):
            for j in range(len(grid[i])):
                if grid[i][j] > max_temp:
                    max_temp = grid[i][j]
                    max_coords = (i, j)
        return max_coords, max_temp
    
    def set_laza(self, boolState) -> None:
        if boolState:
            topic = "avr/pcm/set_laser_on"
            payload = AvrPcmSetLaserOnPayload()
        else:
            topic = "avr/pcm/set_laser_off"
            payload = AvrPcmSetLaserOffPayload()
        self.laza_state = boolState
        self.send_message(topic, payload)

    def set_servo_abs(self, intServo, intAbs) -> None:
        self.send_message(
            "avr/pcm/set_servo_abs",
            AvrPcmSetServoAbsPayload(servo = intServo, absolute = intAbs)
        )
    def spam_logger(self, strAmount, strDebug) -> None:
        for i in range(strAmount):
            logger.debug(strDebug)
    
    ##### Payload Processing #####
    
    def process_autonomous_payload(self, payload: AvrAutonomousEnablePayload) -> None:
        self.autonomous_state = payload['enabled']

    def process_thermal_payload(self, payload: AvrThermalReadingPayload) -> None:
        raw_data = payload.get('data', '')
        decoded_bytes = base64.b64decode(raw_data.encode("utf-8"))
        pixel_values = list(bytearray(decoded_bytes))

        pixel_index = 0
        for row in range(len(self.thermal_grid)):
            for column in range(len(self.thermal_grid[0])):
                self.thermal_grid[column][row] = pixel_values[pixel_index]
                pixel_index += 1

        potential_ideal_temp = self.calc_highest_temp(self.thermal_grid)
        if potential_ideal_temp[1] <= 25:
            self.thermal_ideal_coords = None
            return
        self.thermal_ideal_coords = potential_ideal_temp[0]

    def process_apriltag_payload(self, payload: AvrApriltagsVisiblePayload):
        self.apriltag = payload['tags']

    ##### Detection #####

    def thermal_detection(self) -> None:
        if self.first_boot:
            time.sleep(30) # wait for pcm initialization
            self.set_servo_abs(2, 1450)
            self.set_servo_abs(3, 1450)
            logger.debug("Centering Gimbal")
            self.led_flash([255, 255, 0, 0])

        while True:
            if self.thermal_ideal_coords != None:
                self.led_flash([255, 255, 0, 255])
                self.spam_logger(5, "HOTSPOT DETECTED" )
                self.ThermalScan = True
                return 
            time.sleep(.1)

    def april_detection(self) -> None:
        while True:
            if self.apriltag != None:
                self.spam_logger(5, "DECEMBER TAG DETECTED! ( apriltag auton detection sequence )" )
                self.led_flash([255, 255, 0, 0])
                self.apriltag = None

            time.sleep(1)
if __name__ == "__main__":
    box = Sandbox() 

    thermal_reading = Thread(target=box.thermal_detection)
    thermal_reading.setDaemon(
        True
    )
    thermal_reading.start()

    april_reading = Thread(target=box.april_detection)
    april_reading.setDaemon(
        True
    )
    april_reading.start()

    box.run()
