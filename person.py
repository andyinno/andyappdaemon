import appdaemon.plugins.hass.hassapi as hass

class Person(hass.Hass):
    def initialize(self):
        self.log("Person initialize")

        self._name = self.args.get("name", None)
        self._tracker = self.args.get("person_tracker", None)
        self._family_tracker = self.args.get("family_tracker", None)
        self._notifier = self.args.get("notifier", None)
        self._door_sensor = self.args.get("door_sensor", None)
        self._peripheral_sensors = self.args.get("peripheral_sensors", None)
        self._pending_notification = False

        self.log("Got name {}".format(self._name))
        self.log("Got trackers {}".format(self._tracker))
        self.log("Got trackers {}".format(self._family_tracker))
        self.log("Got notifier {}".format(self._notifier))
        self.log("Door sensor {}".format(self._door_sensor))
        self.log("Peripheral sensors {}".format(self._peripheral_sensors))

        self.listen_state(self.family_changed_away, entity=self._family_tracker, old="home", new="not_home")
        self.listen_state(self.family_changed_home, entity=self._family_tracker, old="home", new="home")
        self.listen_state(self.person_changed_away, entity=self._tracker, old="not_home", new="not_home")
        self.listen_state(self.person_changed_home, entity=self._tracker, old="not_home", new="home")
        self.listen_state(self.door_opened, entity=self._door_sensor, new="off")

    def family_changed_away(self, entity, attribute, old, new, kwargs):
        self.log("Family state changed to away")

    def family_changed_home(self, entity, attribute, old, new, kwargs):
        self.log("Family state changed to home")

    def person_changed_home(self, entity, attribute, old, new, kwargs):
        self.log("{} state changed to home".format(self._name))


    def person_changed_away(self, entity, attribute, old, new, kwargs):
        self.log("{} state changed to away".format(self._name))
        if (self.get_state(self._family_tracker) == "not_home"):
            self.notify("Molto probabilmente delle finestre sono rimaste aperte.", title="Avviso finestre",
                        name=self._notifier)
        self._pending_notification = False

    def door_opened(self, entity, attribute, old, new, kwargs):
        self.log("{} opened".format(self._door_sensor))
        if (self.get_state(self._tracker) == "home"):
            self._pending_notification = True

