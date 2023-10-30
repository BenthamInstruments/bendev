bendev
======

A crossplatform Python package for communicating with the USB/SCPI-enabled Bentham Instruments hardware devices such as the TLS120Xe. The package uses hidapi to send and receive text based commands and replies using the USB HID protocol.

Compatibility
-------------

This software has been tested on Mac OS X, Ubuntu, and Windows, with python 3.8 onwards. It is compatible Bentham Instruments devices with an SCPI over USB HID packet interface.

Installation
------------

`pip install bendev`

Usage
-----

bendev devices can be instantiated in context managers:

``` python
>>> import bendev
>>> with bendev.Device() as dev:
...     print(dev.query("*IDN?"))
"Bentham Instruments Ltd.","MSH150_RD_Direct","99999/9","1.2.53"
```

or normally:

``` python
>>> import bendev
>>> my_tls = bendev.Device()
>>> my_tls.write("SYSTEM:REMOTE")
>>> my_tls.query("MONO:GOTO? 555")
"1"
```

Devices can be opened by serial number, product string or manufacturer string:

``` python
>>> import bendev
>>> device_a = bendev.Device(serial_number="99999/9")
>>> device_b = bendev.Device(product_string="TLS120Xe")
>>> device_c = bendev.Device(manufacturer_string="Bentham")
```

For `product_string` and `manufacturer_string`, it is sufficient if the given substring is present in the device descriptor. The `serial_number` has to be exact. `manufacturer_string` defaults to `"Bentham"`.

The package can also tell you what devices are connected:

``` python
>>> import bendev
>>> devs=bendev.list_connected_devices(verbose=True)
Connected Devices:
Device 18: Bentham Instruments, TLS120Xe, ...
```

Known issues
------------

On ubuntu the python hidapi module has been noted to fail to read device strings for an unknown reason; until this is resolved the devices may be opened as raw hid devices, bypassing the hidapi module:

``` python
>>> import bendev
>>> my_device = bendev.Device(hidraw = "/dev/hidraw2")
>>> my_device.query("*IDN?")
'"Bentham Instruments Ltd.","TLS120Xe","12345/6","0.5.3"'
```


Version history
---------------

- v0.0.1 - v0.0.3: test releases
- v0.0.4: first release
- v0.1.0: added ability to use raw hid devices
- v0.1.1: fix formatting issue
- v0.2.0: add reconnect command
- v0.3.0: add python 3.11 compatibility
- v0.3.1: fix inverted vendor ID filter in list_connected_devices
