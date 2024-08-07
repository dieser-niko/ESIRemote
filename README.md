# ESIRemote

A Python library to remotely control the environment in [FwESI](https://fwesi.de/)

This library is still in early development, but can already be used with some modifications.

## Functionality

FwESI has a remote control (basically a local web server) where the user can control the application without having to interact with the computer itself.

This includes actions such as
- changing the map
- controlling variables of a fire engine (such as the height of the ladder)
- start a fire (in FwESI)
- check state of door
- show/hide elements

The last action is still quite buggy with smoke in the latest tested version (1.10.1) and needs to be fixed by the FwESI developers.
Actions like video control are also a bit unstable.

What **CAN'T** be done:
- read/change coordinates of elements (like the user himself)
- get a livestream of the situation
- detect button presses (there are no buttons)

---

## TODO list

- [ ] Add more docstrings and comments
- [ ] Add more to readme (stuff like installation and usage)
- [ ] remove test code
- [ ] add some examples (and maybe supply scenes)
- [ ] make sure it works flawlessly (check the models especially)
- [ ] add `setup.py` or `pyproject.toml`
- [ ] publish to PyPi with GH Actions
