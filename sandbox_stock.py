# Team Atlas 78867A AVR 23'
import time
from threading import Thread
from loguru import logger

from bell.avr.mqtt.client import (
    MQTTModule,
)
from bell.avr.mqtt.payloads import (
    AvrApriltagsVisiblePayload,
    # AvrAutonomousBuildingDropPayload,
    AvrPcmSetServoOpenClosePayload,
)

class Sandbox(MQTTModule):
    def __init__(self) -> None:
        super().__init__()
        self.topic_map = {
            "avr/apriltags/visible" : self.AprilDetect,
            "avr/pcm/set_servo_open_close": self.drop_flash,
        }
        self.color_white = [255, 255, 255, 255],
        self.color_green = [0, 0, 255, 0]
        self.color_red = [0, 255, 0, 0]
        self.color_yellow = [0, 252, 186, 3]
        self.prefix = "[Atlas-AVR] "

        self.curAprilTag = None
        self.curColor = None

        ### SOMETIMES IT GETS INVERTED ###
        self.OpenOrientation = "close"
        # self.OpenOrientation = "open"

    def AprilDetect(self, payload: AvrApriltagsVisiblePayload) -> None:
        tag_list = payload["tags"]
        tag_id = tag_list[0]["id"] # gets the id of current tag
        self.curAprilTag = tag_id

    def drop_flash(self, payload = AvrPcmSetServoOpenClosePayload) -> None:
        servo_id = payload["servo"]
        action = payload["action"]

        if servo_id == 1 and action == self.OpenOrientation:
            logger.debug("Extinguishing Fire!!!")
            self.curColor = 'Blue'

    def autoLightStatus(self) -> None:
        logger.debug(self.prefix+"AutoLightStatus - Initialized")
        while True:
            if self.curColor == "Blue":
                for i in range(3): #FLASHING DROPPING
                    self.send_message(
                        "avr/pcm/set_base_color",
                        {"wrgb": [255, 0, 0, 255]},
                    )
                    time.sleep(.15)
                    self.send_message(
                        "avr/pcm/set_base_color",
                        {"wrgb": [0, 0, 0, 0]},
                    )
                    time.sleep(.10)
                self.curColor = "N"
            if self.curAprilTag == None:
                # logger.debug("no cur apriltag :(")
                if not self.curColor == "N":
                    self.send_message(
                        "avr/pcm/set_base_color",
                        {"wrgb": [0, 0, 0, 0],}
                    )
                    self.curColor = "N"
            else:
                if not self.curColor == "Green":
                    logger.debug("April Detected ["+str(self.curAprilTag)+"]")
                    for i in range(3): #FLASHING READY TO DROP
                        self.send_message(
                            "avr/pcm/set_base_color",
                            {"wrgb": [0, 0, 255, 1],}
                        )
                        time.sleep(.85)
                        self.send_message(
                            "avr/pcm/set_base_color",
                            {"wrgb": [0, 0, 0, 0],}
                        )
                        time.sleep(.15)
                    self.send_message(
                        "avr/pcm/set_base_color",
                        {"wrgb": [0, 0, 255, 1],}
                    )
                    self.curColor = "Green"
            time.sleep(.5)

    def LazyTick(self) -> None:
        logger.debug(self.prefix+"LazyTick - Initialized")
        while True:
            if not self.curAprilTag == None:
                time.sleep(3.5)
            self.curAprilTag = None
            time.sleep(1) # Thread Delay

if __name__ == "__main__":
    # Initialize Sandbox class
    box = Sandbox()
    ########### Lazy Ticks ###########
    LTick = Thread(target=box.LazyTick)
    LTick.setDaemon(
        True
    )
    LTick.start()

    ########### AUTO STATUS ###########
    lightstatus = Thread(target=box.autoLightStatus)
    lightstatus.setDaemon(
        True
    )
    lightstatus.start()
    box.run()
