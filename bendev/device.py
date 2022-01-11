# @file device.py
# @author Markus Führer
# @date 7 Jan 2022
# @copyright Copyright © 2022 by Bentham Instruments Ltd. 

import sys, time
import hid # from pip install hidapi

from bendev.exceptions import ExternalDeviceNotFound, DeviceClosed

_ON_WINDOWS = (sys.platform == "win32")
_MAX_CHARACTERS = 64 # max size of USB HID packet

class Device: 
    """Simple High Level text-based SCPI over USB/HID communication interface."""
    def __init__(self, serial_number=None, product_string=None, manufacturer_string="Bentham", encoding="ascii"):
        """connect to the first device matching exact serial_number (if present) or
        containing product_string (if present) or containing manufacturer_string.
        Raises ExternalDeviceNotFound exception if no device matches."""
        self.device = None
        self.encoding = encoding
        found_devices = hid.enumerate()
        for dev in found_devices:
            if serial_number:
                if serial_number == dev["serial_number"]:
                    break
            elif product_string:
                if product_string in dev["product_string"]:
                    break
            elif manufacturer_string:
                if manufacturer_string in dev["manufacturer_string"]:
                    break
            else:
                raise 
        else:
            raise ExternalDeviceNotFound(f"Can't find device ({serial_number or product_string})")
        self.device = hid.device()
        self.device.open(dev["vendor_id"], dev["product_id"], dev["serial_number"])
        self.device.set_nonblocking(True) # we'll handle waiting outselves
    
    def verify_open(self):
        if not self.device:
            raise DeviceClosed("This device connection is not open.")
    
    def write(self, command):
        """write a max 64 character command to the device"""
        self.verify_open()
        if (len(command) > _MAX_CHARACTERS):
           raise IOError(f"Tried to send {len(command)} characters, max is {_MAX_CHARACTERS}")
        if _ON_WINDOWS: 
            command = "\x00"+command # hidapi calls on Windows require leading 0. 
                    #(arg may be _MAX_CHARACTERS+1 chars in that case, that's ok)
        self.device.write(command.encode(self.encoding))

    def read(self, read_interval, timeout):
        """read every read_interval seconds until a the device sends a message
        or timeout seconds have elapsed."""
        self.verify_open()
        read_start_time = time.time()
        while len(block := self.device.read(_MAX_CHARACTERS)) == 0:
            time.sleep(read_interval)
            if (timeout != 0) and time.time() - read_start_time > timeout:
                raise TimeoutError(f"TLS120Xe failed to respond in {timeout} seconds")
        return bytes(block).decode(self.encoding).rstrip("\r\n\x00")

    def query(self, command, timeout=0, read_interval=0.05):
        """Send a command and try to read a reply every read_interval seconds until
        one arrives or timeout seconds have elapsed."""
        self.write(command)
        return self.read(read_interval=read_interval, timeout=timeout)
    
    def __del__(self):
        self._close()

    def _close(self):
        if self.device:
            self.device.close()
            self.device = None

    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self._close()
        return False

def list_connected_devices(manufacturer="Bentham", product=None, verbose=False):
    """list all the connected HID devices that match the manufacturer or product.
    Returns a list of device dictionaries. If verbose: print a summary.
    """
    if verbose:
        print ("Connected Devices:")
    devices = hid.enumerate()
    filtered_devices = []
    for i, device in enumerate(sorted(devices, key=lambda d: d["path"])):
        if manufacturer is not None and\
            manufacturer.upper() not in device['manufacturer_string'].upper(): 
            continue
        if product is not None and\
            product.upper() not in device['product_string'].upper(): 
            continue
        if verbose:
            print (f"Device {i+1}: ", end="")
            print (f"{device['manufacturer_string']}, ", end="")
            print (f"{device['product_string']}, ", end="")
            print (f"sn={device['serial_number']}, ", end="")
            print (f"v={device['vendor_id']}, ", end="")
            print (f"p={device['product_id']}")
        filtered_devices.append(device)
    return filtered_devices

if __name__ == "__main__":
    devs = list_connected_devices(verbose=True)
    if len(devs) != 0:
        with Device(serial_number = devs[0]["serial_number"]) as device:
            print (device.query("*IDN?"))

        with Device(product_string=devs[0]["product_string"]) as device:
            print (device.query("*IDN?"))

        d = Device()
        print (d.query("*IDN?"))
        del d
    else:
        print ("No devices found")