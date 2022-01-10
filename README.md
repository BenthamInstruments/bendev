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

bendev devices can be instantiated in context managers:

```
>>> import bendev
>>> with bendev.Device as dev:
...     print(dev.query("*IDN?"))
"Bentham Instruments Ltd.","MSH150_RD_Direct","99999/9","1.2.53"
```

or normally:

```
>>> import bendev
>>> my_tls = bendev.Device()
>>> my_tls.write("SYSTEM:REMOTE")
>>> my_tls.query("MONO:GOTO? 555")
"1"
```

Devices can be opened by serial number, product string or manufacturer string:

```
>>> import bendev
>>> device_a = bendev.Device(serial_number="99999/9")
>>> device_b = bendev.Device(product_string="TLS120Xe")
>>> device_c = bendev.Device(manufacturer_string="Bentham")
```

For product_string and manufacturer string, it is sufficient if the given substring is present in the device descriptor. The serial number has to be exact. Manufacturer_string defaults to "Bentham".

The package can also tell you what devices are connected:

```
>>> import bendev
>>> devs=bendev.list_connected_devices(verbose=True)
Connected Devices:
Device 18: Bentham Instruments, TLS120Xe, ...
```

