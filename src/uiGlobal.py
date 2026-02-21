##############################################################################
# 
# Module: uiGlobal.py
#
# Description:
#     Define all global variables for the entire UI Model2450 App.
#
# Author:
#     Vinay N, MCCI Corporation February 2026
#
# Revision history:
#     V2.2.0 Fri Feb 2026 20:02:2026   Vinay N
#       Module created
#
##############################################################################
# Third-party imports
import wx

# Built-in imports
import os


#======================================================================
# COMPONENTS
#======================================================================

DEFAULT_FONT_SIZE = 8

DEV_2450 = 0

BAUDRATE = [115200, 115200, 0, 9600]

DEVICES = ["2450"]

IMG_ICON = "mcci_logo.ico"
IMG_LOGO = "mcci_logo.png"
COLOR_IMG = "Color.png"
MCCI_LOGO = "mcci_logo_about.png"

# Menu IDs
ID_MENU_FILE_CLOSE = 1012
ID_MENU_HELP_MODEL2450LIB = 1015
ID_MENU_HELP_3201 = 1016
ID_MENU_HELP_WEB = 1017
ID_MENU_HELP_PORT = 1018
ID_MENU_HELP_ABOUT = 1019
ID_MENU_HELP_PDB = 1020
ID_MENU_HELP_DNC = 1021
ID_MENU_HELP_2101 = 1026
ID_MENU_HELP_2301 = 1027
ID_MENU_HELP_WEB_2 = 1028
ID_MENU_HELP_PORT_2 = 1029
ID_MENU_HELP_ABOUT_2 = 1030
ID_MENU_HELP_2450 = 1031

ID_ABOUT_IMAGE = 1033
ID_MENU_LOGIN = 1034
EVT_RESULT_ID = 1035
ID_BTN_DEV_SCAN = 1036
ID_BTN_ADD = 1037
ID_BTN_CONNECT = 1038
ID_CONNECT_MODEL_MENU = 1039
ID_CONFIG_MENU = 1040
ID_SET_COLOR_MENU = 1041

ID_CONNECT_MODEL = 2020
ID_DISCONNECT_MODEL = 2021
ID_CALIBRATION = 2022
ID_BLOCKFRAMES = 1547
ID_PLOTTING = 1548

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
VERSION_COPY  = "\nCopyright "+u"\u00A9"+" 2026 MCCI Corporation"
VERSION_STR = "V2.1.0"

class NumericValidator(wx.Validator):
    """
    Validator to allow only numeric input in text controls.
    """
    
    def __init__(self):
        """
        Initialize NumericValidator and bind character event.

        Args:
            None

        Returns:
            None
        """
        
        wx.Validator.__init__(self)
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self, arg=None):
        """
        Create a copy of the validator.

        Args:
            None

        Returns:
            NumericValidator:
                New instance of NumericValidator.
        """       
        return NumericValidator()
   
    def Validate(self, win):
        """
        Validate that the control contains only digits.

        Args:
            win:
                wx window associated with the validator.

        Returns:
            bool:
                True if all characters are numeric,
                otherwise False.
        """
        # Returns the window associated with the validator.
        tc  = self.GetWindow()
        val = tc.GetValue()
        return val.isdigit()
   
    def OnChar(self, evt):
        """
        Handle key press event and restrict input to digits.

        Args:
            event:
                wx key event object.

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
