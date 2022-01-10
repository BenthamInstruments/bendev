bendev
======

A crossplatform package for communicating with the USB/SCPI-enabled Bentham Instruments hardware devices such as the TLS120Xe. The package uses hidapi to send and receive text based commands and replies using the USB HID protocol. 

Compatibility
-------------

This software has been tested on Mac OS X, Ubuntu, and Windows, with python 3.8 onwards. It is compatible Bentham Instruments devices with an SCPI over USB HID packet interface.

Installation
------------

`pip install bendev`

Usage
-----

```
>>> import bendev
>>> my_tls = bendev.Device()
>>> my_tls.write("SYSTEM:REMOTE")
>>> my_tls.query("MONO:GOTO? 555")
```
