
##############################################################################
# 
# Module: comdialog.py
#
# Description:
#      Dialog to show list of available MCCI Model 2450
#     Search, view, select and connect module
#
# Author:
#     Vinay N, MCCI Corporation May 2025
#
# Revision history:
#     V2.0.0 Mon May 2025 01:00:00   Vinay N 
#       Module created
##############################################################################
import wx
import os
from model2450lib import searchmodel
from model2450lib.model2450 import Model2450
from uiGlobal import *

#======================================================================
# COMPONENTS
#======================================================================

class ComDialog(wx.Dialog):
    """
    A dialog for discovering and connecting to MCCI Model2450 devices.

    Allows the user to:
    - Search for available devices.
    - Select from a dropdown list.
    - Connect to the selected device.
    - Pass the connected device to parent control and firmware tabs.
    """
    def __init__(self, parent):
        """
        Initialize the dialog window with UI components.

        Args:
            parent (wx.Window): The parent frame or panel that opened this dialog.
        """
        super().__init__(parent, title="Connect Model2450", size=(350, 200))
        self.SetIcon(wx.Icon(os.path.join(os.path.abspath(os.path.dirname(__file__)), "icons", IMG_ICON)))

        self.device = None

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        search_btn = wx.Button(self, label="Search")
        self.port_text = wx.ComboBox(self)  # Changed from TextCtrl to ComboBox
        connect_btn = wx.Button(self, label="Connect")

        hbox.Add(search_btn, 0, wx.ALL | wx.CENTER, 5)
        hbox.Add(self.port_text, 1, wx.ALL | wx.CENTER, 5)
        hbox.Add(connect_btn, 0, wx.ALL | wx.CENTER, 5)

        self.result_text = wx.StaticText(self, label="Device not connected")

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(hbox, 0, wx.EXPAND)
        vbox.Add(self.result_text, 0, wx.ALL, 10)

        search_btn.Bind(wx.EVT_BUTTON, self.on_search)
        connect_btn.Bind(wx.EVT_BUTTON, self.on_connect)
        self.SetSizer(vbox)

    def on_search(self, event):
        """
        Event handler for the Search button.

        Uses `searchmodel.get_models()` to scan for available devices,
        then populates the ComboBox with results. Displays a message
        if no devices are found.
        """
        dev_list = searchmodel.get_models()  # Fetch devices using the searchmodel
        print(dev_list)
        if dev_list and "models" in dev_list:
            dev_list = dev_list["models"]
            self.port_text.Clear()  # Clear existing items in the ComboBox
            if len(dev_list) > 0:
                for dev in dev_list:
                    display_text = f"{dev['model']} ({dev['port']})"
                    self.port_text.Append(display_text)
                self.port_text.Select(0)  # Select the first port in the list
            else:
                self.result_text.SetLabel("No devices found")
        else:
            self.result_text.SetLabel("No devices found")

    def on_connect(self, event):
        """
        Event handler for the Connect button.

        Extracts the selected port from the ComboBox,
        attempts to establish a connection using the Model2450 class,
        updates the status, and passes the connected device to parent tabs.
        """
        selection = self.port_text.GetValue()
        if selection:
            # Extract the port from the selection, e.g., "2450 (COM6)" -> "COM6"
            try:
                port = selection.split('(')[1].strip(')')
            except IndexError:
                self.result_text.SetLabel("Invalid selection format.")
                return

            try:
                self.device = Model2450(port)
                self.device.connect()
                sn = self.device.read_sn()

                # Set the status bar text
                self.GetParent().SetStatusText(f"{sn}")

                # Pass the connected device to the ControlPanel
                self.GetParent().control_tab.set_device(self.device)
                # Pass the connected device to FirmwarePanel
                self.GetParent().firmware_tab.set_device(self.device)
                
                self.EndModal(wx.ID_OK)  # Close the dialog with success
                # Display a popup dialog confirming the connection
                wx.MessageBox(f"Device connected successfully.\nSerial Number: {sn}",
                            "Connection Successful", wx.OK | wx.ICON_INFORMATION)

                # Close the dialog after successful connection
                self.Close()
                self.EndModal(wx.ID_OK)  # Close the dialog with success
            except Exception as e:
                self.result_text.SetLabel(f"Connection failed: {str(e)}")
        else:
            self.result_text.SetLabel("Please select a device from the list.")