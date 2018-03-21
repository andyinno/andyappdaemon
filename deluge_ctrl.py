import appdaemon.plugins.hass.hassapi as hass

class DelugeCtrl(hass.Hass):
    def initialize(self):
        print("DelugeCtrl initialize")
        self._people = self.args.get("people", [])

        for person in self._people:
            self.listen_state(self.check_away, person, old="home")
            self.listen_state(self.check_home, person, old="away")

    def check_away(self, **kwargs):
        away = True
        for person in self._people:
            if self.get_state(entity_id=person ) == "home":
                away = False
                break

        if away:
            self.set_state("binary_switch", "on")

    def check_home(self, **kwargs):
        home = True
        for person in self._people:
            if self.get_state(entity_id=person) == "away":
                home = False
                break
        if home:
            self.set_state("binary_switch", "off")