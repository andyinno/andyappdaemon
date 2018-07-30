import appdaemon.plugins.hass.hassapi as hass

class DoorWindowSensor(hass.Hass):
    def initialize(self):
        self._sensor_group = self.args.get("checked_sensor", None)
        self._trigger = self.args.get("trigger")
        self._notifier = self.args.get("notifier")
        self._alarm = self.args.get("alarm")
        
        self.listen_state(self.trigger_active, entity=self._trigger, old="off", new="on")
        self.listen_state(self._alarm, entity=self._alarm, old="disarmed", new="pending")

    def verify_status(self, entity, attribute, old, new, kwargs):
        self.log("Time to go verify the status.")
        alarm = False
        if self.get_state(self._alarm) == "pending":
            self.log("uno c'e'")
            alarm = True
        if self.get_state(self._trigger)=="on":
            self.log("due c'e'")
            trigger = True

        entities = []
        if alarm and trigger:
            if self.get_state(self._sensor_group) == "on":
                groupitem = self.get_state(self.args["group_of_trigger_sensors"],"all")
                entity_list = groupitem['attributes']['entity_id']
                for i in entity_list:
                    if self.get_state(i) == "on":
                        entities.append(i['attribute']['friendly_name'])

            self.notify("Ci sono dei sensori attivi {}".format(entities), name=self._notifier)

    def pending_alarm(self, entity, attribute, old, new, kwargs):
        self.log("pending alarm detected.")
        self.verify_status(entity, attribute, old, new, kwargs)

    def trigger_active(self, entity, attribute, old, new, kwargs):
        self.log("the trigger is active.")
        self.verify_status(entity, attribute, old, new, kwargs)