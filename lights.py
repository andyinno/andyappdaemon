import appdaemon.appapi as appapi
import datetime
import math


class MotionLights(appapi.AppDaemon):
    """
    This class keeps track of different lights managed by a motion sensor.
    the luminosity in the room must be lower of the luminosity_min value passed in the
    configuration that is reported by the luminosity sensor list.
    A disabler binary sensor can be used for disabling the usage of the module.
    For example if kodi starts playing I don't want that some movement in the room turns on the lights.
    """
    def initialize(self):
        print("MotionLights initialize")
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

            # if lights was already on... don't let the timer expire but reload it instead.
            if self._timeout is not None:
                self.cancel_timer(self._timeout)
                self._timeout = self.run_in(self.light_off, 300)
            return

        self.log("luma %d is ok for controlling lights." % (luma))
        self.turn_on_lights()

    def turn_on_lights(self):
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
        self.log("Got luminosity for " + entity + " " + new)
        self._luma_val[int(kwargs["index"])] = float(new)

    def reset_status(self, kwargs):
        self.log("Resetting the disabler")
        self.turn_off(self._disabler)


class NightLight(MotionLights):
    def initialize(self):
        print("NightLight initialize")
        super(NightLight, self).initialize()
        self._brightlight_start = datetime.datetime.strptime(self.args.get("brightlight_start", "0:0:0"),
                                                             "%H:%M:%S").time()
        self._brightlight_end = datetime.datetime.strptime(self.args.get("brightlight_end", "0:0:0"), "%H:%M:%S").time()
        self._bright_value = self.args.get("bright_value", 0)
        self._lowbright_value = self.args.get("lowbright_value", 0)
        self._rgbcolor_value = self.args.get("rgbcolor_value", 0)
        self._lowrgbcolor_value = self.args.get("lowrgbcolor_value", 0)

        self.log("Got starting time {}".format(self._brightlight_start))
        self.log("Got ending time {}".format(self._brightlight_end))
        self.log("Got bright_value  {}".format(self._bright_value))
        self.log("Got lowbright_value {}".format(self._lowbright_value))
        self.log("Got rgbcolor_value {}".format(self._rgbcolor_value))
        self.log("Got lowrgbcolor_value {}".format(self._lowrgbcolor_value))

    def turn_on_lights(self):
        self.log("turn on lights")
        now = self.time()

        if self._brightlight_end > now and now > self._brightlight_start:
            brightness = self._bright_value
            color = self._rgbcolor_value
        else:
            brightness = self._lowbright_value
            color = self._lowrgbcolor_value

        for light in self._lights:
            self.log("turning on light {} with {} {}".format(light, brightness, color))
            self.turn_on(light, color_name=color, brightness=brightness)
        if self._timeout is not None:
            self.cancel_timer(self._timeout)


class FluxLight(MotionLights):
    """ Flux and Motion lights

    This class uses the MotionLights base class including also the fluxer service
    defined in home assistant. The fluxer service call after the turn_on_lights is used
    for updating the color of the lights.
    """
    def initialize(self):
        print("FluxLight initialize")
        super(FluxLight, self).initialize()
        self._fluxer_service = self.args.get("fluxer", None)

        self.log("Got fluxer {}".format(self._fluxer_service))

    def turn_on_lights(self):
        self.log("FluxLight turn on lights")
        super(FluxLight, self).turn_on_lights()
        if (self._fluxer_service is not None):
            self.call_service(self._fluxer_service)
