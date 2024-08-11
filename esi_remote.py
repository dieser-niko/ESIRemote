import time

import requests
from typing import List, Union
import models
from filter_list import FilterList


class ESIRemote:
    def __init__(self, host="http://127.0.0.1", port=2132, session: requests.Session = None, autocommit=True):
        self.host = host
        self.port = port
        self.session = session if session else requests.Session()
        self.autocommit = autocommit
        self._save_files: Union[List[models.Save], FilterList] = FilterList()
        self._active: Union[models.Active, None] = None
        self._operatoractors: Union[List[models.OperatorActor], FilterList] = FilterList()
        self.update_saves()
        self.update_active()
        self.update_operatoractors()

    def _api_get(self, path_name):
        return self.session.get(f"{self.host}:{self.port}/api/{path_name}").json()

    def _api_put(self, path_name, data):
        return self.session.put(f"{self.host}:{self.port}/api/{path_name}", json=data).json()

    def _commit_save(self, force: bool = False):
        """
        Goes through each save and checks if it has an update.
        If yes, it will put the data to the server and stops iterating.
        """
        if not (force or self.autocommit):
            return
        committed = False
        for save in self.save_files:
            if save.commit_changes and not committed:
                response = self._api_put("save-files", save.commit_changes)
                if not response == {"answer": "save file has been loaded"}:
                    raise ValueError(f"Answer from server not as expected: {repr(response)}")
                self.update_active()
                self.update_saves()
                committed = True
            save.commit_changes = {}

    def update_saves(self):
        self._save_files = models.get_updated_values(self._save_files,
                                                     self._api_get("save-files"),
                                                     models.Save.parse,
                                                     "absolutePath")
        for save in self._save_files:
            save.commit_callback = self._commit_save

    @property
    def save_files(self) -> List[models.Save]:
        return FilterList(self._save_files)

    def update_active(self):
        if self._active:
            self._active.update_values(self._api_get("save-files/active"))
        else:
            self._active = models.Active.parse(self._api_get("save-files/active"))

    @property
    def active(self) -> models.Active:
        return self._active

    def _commit_actor(self, force: bool = False):
        if not (force or self.autocommit):
            return

        for actor in self.operatoractors:
            if actor.commit_changes:
                response = self._api_put("operatoractors", actor.commit_changes)
                if not response == {"answer": "actor has been updated"}:
                    raise ValueError(f"Answer from server not as expected: {repr(response)}")
                actor.commit_changes = dict()

        self.update_operatoractors()

    def update_operatoractors(self):
        self._operatoractors = models.get_updated_values(self._operatoractors,
                                                         self._api_get("operatoractors")["operatorActors"],
                                                         models.OperatorActor.parse,
                                                         "id")
        for actor in self.operatoractors:
            actor.commit_callback = self._commit_actor

    @property
    def operatoractors(self) -> Union[List[models.OperatorActor], FilterList]:
        return self._operatoractors

    def commit(self):
        """
        Uploads/commits changes and updates the objects for OperatorActors.
        """
        self._commit_actor()
        self.update_operatoractors()


def value_timer(start, end, seconds):
    timer = time.time()
    while time.time() - timer < seconds:
        yield ((end - start) * ((time.time() - timer) / seconds)) + start
    yield end


if __name__ == "__main__":
    remote = ESIRemote()
    remote.save_files[9].sub_saves[0].load()
    print(remote.active)
    fahrzeug = remote.operatoractors.by_attribute(type="emergency_vehicle").first()
    remote.operatoractors[0].is_visible = False
    enum = remote.operatoractors[0].property_enums[0].all_values.by_attribute(enum_field_value="CLOSED").first()
    remote.operatoractors[0].property_enums[0].current_value = enum
    fahrzeug.properties.by_attribute(name="DP_ExtendSupports").value = False
    fahrzeug.properties[1].value = 0
    fahrzeug.properties[2].value = 0
    fahrzeug.properties[3].value = 0
    time.sleep(3)
    fahrzeug.properties[0].value = True
    time.sleep(2)
    for value in value_timer(0, 20.5, 5):
        fahrzeug.properties[2].value = value
    time.sleep(2)
    for value in value_timer(0, 101.25, 5):
        fahrzeug.properties[1].value = value
    time.sleep(2)
    for value in value_timer(0, 0.55, 5):
        fahrzeug.properties[3].value = value
    for value in value_timer(0.55, 0.6, 2):
        fahrzeug.properties[3].value = value
    time.sleep(2)
    enums = remote.operatoractors[0].property_enums[0].all_values
    for enum in enums:
        if enum.enum_field_value == "OPEN":
            break
    remote.operatoractors[0].property_enums[0].current_value = enum
    remote.operatoractors[1].is_visible = True
