# @file exceptions.py
# @author Markus Führer
# @date 7 Jan 2022
# @copyright Copyright © 2022 by Bentham Instruments Ltd.


class ExternalDeviceNotFound(IOError):
    """The target device was not found."""


class DeviceClosed(IOError):
    """The connection to the target device is not open."""


class SCPIError(RuntimeError):
    """The target device has responded with an error in response to a command."""

    def __init__(self, code: int, message: str):
        super().__init__(f"SCPI error {code}: {message}")
        self.code = code
        self.scpi_message = message
