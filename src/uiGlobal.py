##############################################################################
# 
# Module: uiGlobal.py
#
# Description:
#     Define all global variables for the entire UI Model2450 App.
#
# Author:
#     Vinay N, MCCI Corporation Aug 2024
#
# Revision history:
#     V1.0.0 Mon Aug 12 2024 01:00:00   Vinay N 
#       Module created

##############################################################################
# Lib imports
import wx
import os

DEFAULT_FONT_SIZE = 8
DEV_2450    = 0
BAUDRATE = [115200, 115200, 0, 9600]

DEVICES    = ["2450"]

IMG_ICON = "mcci_logo.ico"
IMG_LOGO = "mcci_logo.png"

ID_MENU_FILE_CLOSE  = 1012
ID_MENU_HELP_ABOUT = 1019
ID_MENU_HELP_WEB = 1017
ID_MENU_HELP_PORT = 1018
ID_MENU_HELP_PDB = 1020
ID_MENU_HELP_DNC = 1021
ID_ABOUT_IMAGE = 1033
ID_MENU_LOGIN = 1034

EVT_RESULT_ID = 1035
ID_BTN_DEV_SCAN = 1036
ID_BTN_ADD = 1037
# ID_BTN_DEV_SCAN
ID_BTN_CONNECT = 1038

ID_CONNECT_SWITCH_MENU = 1039
# config_menu
ID_CONFIG_MENU = 1040
ID_SET_COLOR_MENU = 1041

ID_MENU_HELP_3141 = 1015
ID_MENU_HELP_3201 = 1016
ID_MENU_HELP_2101 = 1026
ID_MENU_HELP_2301 = 1027
ID_MENU_HELP_WEB = 1028
ID_MENU_HELP_PORT = 1029
ID_MENU_HELP_ABOUT = 1030
ID_MENU_HELP_2450 = 1031

ID_BTN_AUTO = 1050
ID_BTN_CLEAR = 1051

ID_MENU_MODEL_CONNECT = 1052
ID_MENU_MODEL_DISCONNECT = 1053



mcci_web = "https://mcci.com/"
mcci_support = "https://portal.mcci.com/portal/home"

#======================================================================
# GLOBAL STRINGS
#======================================================================
VERSION_NAME  = "\nMCCI"+u"\u00AE"+" Model2450 UI"
VERSION_ID    = ""
VERSION_COPY  = "\nCopyright "+u"\u00A9"+" 2024 MCCI Corporation"
VERSION_STR = "V1.0.0"

class NumericValidator(wx.Validator):
    """
    Validator associated NumericValidator Control.
    """
    
    def __init__(self):
        """
        Only digits are allowed in the address.

        Args:
            self: The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
        Returns:
            None
        """
        
        wx.Validator.__init__(self)
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self, arg=None):
        """
        Only digits are allowed in the address. 

        Args:
            self: The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
        Returns:
            NumericValidator():return True if all characters in the string are
            numaric charecters    

        """
       
        return NumericValidator()
   
    def Validate(self, win):
        """
        Only digits are allowed in the textcontrol. 

        Args:
            self: The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
            win: window object is created.
        Returns:
           val.isdigit - "True" if all characters in the string are digits.
        """
        
        # Returns the window associated with the validator.
        tc  = self.GetWindow()
        val = tc.GetValue()
        return val.isdigit()
   
    def OnChar(self, evt):
        """
        all key names and charachters dirctly can use. 
        
        Args:
            self: The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
            evt:evt handler to display the characters
        Returns:
            None
        """
        
        # Returns the window associated with the validator.
        tc = self.GetWindow()
        key = evt.GetKeyCode()

        # For the case of delete and backspace, pass the key
        if (key == wx.WXK_BACK or key == wx.WXK_DELETE  or key > 255):
            evt.Skip()
            return
      
        elif (chr(key).isdigit() or chr(key) == "."):
            evt.Skip()
            return
