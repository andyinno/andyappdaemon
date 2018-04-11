import appdaemon.plugins.hass.hassapi as hass

import datetime

class Room(hass.Hass):
    def initialize(self):
        self._name = self.args.get("name", None)
        self._motion_sensor = self.args.get("motion_sensor", None)
        self._illumination = self.args.get("illumination", None)
        self._max_ill = self.args.get("max_illumination", 999)
        self._light = self.args.get("light", None)
        self._flux = self.args.get("flux", None)

        self.listen_state(self.motion, entity=self._motion_sensor, new='on')
        self._timer = None

        self.log("Got name {}".format(self._name))
        self.log("Got motion_sensor {}".format(self._motion_sensor))
        self.log("Got light {}".format(self._light))
        self.log("Got flux {}".format(self._flux))
        self.log("Got illumination {}".format(self._illumination))
        self.log("Got limit {}".format(self._max_ill))
        self._timer = self.run_in(self.demotion, 300)
        
    def motion(self, entity, attribute, old, new, kwargs):
        self.log("{} detected motion".format(self._name))
        self.turn_on(self._light)
        if self._timer is not None:
            self.cancel_timer(self._timer)
        if self._illumination is not None:
            if self.get_state(self._illumination) > self._max_ill:
                self.log("Room {} is too bright.".format(self._name))
                return

        self._timer = self.run_in(self.demotion, 300)
        if self._flux is not None:
            self.call_service(self._flux)

    def demotion(self, kwargs):
        self.log("{}  timer ended".format(self._name))
        self.turn_off(self._light)
        if (self.get_state(self._light)=='on'):
            self._timer = self.run_in(self.demotion, 10)

class BedRoomNight(Room):
    def motion(self, entity, attribute, old, new, kwargs):
        self.log("{} detected motion by night".format(self._name))
        self.turn_on(self._light, color_name="red", brightness="30")
        if self._timer is not None:
            self.cancel_timer(self._timer)
        self._timer = self.run_in(self.demotion, 300)

