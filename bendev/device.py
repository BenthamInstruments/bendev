# -*- coding:utf-8 -*-
# @file device.py
# @author Markus Führer
# @date 7 Jan 2022
# @copyright Copyright © 2022 by Bentham Instruments Ltd.

import sys, time
import hid  # from pip install hidapi
import bendev.file_device as file_device
import logging

from bendev.exceptions import ExternalDeviceNotFound, DeviceClosed, SCPIError

_ON_WINDOWS = (sys.platform == "win32")
_MAX_CHARACTERS = 64  # max size of USB HID packet

logger = logging.getLogger("bendev")


def scpi_convert(p: str) -> str | int | float:
    """Converts a string reply from a SCPI device to a string, int or float.
    If the string can be converted to an int, it is. If it can be converted 
    to a float, it is. Otherwise, the string is returned unaltered.

    Arguments:
        reply: string containing the reply from the SCPI device

    Returns:
        string, int or float
    """
    if p.startswith('"') and p.endswith('"'):
        return p[1:-1]

    try:
        return int(p)
    except ValueError:
        try:
            return float(p)
        except ValueError:
            return p


class Device:
    """Simple High Level text-based SCPI over USB/HID communication interface 
    device class. Instantiation of this class connects to a device or raises
    an exception. Devices can be identified by serial number, product 
    string,or manufacturer string. The connection can be closed manually 
    or automatically when the instance is destroyed.
    
    Also functions as a context manager:
    >>> with bendev.Device() as device:
    ...     device.write("SYSTEM:LOCAL")

    The messages are encoded as ascii (configurable on initialisation) but
    otherwise sent unaltered as USB HID packets.
    """

    def __init__(self,
                 serial_number=None,
                 product_string=None,
                 manufacturer_string="Bentham",
                 encoding="ascii",
                 vendor_id=1240,
                 product_id=None,
                 hidraw=None,
                 path=None):
        """Connects to the first device matching exact serial_number (if 
        present) or containing product_string (if present) or containing 
        manufacturer_string. Raises ExternalDeviceNotFound exception if no 
        device matches.

        Arguments:
            serial_number: string containing the exact serial number | None
            product_string: string containing part of the target product 
              name | None
            manufacturer_string: string containing part of the device's 
              manufacturer | None
            vendor_id: the vendor ID of the target device | None 
              | default 1240
            product_id: the product ID of the target device | None
            hidraw: device path, usually in /dev | None

        Bendev identifies the correct device differently depending on which 
        arguments are provided. If multiple from the list below are
        provided, the first matching entry in the list is used to judge 
        if a device is the correct device. 
        - if hidraw if provided: bypass the hid module and read/write using 
            the os module to read and write the raw hid device identified by 
            the path, e.g.: 
                >>> device = Device(hidraw="/dev/hidraw2")
        - if serial number is provided: serial number must match exactly
        - product string: the string is a substring of the device product 
            string
        - vendor ID and product ID: both must match exactly
        - vendor ID only: vendor ID must match exactly
        - manufacturer string: the string is a substring of the device 
            manufacturer string

        If for example the serial number and vendor_ID are provided, the 
        vendor_ID, being further down in the list, is ignored and the device
        is solely identified by serial number.
        """

        self.serial_number = serial_number
        self.product_string = product_string
        self.manufacturer_string = manufacturer_string
        self.encoding = encoding
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.hidraw = hidraw
        self.path = path

        self.usb_info = None

        self._connect()

    def _connect(self):
        """Connect using the parameters set at __init__ time."""
        self.device = None
        if self.hidraw is None:
            found_devices = hid.enumerate()
            for dev in found_devices:
                if self.path:
                    if self.path == dev["path"]:
                        break
                if self.serial_number:
                    if self.serial_number == dev["serial_number"]:
                        break
                elif self.product_string:
                    if self.product_string in dev["product_string"]:
                        break
                elif self.vendor_id and self.product_id:
                    if self.vendor_id == dev[
                            "vendor_id"] and self.product_id == dev[
                                "product_id"]:
                        break
                elif self.vendor_id:
                    if self.vendor_id == dev["vendor_id"]:
                        break
                elif self.manufacturer_string:
                    if self.manufacturer_string in dev["manufacturer_string"]:
                        break
                else:
                    raise ValueError(
                        "Missing qualifier; serial_number, product_string and manufacturer_string can't all be None."
                    )
            else:
                raise ExternalDeviceNotFound(
                    f"Can't find device ({self.serial_number or self.product_string})"
                )
            
            self.device = hid.device()
            if self.path:
                logger.info(f"Connecting to device at {self.path}")                
                self.device.open_path(self.path)
            else:
                logger.info(f"Connecting to device with VID={dev["vendor_id"]}, PID={dev["product_id"]}" + " & SN={dev['serial_number']}" if self.serial_number else "")
                self.device.open(
                    dev["vendor_id"], dev["product_id"],
                    dev["serial_number"] if self.serial_number else None)
            self._update_info(dev)
            self.device.set_nonblocking(True)  # we'll handle waiting outselves
        else:
            self.device = file_device.FileDevice(self.hidraw)

    def _update_info(self, dev_info: dict):
        """Update the device information."""
        for k, v in dev_info.items():
            setattr(self, k, v)
        self.usb_info = dev_info

    def _verify_open(self):
        if not self.device:
            raise DeviceClosed("This device connection is not open.")

    def get_usb_info(self):
        """Returns a dictionary containing the USB information of the device.
        The dictionary contains the following keys:
        - path
        - serial_number
        - manufacturer_string
        - product_string
        - vendor_id
        - product_id
        """
        return self.usb_info

    def reconnect(self):
        """Close and reopen this device's connection using the same
        parameters as the bendev.Device instance was initially initialized
        with."""
        logger.info("Reconnecting to device")
        self.close()
        self._connect()

    def write(self, command):
        """Writes a max 64 character command to the device. Raises IOError on
        commands that are too long.

        Arguments:
            command: python string containing the command

        Returns:
            None
        """
        self._verify_open()
        if (len(command) > _MAX_CHARACTERS):
            raise IOError(
                f"Tried to send {len(command)} characters, max is {_MAX_CHARACTERS}"
            )
        logger.debug(f">>> {command}")
        if _ON_WINDOWS:
            command = "\x00" + command  # hidapi calls on Windows require leading 0.
            #(arg may be _MAX_CHARACTERS+1 chars in that case, that's ok)
        self.device.write(command.encode(self.encoding))

    def read(self, timeout, read_interval):
        """Reads every read_interval seconds until the device sends a message,
        or until timeout seconds have elapsed, in which case a TimeoutError 
        is raised.

        Arguments:
            timeout: number, time in seconds before raising a TimeoutError 
                if no message is received. 0 or None means never time out.
            read_interval: number, time in seconds to sleep between attempts 
                to read
        
        Returns:
            the device reply as a string
        """
        self._verify_open()
        read_start_time = time.time()
        while len(block := self.device.read(_MAX_CHARACTERS)) == 0:
            time.sleep(read_interval)
            if (timeout != 0) and time.time() - read_start_time > timeout:
                raise TimeoutError(
                    f"Device failed to respond in {timeout} seconds")
        data = bytes(block).decode(self.encoding).rstrip("\r\n\x00")
        logger.debug(f"<<< {data}")
        return data

    def query(self, command, timeout=0, read_interval=0.05):
        """Sends a command and tries to read a reply every read_interval 
        seconds  until one arrives, or until timeout seconds have elapsed, 
        in which case a TimeoutError is raised.

        Arguments:
            command: string containing the command to send
            timeout: number, time in seconds before raising a TimeoutError 
                if no message is received. 0 or None means never time out. 
                Default: 0
            read_interval: number, time in seconds to sleep between attempts 
                to read.
                Default: 0.05
        
        Returns:
            the device reply as a string
        """
        self.write(command)
        return self.read(read_interval=read_interval, timeout=timeout)

    def check_scpi_error(self, timeout=0, read_interval=0.05):
        """Checks the SCPI error queue for errors and raises a RuntimeError if
        any are found. This function is called automatically after each 
        command sent to the device. If you want to check the error queue 
        without sending a command, you can use the following command:
        >>> device.query(":SYST:ERR?")
        """
        error_count = self.query(":SYST:ERR:COUNT?", timeout=timeout, read_interval=read_interval)
        if error_count != "0":
            error = self.query(":SYST:ERR?").split(",")
            raise SCPIError(int(error[0]), error[1])

    def cmd(self, command, timeout=0, read_interval=0.05):
        """Sends a (non-query) command to the device. The SCPI error queue is
        checked for errors and if any are found, a SCPIError is raised.

        Arguments:
            command: string containing the command to send
            timeout: number, time in seconds before raising a TimeoutError 
                if no message is received. 0 or None means never time out. 
                Default: 0
            read_interval: number, time in seconds to sleep between attempts 
                to read.
                Default: 0.05
        
        Returns:
            the device reply as a string
        """
        self.write(command)
        try:
            self.check_scpi_error(timeout=timeout, read_interval=read_interval)
        except SCPIError as e:
            raise e

    def cmd_query(self,
                  command,
                  timeout=0,
                  read_interval=0.05) -> str | int | float | list[str | int | float]:
        """Sends a command and tries to read a reply every read_interval 
        seconds until one arrives, or until timeout seconds have elapsed, 
        in which case a TimeoutError is raised. The SCPI error queue is
        checked for errors and if any are found, a RuntimeError is raised.

        The reply is converted to a string, int or float if possible. If the
        reply is a comma separated list of values, each value is converted
        individually and the list of converted values is returned.

        Arguments:
            command: string containing the command to send
            timeout: number, time in seconds before raising a TimeoutError 
                if no message is received. 0 or None means never time out. 
                Default: 0
            read_interval: number, time in seconds to sleep between attempts 
                to read.
                Default: 0.05
        
        Returns:
            the device reply as a string
        """
        reply = self.query(command,
                           timeout=timeout,
                           read_interval=read_interval)
        try:
            self.check_scpi_error(timeout=timeout, read_interval=read_interval)
        except SCPIError as e:
            raise e

        reply = reply.split(",")

        reply = [scpi_convert(r) for r in reply]

        return reply[0] if len(reply) == 1 else reply

    def __del__(self):
        self.close()

    def close(self):
        """Close communication with the device."""
        if self.device:
            self.device.close()
            self.device = None

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
        return False  # do not catch exceptions


def list_connected_devices(manufacturer_string=None,
                           product_string=None,
                           vendor_ID=1240,
                           verbose=False):
    """list all the connected HID devices that match the manufacturer_string or
    product_string or vendor_ID. If a given string is found within the 
    appropriate device descriptor (even partially), the device is 
    considered to match.  Captialisation is not considered. If both 
    qualifiers are None, all devices are returned.

    Arguments:
        manufacturer_string: string containing the name of the 
            manufacturer of matching
            devices | None
        product_string: string containing the product name for matching 
            devices | None
        verbose: boolean indicating whether or not to also print out 
            matching devices to stdout
    
    Returns:
        list of dictionaries containing string:string device descriptor 
        information
    """
    if verbose:
        print("Connected Devices:")
    devices = hid.enumerate()
    filtered_devices = []
    for i, device in enumerate(sorted(devices, key=lambda d: d["path"])):
        if manufacturer_string is not None and\
            manufacturer_string.upper() not in device['manufacturer_string'].upper():
            continue
        if product_string is not None and\
            product_string.upper() not in device['product_string'].upper():
            continue
        if vendor_ID is not None and\
            vendor_ID != device['vendor_id']:
            continue
        if verbose:
            print(f"Device {i+1}: ", end="")
            print(f"{device['manufacturer_string']}, ", end="")
            print(f"{device['product_string']}, ", end="")
            print(f"sn={device['serial_number']}, ", end="")
            print(f"v={device['vendor_id']}, ", end="")
            print(f"p={device['product_id']}")
        filtered_devices.append(device)
    return filtered_devices


if __name__ == "__main__":
    devs = list_connected_devices(verbose=True)
    if len(devs) != 0:
        with Device(serial_number=devs[0]["serial_number"]) as device:
            print(device.query("*IDN?"))

        with Device(product_string=devs[0]["product_string"]) as device:
            print(device.query("*IDN?"))

        d = Device()
        print(d.query("*IDN?"))
        del d
    else:
        print("No devices found")
