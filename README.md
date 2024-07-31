# ESIRemote

A Python library to remotely control the environment in [FwESI](https://fwesi.de/)

This library is still in early development, but can already be used with some modifications.

## Functionality

FwESI has a remote control (basically a local web server) where the user can control the application without having to interact with the computer itself.

This includes actions such as
- changing the map
- controlling variables of a fire engine (such as the height of the ladder)
- start a fire (in FwESI)
- show/hide elements
- check state of door

The last action is still quite buggy with smoke in the latest tested version (1.10.1) and needs to be fixed by the FwESI developers.
Actions like video control are also a bit unstable.

What **CAN'T** be done:
- read/change coordinates of elements (like the user himself)
- get a livestream of the situation
- detect button presses (there are no buttons)

---

TODO: Add more
