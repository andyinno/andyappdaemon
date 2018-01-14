import appdaemon.appapi as appapi
import datetime

class MotionLights(appapi.AppDaemon):
    def initialize(self):
        print("qui")
        self._lights = self.args.get("lights", [])
        self._motion = self.args.get("motion", None)
        self._luminosity = self.args.get("luminosity", [])
        self._disabler = self.args.get("disabler", None)
        self._timeout = None
        self._luma_val = []
        self._luminosity_min = self.args.get("luminosity_min", 20)
        self.log("Got controlled lights {}".format(self._lights))
        self.log("Got controller motion sensor {}".format(self._motion))
        self.log("Got luminosity sensor {}".format(self._luminosity))
        self.log("Got disabler sensor {}".format(self._disabler))
        self.listen_state(self.motion, entity=self._motion, new="on")
        self.listen_state(self.demotion, entity=self._motion, new="off")
        i = 0
        for item in self._luminosity:
            self.listen_state(self.luminosity, item, index=i)
            i += 1
            self._luma_val.append(0)
        time = datetime.time(6, 0, 0)
        self.run_daily(self.reset_status, time)

    def motion(self, entity, attribute, old, new, kwargs):
        self.log("Motion detected")
        luma = 0
        for val in self._luma_val:
            if int(val) > int(luma):
                luma = val

        if self.get_state(self._disabler) == 'on':
            self.log("Controlling lights is disabled")
            return

        if luma > self._luminosity_min:
            self.log("room is too bright for lights. luma %d" % (luma))
            return

        self.log("luma %d is ok for controlling lights." % (luma))
        for light in self._lights:
            self.turn_on(light)
        if self._timeout is not None:
            self.cancel_timer(self._timeout)

    def demotion(self, entity, attribute, old, new, kwargs):
        if self.get_state(self._disabler) == 'on':
            self.log("Controlling lights is disabled")
            return
        self.log("Motion switched off, starting timer")
        self._timeout = self.run_in(self.light_off, 300)

    def light_off(self, kwargs):
        if self.get_state(self._disabler) == 'on':
            self.log("Controlling lights is disabled")
            return
        self.log("Timer ended.")
        self.cancel_timer(self._timeout)
        self._timeout = None
        for light in self._lights:
            self.turn_off(light)

    def luminosity(self, entity, attribute, old, new, kwargs):
        self.log("Got luminosity for "+entity+" "+new)
        self._luma_val[int(kwargs["index"])] = float(new)

    def reset_status(self, **kwargs):
        self.log("Resetting the disabler")
        self.turn_off(self._disabler)
