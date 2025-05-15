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
#     Vinay N, MCCI Corporation Aug 2024
#
# Revision history:
#     V1.0.0 Mon Aug 12 2024 01:00:00   Vinay N 
#       Module created
##############################################################################

# from model2450lib import searchmodel
# from model2450lib import searchmodel
from model2450lib import searchmodel
from uiGlobal import *

def firmware_version():
    # dev_ver =
    pass 

def search_device():
    """
    searching the devices
    Args:
        top: top creates the object
    Returns:
        findict: network device list
        dev_dict: devices in dictionary
    """
    dev_dict = searchmodel.get_models()
    return dev_dict

def get_avail_ports(top):
    """
    Get the list of avalible ports

    Args:
        None

    Returns:
        dev_list: return the comport
    """
    dev_list = searchmodel.get_avail_ports()
    return dev_list

def get_dev_baud(devname):
    devidx = None
    for i in range(len(DEVICES)):
        if devname == DEVICES[i]:
            # self.top.selDevice = i
            devidx = i
            break
    return devidx
