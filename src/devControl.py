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

from model2450lib import searchswitch
# from model2450lib import switch2450

# from model2450lib import searchswitch

from uiGlobal import *

# from uiGlobals import *



# def search_device():
#     dev_list = searchswitch.get_switches()
#     return dev_list

#     # print("Dev_list:", dev_list)

def get_avail_ports(top):
    """
    Get the list of avalible ports

    Args:
        None

    Returns:
        dev_list: return the comport
    """
    dev_list = searchswitch.get_avail_ports()
    return dev_list

def search_device():
    """
    searching the devices
    Args:
        top: top creates the object
    Returns:
        findict: network device list
        dev_dict: devices in dictionary
    """
    dev_dict = searchswitch.get_switches()
    return dev_dict



def get_dev_baud(devname):
    devidx = None
    for i in range(len(DEVICES)):
        if devname == DEVICES[i]:
            # self.top.selDevice = i
            devidx = i
            break
    return devidx

def connect_device(swdict):
    """
    Connect the device.
    """
    print("connect-device:", swdict)

def disconnect_device(self):
    pass
    


