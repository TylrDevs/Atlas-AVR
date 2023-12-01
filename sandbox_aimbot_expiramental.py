from bell.avr.mqtt.client import MQTTModule
from bell.avr.mqtt.payloads import (AvrFcmLocationLocalPayload,
                                    AvrAutonomousBuildingDropPayload,
                                    AvrPcmSetServoAbsPayload,
                                    AvrFcmAttitudeEulerPayload,
                                    AvrAutonomousEnablePayload)
from loguru import logger
from threading import Thread
import time
import math

class Sandbox(MQTTModule):

    def __init__(self) -> None:

        super().__init__()

        self.topic_map = {"avr/fcm/location/local": self.get_pos,
                          "avr/autonomous/building/drop": self.building_set,
                          "avr/pcm/set_servo_abs": self.update_servo,
                          "avr/autonomous/enable": self.set_home,
                          "avr/fcm/attitude/euler": self.get_att
                          }

        self.building_map = {0 : False, 1 : False, 2 : False,
                             3 : False, 4 : False, 5 : False}

        self.buildings_ready = set()

        self.setPos = False

        self.servoPos = {0 : 0, 1 : 0, 2 : 0, 3 : 0,
                         4 : 0, 5 : 0, 6 : 0, 7 : 0}

        self.setupPhase = {0 : 0, 4 : 0, 5 : 0}
        self.target_pos = {0 : [], 4 : [], 5 : []}

        self.yPossibles = []

        self.zPossibles = []

        self.curPos = []

        self.yList1 = []
        self.yList2 = []
        self.zList1 = []
        self.zList2 = []

        self.attitudes = []

        self.target_pos_map = {}

        self.target_pos_map[0] = {'x': 0, 'y': 0, 'z': 0, 'pitch': 0, 'yaw': 0, 'pan': 0, 'tilt': 0}
        self.target_pos_map[4] = {'x': 0, 'y': 0, 'z': 0, 'pitch': 0, 'yaw': 0, 'pan': 0, 'tilt': 0}
        self.target_pos_map[5] = {'x': 0, 'y': 0, 'z': 0, 'pitch': 0, 'yaw': 0, 'pan': 0, 'tilt': 0}

    def set_home(self, payload: AvrAutonomousEnablePayload) -> None:
        self.send_message("avr/fcm/action/capture_home", {})
        logger.debug("Home position set")

    def get_att(self, payload: AvrFcmAttitudeEulerPayload) -> None: # constantly updates attitudes
        roll = payload["roll"]
        pitch = payload["pitch"]
        yaw = payload["yaw"]
        self.attitudes = [roll, pitch, yaw]

    def update_servo(self, payload: AvrPcmSetServoAbsPayload) -> None: # constantly updates servo abs position
        servo = payload["servo"]
        val = payload["absolute"]
        self.servoPos[servo] = val

    def get_pos(self, payload: AvrFcmLocationLocalPayload) -> None: # constantly updates position
        dX = payload["dX"]
        dY = payload["dY"]
        dZ = payload["dZ"]
        self.curPos = [dX, dY, dZ]
        #print(self.curPos)

#24.8 CM OFFSET
    def building_set(self, payload: AvrAutonomousBuildingDropPayload) -> None: # updates building map and sets up the targets for aimbot loop
        id = payload["id"]
        enabled = payload["enabled"]

        self.building_map[id] = enabled

        if ( id == 0 or id == 4 or id == 5 ) and enabled == True:            
            x = self.curPos[0] + 2
            y = self.curPos[1]
            z = self.curPos[2]
            pitch = self.attitudes[1]
            yaw = self.attitudes[2]
            pan = self.servoPos[2]
            tilt = self.servoPos[3]
            self.target_pos_map[id] = {'x': x, 'y': y, 'z': z, 'pitch': pitch,
                                       'yaw': yaw, 'pan': pan, 'tilt': tilt}
            logger.debug(f"Target {id} map: {self.target_pos_map[id]}")
            self.setupPhase[id] = 1

                

    def aim_loop(self) -> None: # loop that aims servos at curent target
        while True:
            for target in self.target_pos:
                if self.setupPhase[target] == 1 and self.building_map[target] == True:

                    xT = self.target_pos_map[target]["x"]
                    yT = self.target_pos_map[target]["y"]
                    zT = self.target_pos_map[target]["z"]
                    pitchT = self.target_pos_map[target]["pitch"]
                    yawT = self.target_pos_map[target]["yaw"]

                    xP = self.curPos[0]
                    yP = self.curPos[1]
                    zP = self.curPos[2]
                    pitchP = self.attitudes[1]
                    yawP = self.attitudes[2]

                    logger.debug(f"xP: {xP}, yP: {yP}, zP: {zP}, pitchP: {pitchP}, yawP: {yawP}")
                    logger.debug(f"xT: {xT}, yT: {yT}, zT: {zT}, pitchT: {pitchT}, yawT: {yawT}")

                    rot = self.get_rotation(xP, yP, zP, xT, yT, zT)
                    logger.debug(f"rotY: {rot[0], type(rot[0])}")
                    logger.debug(f"rotZ: {rot[1], type(rot[1])}")
                    logger.debug(rot)
                    rotY = rot[0]# - (yawT - yawP)
                    rotZ = rot[1]# - (pitchT - pitchP)
                    logger.debug(f"Servo Degree Rotation: Y: {rotY}, Z: {rotZ}")
                    rotY = self.deg_to_abs(rotY)
                    rotZ = self.deg_to_abs(rotZ)
                    if (rotY < 2220 and rotY > 780) and (rotZ < 2220 and rotZ > 780):
                        self.send_message(
                            "avr/pcm/set_servo_abs",
                            {"servo": 2, "absolute": rotY},
                        )
                        self.send_message(
                            "avr/pcm/set_servo_abs",
                            {"servo": 3, "absolute": rotZ},
                        )
                    logger.debug(f"Servo Abs Rotation: Y: {rotY}, Z: {rotZ}")
                    self.send_message("avr/pcm/set_laser_on", {})
                    time.sleep(0.25)

    def deg_to_abs(self, d): # helper function to convert degrees to absolute servo msgs
        return round(10 * d + 1500)

    def abs_to_deg(self, a): # helper functino to convert absolute servo msgs to degrees
        return 0.1(a - 1500)

    def get_rotation(self, x1, y1, z1, x2, y2, z2): # helper function to get the angle rotation that a 3-coordinate position
        rY = rZ = 0                                 # must turn in the y and z dimensions to aim at another 3-coord position

        if x2 - x1 == 0:
            return [0, 0]

        tan1 = (y2 - y1)/(x2 - x1)

        rY = math.degrees(math.atan(tan1))

        tan2 = (z2 - z1)/(x2 - x1)

        rZ = math.degrees(math.atan(tan2))
        logger.debug(f"rY: {rY, type(rY)}")
        logger.debug(f"rY: {rZ, type(rZ)}")

        return [rY, rZ]

    def gen_pos(self, r, offset, att, curX):
        r += att
        x = curX
        curlist = []
        while x <= 10:
            pos = x * math.atan(math.tan((r * math.pi) / 180))
            pos += offset
            curlist.append([pos, x])
            x += 0.001
        return curlist

    def find_closest_pair(self, a1, a2): # two-pointer algorithm that finds the closest pairs from two arrays
        i, j = 0, 0                      # used to find the target in the setup phases
        min_difference = float('inf')
        closest_pair = None

        while i < len(a1) and j < len(a2):
            difference = abs(a1[i][0] - a2[j][0])

            if difference < min_difference:
                min_difference = difference
                closest_pair = [a1[i], a2[j]]

            if a1[i][0] < a2[j][0]:
                i += 1
            else:
                j += 1

        return closest_pair

if __name__ == "__main__":

    box = Sandbox()

    aim_thread = Thread(target=box.aim_loop)
    aim_thread.setDaemon(True)
    aim_thread.start()

    pos_thread = Thread(target=box.get_pos)
    pos_thread.setDaemon(True)
    pos_thread.start()

    box.run()
