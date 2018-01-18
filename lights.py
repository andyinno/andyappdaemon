import appdaemon.appapi as appapi
import datetime
import math

'''
    The code related to the calculation of the brightness and the RGB color was
    taken from the source code of Home Assistant.
    The main file was here: 
    https://github.com/home-assistant/home-assistant/blob/master/homeassistant/components/switch/flux.py
'''

def _bound(color_component: float, minimum: float=0,
           maximum: float=255) -> float:
    """
    Bound the given color component value between the given min and max values.
    The minimum and maximum values will be included in the valid output.
    i.e. Given a color_component of 0 and a minimum of 10, the returned value
    will be 10.
    """
    color_component_out = max(color_component, minimum)
    return min(color_component_out, maximum)


def _get_red(temperature: float) -> float:
    """Get the red component of the temperature in RGB space."""
    if temperature <= 66:
        return 255
    tmp_red = 329.698727446 * math.pow(temperature - 60, -0.1332047592)
    return _bound(tmp_red)


def _get_green(temperature: float) -> float:
    """Get the green component of the given color temp in RGB space."""
    if temperature <= 66:
        green = 99.4708025861 * math.log(temperature) - 150#161.1195681661
    else:
        green = 288.1221695283 * math.pow(temperature - 60, -0.0755148492)
    return _bound(green)


def _get_blue(temperature: float) -> float:
    """Get the blue component of the given color temperature in RGB space."""
    if temperature >= 105: #66:
        return 255
    if temperature <= 19:
        return 0
    blue = 138.5177312231 * math.log(temperature - 10) - 305.0447927307
    return _bound(blue)

def color_temperature_to_rgb(color_temperature_kelvin):
    """
    Return an RGB color from a color temperature in Kelvin.
    This is a rough approximation based on the formula provided by T. Helland
    http://www.tannerhelland.com/4435/convert-temperature-rgb-algorithm-code/
    """
    # range check
    if color_temperature_kelvin < 1000:
        color_temperature_kelvin = 1000
    elif color_temperature_kelvin > 40000:
        color_temperature_kelvin = 40000

    tmp_internal = color_temperature_kelvin / 100.0

    red = _get_red(tmp_internal)

    green = _get_green(tmp_internal)

    blue = _get_blue(tmp_internal)

    return (red, green, blue)


def color_RGB_to_xy(iR: int, iG: int, iB: int):
    """Convert from RGB color to XY color."""
    if iR + iG + iB == 0:
        return 0.0, 0.0, 0

    R = iR / 255
    B = iB / 255
    G = iG / 255

    # Gamma correction
    R = pow((R + 0.055) / (1.0 + 0.055),
            2.4) if (R > 0.04045) else (R / 12.92)
    G = pow((G + 0.055) / (1.0 + 0.055),
            2.4) if (G > 0.04045) else (G / 12.92)
    B = pow((B + 0.055) / (1.0 + 0.055),
            2.4) if (B > 0.04045) else (B / 12.92)

    # Wide RGB D65 conversion formula
    X = R * 0.664511 + G * 0.154324 + B * 0.162028
    Y = R * 0.313881 + G * 0.668433 + B * 0.047685
    Z = R * 0.000088 + G * 0.072310 + B * 0.986039

    # Convert XYZ to xy
    x = X / (X + Y + Z)
    y = Y / (X + Y + Z)

#    Y *= 1.15
    # Brightness
    Y = 1 if Y > 1 else Y
    brightness = round(Y * 255)

    return round(x, 3), round(y, 3), brightness


class MotionLights(appapi.AppDaemon):
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
        self.log("Got luminosity for "+entity+" "+new)
        self._luma_val[int(kwargs["index"])] = float(new)

    def reset_status(self, kwargs):
        self.log("Resetting the disabler")
        self.turn_off(self._disabler)


class NightLight(MotionLights):
    def initialize(self):
        print("NightLight initialize")
        super(NightLight, self).initialize()
        self._brightlight_start = datetime.datetime.strptime(self.args.get("brightlight_start", "0:0:0"), "%H:%M:%S").time()
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

        if self._brightlight_end  > now  and now > self._brightlight_start:
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
    def initialize(self):
        print("FluxLight initialize")
        super(FluxLight, self).initialize()
        self._start_time = datetime.datetime.strptime(self.args.get("start_time", "0:0:0"), "%H:%M:%S")
        self._stop_time = datetime.datetime.strptime(self.args.get("stop_time", "0:0:0"), "%H:%M:%S")

        self._start_colortemp = self.args.get("start_colortemp", 0)
        self._sunset_colortemp = self.args.get("sunset_colortemp", 0)
        self._stop_colortemp = self.args.get("stop_colortemp", 0)

        self.log("Got starting time {}".format(self._start_time))
        self.log("Got stop time {}".format(self._stop_time))
        self.log("Got start color {}".format(self._start_colortemp))
        self.log("Got stop color {}".format(self._stop_colortemp))
        self.log("Got sunset color {}".format(self._sunset_colortemp))

#        self.turn_on_lights()

    def turn_on_lights(self):
        self.log("FluxLight turn on lights")

        now = self.datetime()
        start_time = now.replace(hour=self._start_time.hour, minute=self._start_time.minute, second=self._start_time.second)
        stop_time = now.replace(hour=self._stop_time.hour, minute=self._stop_time.minute, second=self._stop_time.second)
        sunset = self.sunset()

        if stop_time <= start_time:
            self.log("stop_time does not happen in the same day as start_time")
            if start_time < now:
                self.log("stop time is tomorrow")
                stop_time += datetime.timedelta(days=1)

        elif now < start_time:
            self.log("stop_time was yesterday since the new start_time is not reached")
            stop_time -= datetime.timedelta(days=1)

        for light in self._lights:

            if self._start_time < now < sunset:
                self.log("Daytime, sunset at {}".format(sunset))
                day_length = int(sunset.timestamp() - start_time.timestamp())
                seconds_from_start = int(now.timestamp() - start_time.timestamp())
                percentage_complete = seconds_from_start / day_length
                temp_range = abs(self._start_colortemp - self._sunset_colortemp)
                temp_offset = temp_range * percentage_complete
                if self._start_colortemp > self._sunset_colortemp:
                    temp = self._start_colortemp - temp_offset
                else:
                    temp = self._start_colortemp + temp_offset

            else:
                self.log("Nighttime, sunset at {}".format(sunset))
                if now < stop_time:
                    if stop_time < start_time and stop_time.day == sunset.day:
                        sunset_time = sunset - datetime.timedelta(days=1)
                    else:
                        sunset_time = sunset

                    night_length = int(stop_time.timestamp() -
                                       sunset_time.timestamp())
                    seconds_from_sunset = int(now.timestamp() -
                                              sunset_time.timestamp())
                    percentage_complete = seconds_from_sunset / night_length
                else:
                    percentage_complete = 1

                temp_range = abs(self._sunset_colortemp - self._stop_colortemp)
                temp_offset = temp_range * percentage_complete
                if self._sunset_colortemp > self._stop_colortemp:
                    temp = self._sunset_colortemp - temp_offset
                else:
                    temp = self._sunset_colortemp + temp_offset

            rgb = color_temperature_to_rgb(temp)
            x_val, y_val, b_val = color_RGB_to_xy(*rgb)

            brightness = b_val


            self.log("Turning on light with rgb: {} and brightness {}".format(rgb, brightness))
            transition = 30
            if self.get_state(light) == "off":
                transition = 1
            self.turn_on(light, rgb_color=rgb, brightness=brightness, transition=transition)
#            self.turn_on(light, xy_color=[x_val,y_val], brightness=brightness, transition=transition)
            if self._timeout is not None:
                self.cancel_timer(self._timeout)
