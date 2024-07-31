from typing import List, Union
import re
import json

variable_pattern = re.compile(r'(?<!^)(?=[A-Z])')


def prepare_variables(item: dict) -> dict:
    return {variable_pattern.sub("_", name).lower(): item[name] for name in item}


def commit(force: bool = False):
    raise NotImplementedError(f"commit(force={force}) needs to be replaced by a function")


def check_updates(items: List["Base"]):
    commit_changes = list()
    for item in items:
        if item.commit_changes:
            commit_changes.append(item.commit_changes)
    return commit_changes


def get_updated_values(old_items: List["Base"], new_items: list, object_parser, attribute_name: str = "name"):
    variable_name = variable_pattern.sub("_", attribute_name).lower()
    new_values = list()
    old_items_dict = {getattr(item, variable_name): item for item in old_items}
    for item in new_items:
        new_values.append(old_items_dict.get(item[attribute_name], object_parser(item)))
        new_values[-1].commit_changes = dict()
    return new_values


class Base:
    def __init__(self, *args, **kwargs):
        self.commit_changes = dict()
        self.commit_callback = commit

    @classmethod
    def parse(cls, item):
        return cls(**prepare_variables(item))

    def update_values(self, item):
        self.commit_changes = dict()
        for name, value in prepare_variables(item).items():
            setattr(self, f"_{name}", value)

    def commit(self, force: bool = False):
        # the actual update function has to be hid behind a function,
        # so it can be transferred down to subsaves and whatnot.
        self.commit_callback(force)


class Active(Base):
    def __init__(self, scenario_id: int, scenario_name: str):
        super().__init__()
        self._scenario_id = scenario_id
        self._scenario_name = scenario_name

    def __repr__(self):
        return f"Active(scenario_id={self.scenario_id}, scenario_name={self.scenario_name})"

    @property
    def scenario_id(self):
        return self._scenario_id

    @property
    def scenario_name(self):
        return self._scenario_name


class Save(Base):
    def __init__(self, scenario_id: int, scenario_name: str, category_name: str, absolute_path: str,
                 sub_saves: List['Save']):
        super().__init__()
        self._scenario_id = scenario_id
        self._scenario_name = scenario_name
        self._category_name = category_name
        self._absolute_path = absolute_path
        self._sub_saves = sub_saves

    def __repr__(self):
        return (f"Save(scenario_id={self._scenario_id}, "
                f"scenario_name={self._scenario_name}, "
                f"category_name={self._category_name}, "
                f"absolute_path={self._absolute_path}, "
                # need to restrict the output
                f"sub_saves=[{', '.join([f'Save(scenario_name={sub.scenario_name})' for sub in self._sub_saves])}])")

    @classmethod
    def parse(cls, item):
        save = cls(**prepare_variables({**item, **{"subSaves": [cls.parse(sub) for sub in item["subSaves"]]}}))
        for sub_save in save.sub_saves:
            sub_save.commit_callback = save.commit
        return save

    def update_values(self, item):
        return super().update_values({
            **item,
            **{"subSaves": get_updated_values(self.sub_saves,
                                              item["subSaves"],
                                              Save.parse, "absolutePath")}
        })

    def commit(self, force: bool = True):
        for sub_save in self.sub_saves:
            if sub_save.commit_changes:
                self.commit_changes = sub_save.commit_changes
                break
        self.commit_callback(force=force)

    @property
    def scenario_id(self):
        return self._scenario_id

    @property
    def scenario_name(self):
        return self._scenario_name

    def category_name(self):
        return self._category_name

    @property
    def absolute_path(self):
        return self._absolute_path

    @property
    def sub_saves(self):
        return self._sub_saves

    def load(self, force_commit=True):
        self.commit_changes["absolutePath"] = self.absolute_path
        self.commit(force_commit)


def convert_type_value(_type: str, value: str):
    new_type = None
    new_value: Union[bool, str, int, float, None] = None

    if _type == "bool":
        new_type = bool
        new_value: bool = json.loads(value)
    elif _type == "string":
        new_type = str
        new_value: str = value
    elif _type == "int":
        new_type = int
        new_value: int = int(value)
    elif _type == "float":
        new_type = float
        new_value: float = float(value)

    return new_type, new_value


class Property(Base):
    def __init__(self, display_name: str, name: str, type: str, value: str, min_value: int, max_value: int,
                 step_size: int):
        super().__init__()
        self._display_name = display_name
        self._name = name
        self._type, self._value = convert_type_value(type, value)
        self._min_value = min_value
        self._max_value = max_value
        self._step_size = step_size

    @property
    def display_name(self):
        return self._display_name

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = self.type(value)
        self.commit_changes["value"] = json.dumps(self._value)
        self.commit_changes["name"] = self.name  # has to be included
        self.commit()

    @property
    def min_value(self):
        return self._min_value

    @property
    def max_value(self):
        return self._max_value

    @property
    def step_size(self):
        return self._step_size


class PropertyArray(Base):
    """
    This is probably a WIP item from FwESI, but since I don't know the possible attributes,
    I'm going to make the best out of it.
    """

    def __init__(self, **kwargs):
        print("PropertyArrays are not implemented yet")
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)


class EnumField(Base):
    def __init__(self, enum_field_id: int, enum_field_value: str):
        super().__init__()
        self._enum_field_id = enum_field_id
        self._enum_field_value = enum_field_value

    @property
    def enum_field_id(self):
        return self._enum_field_id

    @property
    def enum_field_value(self):
        return self._enum_field_value


class PropertyEnum(Base):
    def __init__(self, name: str, type: str, display_name: str, all_values: List[EnumField], current_value: EnumField):
        super().__init__()
        self._name = name
        self._type = type
        self._display_name = display_name
        self._all_values = all_values
        self._current_value = current_value

    @classmethod
    def parse(cls, item):
        enum_fields = {value["enumFieldId"]: EnumField.parse(value) for value in item["allValues"]}
        return cls(**prepare_variables({
            **item,
            **{"currentValue": enum_fields[item["currentValue"]["enumFieldId"]]},
            **{"allValues": list(enum_fields.values())}  # by using **{} we can replace keys/values from item
        }))

    def update_values(self, item):
        self.commit_changes = dict()
        new_enums = dict()
        for enum_new in item["allValues"]:
            enum_field = None
            for enum_field in self.all_values:
                if (enum_field.enum_field_id,
                    enum_field.enum_field_value) == (enum_new["enumFieldId"],
                                                     enum_new["enumFieldValue"]):
                    break
            if not enum_field:
                enum_field = EnumField.parse(enum_new)
            new_enums[enum_field.enum_field_id] = enum_field

        # this is written without .get(...) so if something goes wrong, we purposely get an error
        return super().update_values({
            **item,
            **{"currentValue": new_enums[item["currentValue"]["enumFieldId"]]},
            **{"allValues": list(new_enums.values())}
        })

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @property
    def display_name(self):
        return self._display_name

    @property
    def all_values(self):
        return self._all_values

    @property
    def current_value(self):
        return self._current_value

    @current_value.setter
    def current_value(self, value: EnumField):
        if value not in self._all_values:
            raise ValueError(f"Value {value} is not in all_values.")
        self._current_value = value
        self.commit_changes["currentValue"] = {
            "enumFieldId": value.enum_field_id,
            "enumFieldValue": value.enum_field_value
        }
        self.commit_changes["name"] = self.name
        self.commit()


class Action(Base):
    def __init__(self, name: str, display_name: str, button_name: str):
        super().__init__()
        self._name = name
        self._display_name = display_name
        self._button_name = button_name

    @property
    def name(self):
        return self._name

    @property
    def display_name(self):
        return self._display_name

    @property
    def button_name(self):
        return self._button_name

    def trigger(self):
        self.commit_changes["name"] = self.name
        self.commit()


class OperatorActor(Base):
    def __init__(self,
                 name: str,
                 id: int,
                 is_visible: bool,
                 type: str,
                 properties: List[Property],
                 property_arrays: List[PropertyArray],
                 property_enums: List[PropertyEnum],
                 actions: List[Action]):
        super().__init__()
        self._name = name
        self._id = id
        self._is_visible = is_visible
        self._type = type
        self._properties = properties
        self._property_arrays = property_arrays
        self._property_enums = property_enums
        self._actions = actions

    @classmethod
    def parse(cls, item):
        actor = cls(**prepare_variables({
            **item,
            **{"properties": [Property.parse(_property) for _property in item["properties"]]},
            **{"propertyArrays": [PropertyArray.parse(property_array) for property_array in item["propertyArrays"]]},
            **{"propertyEnums": [PropertyEnum.parse(property_enum) for property_enum in item["propertyEnums"]]},
            **{"actions": [Action.parse(action) for action in item["actions"]]}
        }))
        for item in actor.properties + actor.property_arrays + actor.property_enums + actor.actions:
            item.commit_callback = actor.commit
        return actor

    def commit(self, force: bool = False):
        """
        check all attributes if anything changed and if so, append the ID before triggering an update.
        """
        properties = check_updates(self.properties)
        property_arrays = check_updates(self.property_arrays)
        property_enums = check_updates(self.property_enums)
        actions = check_updates(self.actions)
        if properties:
            self.commit_changes["properties"] = properties
        if property_arrays:
            self.commit_changes["propertyArrays"] = property_arrays
        if property_enums:
            self.commit_changes["propertyEnums"] = property_enums
        if actions:
            self.commit_changes["actions"] = actions

        if self.commit_changes:
            self.commit_changes["id"] = self.id

        self.commit_callback(force=force)

    def update_values(self, updated_values):
        self.commit_changes = dict()
        new_values = {
            "properties": get_updated_values(self.properties,
                                             updated_values["properties"],
                                             Property.parse),
            "propertyArrays": get_updated_values(self.property_arrays,
                                                 updated_values["propertyArrays"],
                                                 PropertyArray.parse),
            "propertyEnums": get_updated_values(self.property_enums,
                                                updated_values["propertyEnums"],
                                                PropertyEnum.parse),
            "actions": get_updated_values(self.actions,
                                          updated_values["actions"],
                                          Action.parse)
        }
        return super().update_values({
            **updated_values,
            **new_values
        })

    @property
    def name(self):
        return self._name

    @property
    def id(self):
        return self._id

    @property
    def is_visible(self):
        return self._is_visible

    @is_visible.setter
    def is_visible(self, value):
        self._is_visible = value
        self.commit_changes["isVisible"] = value
        self.commit()

    @property
    def type(self):
        return self._type

    @property
    def properties(self):
        return self._properties

    @property
    def property_arrays(self):
        return self._property_arrays

    @property
    def property_enums(self):
        return self._property_enums

    @property
    def actions(self):
        return self._actions
