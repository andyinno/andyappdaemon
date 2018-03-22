import appdaemon.plugins.hass.hassapi as hass


class LastMotion(hass.Hass):
    def initialize(self):
        self.log("LastMotion.initialize")
        self._kitchen = self.args.get("kitchen", None)
        self._livingroom = self.args.get("livingroom", None)
        self._playroom = self.args.get("playroom", None)
        self._bedroom = self.args.get("bedroom", None)

        self.listen_state(self.motion_kitchen, entity=self._kitchen, new="off")
        self.listen_state(self.motion_livingroom, entity=self._livingroom, new="off")
        self.listen_state(self.motion_playroom, entity=self._playroom, new="off")
        self.listen_state(self.motion_bedroom, entity=self._bedroom, new="off")
        self.log("Ok with states")

    def motion_kitchen(self, entity, attribute, old, new, kwargs):
        self.log("Motion kitchen")
        self.select_option("input_select.last_motion", "Kitchen")

    def motion_livingroom(self, entity, attribute, old, new, kwargs):
        self.log("Motion livingroom")
        self.select_option("input_select.last_motion", "LivingRoom")

    def motion_playroom(self, entity, attribute, old, new, kwargs):
        self.log("Motion playroom")
        self.select_option("input_select.last_motion", "Playroom")

    def motion_bedroom(self, entity, attribute, old, new, kwargs):
        self.log("Motion bedroom")
        self.select_option("input_select.last_motion", "Bedroom")
