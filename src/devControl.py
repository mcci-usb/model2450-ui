##############################################################################
# 
# Module: devControl.py
#
# Description:
#     Receive device function commands from resepective device window
#     Check if the device is available in network, then send command to server
#     If the device is available in same computer then send command to device
#
# Author:
#     Vinay N, MCCI Corporation February 2026
#
# Revision history:
#     V2.2.0 Fri Feb 2026 20:02:2026   Vinay N
#       Module created
#
##############################################################################

from model2450lib import searchmodel
from uiGlobal import *

# =============================================================================
# COMPONENTS
# =============================================================================


def firmware_version():
    """
    Retrieve firmware version information from the device.

    This function is intended to query the connected
    Model2450 device and obtain firmware version details.

    Args:
        None

    Returns:
        None
    """
    pass


def search_device():
    """
    Search for available Model devices on the network.

    This function queries the model search utility to
    discover connected or network-accessible devices.

    Args:
        None

    Returns:
        dict:
            Dictionary containing discovered device
            information.
    """
    dev_dict = searchmodel.get_models()
    return dev_dict


def get_avail_ports(top):
    """
    Retrieve available serial communication ports.

    This function queries the system for available
    COM ports that can be used for device connection.

    Args:
        top:
            Reference to the top-level window
            (not used directly).

    Returns:
        list:
            List of available serial ports.
    """
    dev_list = searchmodel.get_avail_ports()
    return dev_list


def get_dev_baud(devname):
    """
    Get device index corresponding to the device name.

    This function searches the global DEVICES list
    and returns the index of the matching device.

    Args:
        devname:
            Name of the device.

    Returns:
        int | None:
            Index of the device in DEVICES list
            if found, otherwise None.
    """
    devidx = None

    for i in range(len(DEVICES)):
        if devname == DEVICES[i]:
            devidx = i
            break

    return devidx