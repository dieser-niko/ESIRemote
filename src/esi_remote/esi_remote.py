import time

import requests
from typing import List, Union
from .models import Save, Active, OperatorActor, get_updated_values
from .filter_list import FilterList


class ESIRemote:
    def __init__(self, host="http://127.0.0.1", port=2132, session: requests.Session = None, autocommit=True):
        """
        Creates an ESIRemote API client.

        :param host: Host to the FwESI Remote server (default=http://127.0.0.1)
        :param port: Port to the FwESI Remote server (default=2132)
        :param session: Custom requests.Session for API requests (optional)
        :param autocommit: If `True`, then it automatically makes an API call on a value change (default=True)
        :return: ESIRemote object
        """
        self.host = host
        self.port = port
        self.session = session if session else requests.Session()
        self.autocommit = autocommit
        self._save_files: Union[List[Save], FilterList] = FilterList()
        self._active: Union[Active, None] = None
        self._operatoractors: Union[List[OperatorActor], FilterList] = FilterList()
        self.update_saves()
        self.update_active()
        self.update_operator_actors()

    def _api_get(self, path_name):
        """
        Internal GET call

        :param path_name: URL path
        :return: JSON-decoded response
        """
        return self.session.get(f"{self.host}:{self.port}/api/{path_name}").json()

    def _api_put(self, path_name, data):
        """
        Internal PUT call

        :param path_name: URL path
        :param data: Body of request (sent as JSON)
        :return: JSON-decoded response
        """
        return self.session.put(f"{self.host}:{self.port}/api/{path_name}", json=data).json()

    def _commit_save(self, force: bool = False):
        """
        Goes through each save and checks if it has an update.
        If so, it will commit the data and stops iterating.

        :param force: If `True`, the commit will be applied even if `autocommit` is turned off
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
        """
        Updates Save object list.
        """
        self._save_files = get_updated_values(self._save_files,
                                              self._api_get("save-files"),
                                              Save.parse,
                                              "absolutePath")
        for save in self._save_files:
            save.commit_callback = self._commit_save

    @property
    def save_files(self) -> List[Save]:
        # Make sure that it's actually a FilterList (it probably already is)
        return FilterList(self._save_files)

    def update_active(self):
        """
        Updates Active object.
        """
        if self._active:
            self._active.update_values(self._api_get("save-files/active"))
        else:
            self._active = Active.parse(self._api_get("save-files/active"))

    @property
    def active(self) -> Active:
        return self._active

    def _commit_operator_actors(self, force: bool = False):
        """
        Goes through OperatorActor list and checks if the object has an update.
        If so, this will commit the data.

        :param force: If `True`, the commit will be applied even if `autocommit` is turned off
        """

        if not (force or self.autocommit):
            return

        for actor in self.operator_actors:
            if actor.commit_changes:
                response = self._api_put("operatoractors", actor.commit_changes)
                if not response == {"answer": "actor has been updated"}:
                    raise ValueError(f"Answer from server not as expected: {repr(response)}")
                actor.commit_changes = dict()

        self.update_operator_actors()

    def update_operator_actors(self):
        """
        Updates OperatorActor object list.
        """
        self._operatoractors = get_updated_values(self._operatoractors,
                                                  self._api_get("operatoractors")["operatorActors"],
                                                  OperatorActor.parse,
                                                  "id")
        for actor in self.operator_actors:
            actor.commit_callback = self._commit_operator_actors

    @property
    def operator_actors(self) -> Union[List[OperatorActor], FilterList]:
        # Make sure that it's actually a FilterList (it probably already is)
        return FilterList(self._operatoractors)

    def commit(self):
        """
        Uploads/commits changes and updates the objects for OperatorActors.
        """
        self._commit_operator_actors()
        self.update_operator_actors()


def value_timer(start, end, seconds):
    """
    A time-based, linear generator.
    """
    # This function will either have to be extended or removed. Also, it shouldn't stay in this file.
    timer = time.time()
    while time.time() - timer < seconds:
        yield ((end - start) * ((time.time() - timer) / seconds)) + start
    yield end


if __name__ == "__main__":
    remote = ESIRemote()
    remote.save_files[9].sub_saves[0].load()
    print(remote.active)
    fahrzeug = remote.operator_actors.by_attribute(type="emergency_vehicle").first()
    remote.operator_actors[0].is_visible = False
    enum = remote.operator_actors[0].property_enums[0].all_values.by_attribute(enum_field_value="CLOSED").first()
    remote.operator_actors[0].property_enums[0].current_value = enum
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
    enums = remote.operator_actors[0].property_enums[0].all_values
    for enum in enums:
        if enum.enum_field_value == "OPEN":
            break
    remote.operator_actors[0].property_enums[0].current_value = enum
    remote.operator_actors[1].is_visible = True
