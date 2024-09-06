
##############################################################################
# 
# Module: comDialog.py
#
# Description:
#     Dialog to show list of available MCCI Model 2450
#     Search, view, select and connect module
#
# Author:
#     Vinay N, MCCI Corporation Aug 2024
#
# Revision history:
#     V1.0.0 Mon Aug 12 2024 01:00:00   Vinay N 
#       Module created
##############################################################################
import wx
from uiGlobal import *
import devControl
# from model2450lib import searchmodel, model2450
from model2450lib import searchmodel
from model2450lib import model2450

import logWindow

class SearchModel(wx.PyEvent):
    """A class ServerEvent with init method"""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data

class ComDialog(wx.Dialog):
    """
    A  class AboutWindow with init method
    The AboutWindow navigate to MCCI Logo with naming of 
    application UI "Criket",Version and copyright info.  
    """
    def __init__(self, parent, title, control_window, firmware_window):
        """
        AboutWindow that contains the about dialog elements.

        Args:
            self: The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
            parent: Pointer to a parent window.
            top: creates an object
        Returns:
            None
        """
        super(ComDialog, self).__init__(parent, title=title, size=(300, 200))
        self.control_window = control_window
        self.firmware_window = firmware_window
        self.InitUI()
        self.SetSize((380, 140))
        self.SetTitle("COM Port Selection")
        self.SetBackgroundColour("White")

        self.dlist = []
        self.clist = []
        self.parent = parent

    def InitUI(self):
        panel = wx.Panel(self)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Label and ComboBox
        self.label_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # com_label = wx.StaticText(panel, label="Select COM Port:")
        self.search_button = wx.Button(panel, label="Search")
        self.com_combo = wx.ComboBox(panel, size=(100, -1))
        self.connect_button = wx.Button(panel, label="Connect")

        self.label_sizer.Add(self.search_button, flag=wx.ALL, border=10)
        self.label_sizer.Add(self.com_combo, flag=wx.ALL, border=10)
        self.label_sizer.Add(self.connect_button, flag=wx.ALL, border=10)
        self.main_sizer.Add(self.label_sizer, flag=wx.EXPAND)

        panel.SetSizer(self.main_sizer)

        # Bind the Search button to the OnSearch method
        self.Bind(wx.EVT_BUTTON, self.OnSearch, self.search_button)
        # Bind the Connect button to the OnConnect method
        self.Bind(wx.EVT_BUTTON, self.OnConnect, self.connect_button)

    def get_device(self):
        """
        Get the list of devices of model2450
        """
        self.devlist = searchmodel.get_models()
        print(self.devlist)
        if (wx.IsBusy()):
            wx.EndBusyCursor()
        self.dev_list = self.devlist["models"]
        if (len(self.dev_list) == 0):
            self.com_combo.Clear()
        else:
            self.key_list = []
            self.val_list = []
            for i in range(len(self.dev_list)):
                self.key_list.append(self.dev_list[i]["port"])
                self.val_list.append(self.dev_list[i]["model"])
            self.com_combo.Clear()

            for i in range(len(self.key_list)):
                str1 = self.val_list[i] + "(" + self.key_list[i] + ")"
                
                self.com_combo.Append([str1])

            if (len(self.key_list)):
                self.com_combo.Select(0)
                self.connect_button.Enable()

            else:
                self.connect_button.Disable()

    def OnSearch(self, e):
        """
        when click on search button, its started the search the model 2450 devices.
        """
        self.parent.log_message(f"\nSearching the COM...")
        self.get_device()

    def OnConnect(self, e):
        """
        Connect or Open the COM port for the Model 2450 device and fetch the serial number.
        
        Args:
            e: Event triggered when the Connect button is clicked.
        """
        self.selected = self.com_combo.GetValue()
        if self.selected:
            self.port = self.selected.split('(')[1].strip(')')
            if self.control_window.connect_to_model(self.port):
                self.firmware_window.connect_to_model(self.port)  # Also connect to firmware window
                self.firmware_window.set_model(self.control_window.model)  # Pass the model instance to firmware window
                
                # Fetch the serial number
                serial_number = self.control_window.model.read_sn().strip()
                print("serial_number:", serial_number)
                # self.UpdateAll([dialog.get_selected_port() + " "+ "Connected", "", ""])
                self.parent.UpdateAll([f"{self.port} Connected", f"{serial_number}", ""])
                             
                self.parent.log_message(f"\nSuccessfully Connected to {self.port}\n")
                self.EndModal(wx.ID_OK)  # Close the dialog with success
            else:
                self.parent.log_message(f"\nFailed to connect to {self.port}")
                self.EndModal(wx.ID_CANCEL)  # Close the dialog with failure
    
    def get_selected_port(self):
        return self.port  # Provide access to the selected COM port
    
   
    
