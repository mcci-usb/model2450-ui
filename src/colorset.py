
##############################################################################
# 
# Module: colorset.py
#
# Description:
#      set the color.
#
# Author:
#     Vinay N, MCCI Corporation May 2025
#
# Revision history:
#     V2.0.0 Mon May 2025 01:00:00   Vinay N 
#       Module created
##############################################################################
# colorset.py

import wx
# from model2450lib import model2450
# from model2450lib import model2450

from uiGlobal import * 
from pathlib import Path
import threading
# import logWindow

class ColorSet(wx.Frame):
    def __init__(self, parent, log_window, device=None):
        super(ColorSet, self).__init__(parent)
        self.device = device
        # self.log_window = log_window
        self.log_window = log_window
        base = os.path.abspath(os.path.dirname(__file__))
        self.SetIcon(wx.Icon(base+"/icons/"+IMG_ICON))
        self.Show()

        self.SetBackgroundColour("white")
        self.SetMinSize((440, 400))
        self.SetMaxSize((440, 400))
        self.panel = wx.Panel(self)

        self.top_vbox = wx.BoxSizer(wx.VERTICAL)
        self.image_set = "icons/Color.png"

        # Horizontal box for password with image
        self.hbox_pswd = wx.BoxSizer(wx.HORIZONTAL)
        self.st_pswd_img = wx.StaticBitmap(self.panel, bitmap=wx.Bitmap(self.image_set))
        self.hbox_pswd.Add(self.st_pswd_img, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.top_vbox.Add(self.hbox_pswd, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        # Horizontal box for buttons
        self.color_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_set_red = wx.Button(self.panel, -1, "Calibration Red", size=(-1, -1))
        self.btn_set_green = wx.Button(self.panel, -1, "Calibration Green", size=(-1, -1))
        self.btn_set_blue = wx.Button(self.panel, -1, "Calibration Blue", size=(-1, -1))
        self.color_btn_sizer.Add(self.btn_set_red, 1, wx.ALIGN_CENTER | wx.ALL, 20)
        self.color_btn_sizer.Add(self.btn_set_green, 1, wx.ALIGN_CENTER | wx.ALL, 13)
        self.color_btn_sizer.Add(self.btn_set_blue, 1, wx.ALIGN_CENTER | wx.ALL, 20)
        self.top_vbox.Add(self.color_btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.panel.SetSizer(self.top_vbox)
        self.Centre()
        self.Show()
        self.btn_set_red.Bind(wx.EVT_BUTTON, self.OnsetRed)
        self.btn_set_green.Bind(wx.EVT_BUTTON, self.OnsetGreen)
        self.btn_set_blue.Bind(wx.EVT_BUTTON, self.OnsetBlue)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
    
    def OnClose(self, event):
        print("close->")
        self.Destroy()

    def OnsetRed(self, e):
        print("Red --->")
        if self.device is None:
            wx.MessageBox("Please connect to a model first", "Error", wx.OK | wx.ICON_ERROR)
            return

        def task():
            try:
                # wx.CallAfter(self.log_window.log_message, f"\nSet Red")
                wx.CallAfter(self.log_window.log_message, "\nSet Red: used to set the calibration value for red")
                self.read = self.device.set_red()      
            except:
                pass

        threading.Thread(target=task).start()

    def OnsetGreen(self, e):
        if self.device is None:
            wx.MessageBox("Please connect to a model first", "Error", wx.OK | wx.ICON_ERROR)
            return

        def task():
            try:
                wx.CallAfter(self.log_window.log_message, "\nSet Green: used to set the calibration value for green")
                self.read = self.device.set_green()    
            except:
                pass

        threading.Thread(target=task).start()

    def OnsetBlue(self, e):
        if self.device is None:
            wx.MessageBox("Please connect to a model first", "Error", wx.OK | wx.ICON_ERROR)
            return

        def task():
            try:
                wx.CallAfter(self.log_window.log_message, "\nSet Blue: used to set the calibration value for blue")
                self.read = self.device.set_blue()    
            except:
                pass

        threading.Thread(target=task).start()
            
    def set_device(self, device):
        """Sets the device for the control panel."""
        self.device = device