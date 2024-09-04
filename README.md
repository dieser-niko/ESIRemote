# ESIRemote

A Python library to remotely control the environment in [FwESI](https://fwesi.de/)

## Functionality

### FwESI
<details><summary>expand</summary>

FwESI has a remote control (basically a local web server) where the user can control the application without having to interact with the computer itself.

This includes actions such as
- loading save file/sub save
- controlling variables of a fire engine (such as the height and length of the ladder)
- start a fire (in FwESI)
- check state of door
- show/hide elements

The last action is still quite buggy with smoke in the latest tested version (1.10.1) and needs to be fixed by the FwESI developers.
Actions like video control are also a bit unstable.

What **CAN'T** be done:
- read/change coordinates of elements (like the user himself)
- get a livestream of the situation
- detect button presses (there are no buttons)
</details>

### ESIRemote
The library automatically parses the available objects (also called OperatorActors), parameters and save files as Python objects.

By default, ESIRemote allows the user to modify the attributes of these objects.
Changes are applied automatically, but this can be turned off.

Anything available on the remote server can be used with this library.


## Installation

ESIRemote is still in early development, but can already be installed using PyPI:
```console
pip install esiremote
```

## Quick Start
Check out the (TODO) examples directory to get an idea of how you can use ESIRemote.

Before you can use this library, make sure the remote server is enabled. You can enable it by default in the settings.

Also make sure you have objects with the remote option enabled.
```python3
from esiremote import ESIRemote

remote = ESIRemote()
for operatoractor in remote.operatoractors:
    print(operatoractor.name)
```
This little example lists all elements available. 

---
<details><summary>TODO list</summary>

- [ ] Add more docstrings and comments
- [x] Add more to readme (stuff like installation and usage)
- [x] Add more helper functions (like search by ID, name, type, etc)
  - Maybe do something like a custom list object with a function called "search_by_attribute" or something
- [ ] remove test code
- [ ] add some examples (and maybe supply scenes)
- [ ] make sure it works flawlessly (check the models especially)
- [x] add `setup.py` or `pyproject.toml`
- [x] publish to PyPi with GH Actions
- [ ] add unittests
- [ ] Feature: load external save file (might not work at all)
</details>
