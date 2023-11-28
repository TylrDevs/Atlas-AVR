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
        self.topic_map = {
            "avr/thermal/reading": self.process_thermal_payload,
            "avr/autonomous/enable": self.process_autonomous_payload
        }
        self.thermal_grid = [[0 for _ in range(8)] for _ in range(8)]
        self.thermal_ideal_coords = None

        self.laza_state = None
        self.autonomous_state = None

        self.first_boot = True

    def process_autonomous_payload(self, payload: AvrAutonomousEnablePayload) -> None:
        self.autonomous_state = payload['enabled']

    def calc_highest_temp(self, grid):
        max_temp = 0
        max_coords = [0, 0]

        for i in range(len(grid)):
            for j in range(len(grid[i])):
                if grid[i][j] > max_temp:
                    max_temp = grid[i][j]
                    max_coords = (i, j)
        return max_coords, max_temp

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
        logger.debug(self.thermal_ideal_coords)
    
    def set_servo_abs(self, intServo, intAbs) -> None:
        self.send_message(
            "avr/pcm/set_servo_abs",
            AvrPcmSetServoAbsPayload(servo = intServo, absolute = intAbs)
        )

    def set_laza(self, boolState) -> None:
        if boolState:
            topic = "avr/pcm/set_laser_on"
            payload = AvrPcmSetLaserOnPayload()
        else:
            topic = "avr/pcm/set_laser_off"
            payload = AvrPcmSetLaserOffPayload()
        self.laza_state = boolState
        self.send_message(topic, payload)

    def thermal_lock(self) -> None:
        while True:
            if self.first_boot:
                time.sleep(10) # wait for pcm initialization
                self.set_servo_abs(2, 1450)
                self.set_servo_abs(3, 1450)
                logger.debug("Centering Gimbal")
                self.first_boot = False

            if self.autonomous_state == True:
                if not self.thermal_ideal_coords == None:
                    if self.laza_state == False or self.laza_state == None:
                        self.set_laza(True)
                        logger.debug("Laza Laza @ " + str(self.thermal_ideal_coords))
                        # Servo 3: Pitch
                        # Servo 2: Yaw

                        Ideal_Column = (self.thermal_ideal_coords[0]*10)
                        Ideal_Row = (self.thermal_ideal_coords[1]*10) 
                        # Max of the abs is roughly ~2950
                        # Half is 1450 and 0 is yeah 0

                        
                else:
                    if self.laza_state == True:
                        self.set_laza(False)
                        logger.debug("Laza eepy")
            time.sleep(1)

if __name__ == "__main__":
    box = Sandbox() 

    thermallock = Thread(target=box.thermal_lock)
    thermallock.setDaemon(
        True
    )
    thermallock.start()

    box.run()
