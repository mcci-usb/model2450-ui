##############################################################################
#
# Module: colorset.py
#
# Description:
#     This module implements a wxPython-based GUI frame (ColorSet) that allows
#     users to configure and apply calibration values for Red, Green, and Blue
#     color channels on a connected MCCI Model2450 device.
#
# Author:
#     Vinay N, MCCI Corporation February 2026
#
# Revision history:
#     V2.2.0 Fri Feb 21 2026 20:02:00   Vinay N
#       Module created
#
##############################################################################
# Third-party imports
import wx

# Built-in imports
import os
import threading

# Local application imports
from uiGlobal import *

#======================================================================
# COMPONENTS
#======================================================================

class ColorSet(wx.Frame):
    """
    GUI frame for RGB calibration control.

    This wxPython frame provides an interface to trigger calibration
    routines for Red, Green, and Blue color channels on a connected
    Model2450 device.

    Features:
        • Displays calibration reference image.
        • Provides individual calibration buttons.
        • Executes calibration commands asynchronously.
        • Logs calibration activity to the log window.

    Args:
        parent (wx.Window):
            Parent window that owns this frame.

        log_window (LogWindow):
            Reference to application log window used
            for status and activity logging.

        device (Model2450, optional):
            Connected device instance used to send
            calibration commands.

    Threading:
        Calibration commands are executed in worker
        threads to prevent UI blocking.

    Notes:
        Device must be connected before calibration.
    """

    def __init__(self, parent, log_window, device=None):
        """
        Initialize the ColorSet frame UI and resources.

        This constructor sets up:

            • Frame properties (size, icon, background).
            • Calibration image display.
            • RGB calibration buttons.
            • Layout sizers.
            • Event bindings.

        Args:
            parent (wx.Window):
                Parent container window.

            log_window (LogWindow):
                Logging interface for status updates.

            device (Model2450, optional):
                Active device connection instance.

        Returns:
            None
        """
        super(ColorSet, self).__init__(parent)

        self.device = device
        self.log_window = log_window

        # Get current file directory
        base_path = os.path.dirname(os.path.abspath(__file__))

        # Set window icon
        icon_path = os.path.join(base_path, "icons", IMG_ICON)
        if os.path.exists(icon_path):
            self.SetIcon(wx.Icon(icon_path))

        self.SetBackgroundColour("white")
        self.SetMinSize((440, 400))
        self.SetMaxSize((440, 400))

        self.panel = wx.Panel(self)
        self.top_vbox = wx.BoxSizer(wx.VERTICAL)

        image_path = os.path.join(base_path, "icons", "Color.png")

        if os.path.exists(image_path):
            bitmap = wx.Bitmap(image_path, wx.BITMAP_TYPE_PNG)
            self.st_pswd_img = wx.StaticBitmap(self.panel, bitmap=bitmap)
            self.top_vbox.Add(self.st_pswd_img, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        else:
            print("Color.png not found at:", image_path)

        self.color_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_set_red = wx.Button(self.panel, -1, "Calibration Red")
        self.btn_set_green = wx.Button(self.panel, -1, "Calibration Green")
        self.btn_set_blue = wx.Button(self.panel, -1, "Calibration Blue")

        self.color_btn_sizer.Add(self.btn_set_red, 1, wx.ALL, 15)
        self.color_btn_sizer.Add(self.btn_set_green, 1, wx.ALL, 15)
        self.color_btn_sizer.Add(self.btn_set_blue, 1, wx.ALL, 15)

        self.top_vbox.Add(self.color_btn_sizer, 0, wx.ALIGN_CENTER)

        self.panel.SetSizer(self.top_vbox)

        self.Centre()
        self.Show()

        # Bind events
        self.btn_set_red.Bind(wx.EVT_BUTTON, self.OnsetRed)
        self.btn_set_green.Bind(wx.EVT_BUTTON, self.OnsetGreen)
        self.btn_set_blue.Bind(wx.EVT_BUTTON, self.OnsetBlue)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, event):
        """
        Handle frame close event.

        Destroys the ColorSet frame and releases UI resources.

        Args:
            event:
                wxPython close event object.

        Returns:
            None
        """
        self.Destroy()

    def OnsetRed(self, e):
        """
        Handle frame close event.

        Destroys the ColorSet frame and releases UI resources.

        Args:
            event:
                wxPython close event object.

        Returns:
            None
        """
        if self.device is None:
            wx.MessageBox("Please connect to a model first", "Error",
                          wx.OK | wx.ICON_ERROR)
            return

        def task():
            try:
                wx.CallAfter(self.log_window.log_message,
                             "\nSet Red: used to set the calibration value for red")
                self.device.set_red()
            except Exception as ex:
                print("Red Error:", ex)

        threading.Thread(target=task).start()

    def OnsetGreen(self, e):
        """
        Trigger Green color calibration.

        Sends a calibration command to the connected device
        to set the Green channel reference value.

        Functional Flow:
            • Validates device connection.
            • Logs calibration action.
            • Executes calibration in a background thread.

        Args:
            e:
                wxPython button click event.

        Returns:
            None
        """
        if self.device is None:
            wx.MessageBox("Please connect to a model first", "Error",
                          wx.OK | wx.ICON_ERROR)
            return

        def task():
            try:
                wx.CallAfter(self.log_window.log_message,
                             "\nSet Green: used to set the calibration value for green")
                self.device.set_green()
            except Exception as ex:
                print("Green Error:", ex)

        threading.Thread(target=task).start()

    def OnsetBlue(self, e):
        """
        Trigger Green color calibration.

        Sends a calibration command to the connected device
        to set the Green channel reference value.

        Functional Flow:
            • Validates device connection.
            • Logs calibration action.
            • Executes calibration in a background thread.

        Args:
            e:
                wxPython button click event.

        Returns:
            None
        """
        if self.device is None:
            wx.MessageBox("Please connect to a model first", "Error",
                          wx.OK | wx.ICON_ERROR)
            return

        def task():
            try:
                wx.CallAfter(self.log_window.log_message,
                             "\nSet Blue: used to set the calibration value for blue")
                self.device.set_blue()
            except Exception as ex:
                print("Blue Error:", ex)

        threading.Thread(target=task).start()

    # ==============================================================
    # Set Device
    # ==============================================================

    def set_device(self, device):
        """
        Assign connected device instance.

        Updates the frame with an active Model2450 device
        reference used for calibration commands.

        Args:
            device (Model2450):
                Connected device object.

        Returns:
            None

        Notes:
            Must be called after successful device connection.
        """
        self.device = device
