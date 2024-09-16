##############################################################################
# 
# Module: colorset.py
#
# Description:
#     set the color  {red, yellow and blue}
#
# Author:
#     Vinay N, MCCI Corporation Aug 2024
#
# Revision history:
#     V1.0.0 Mon Aug 12 2024 01:00:00   Vinay N 
#       Module created
##############################################################################
# colorset.py

import wx
# from model2450lib import model2450
from model2450lib import model2450

from uiGlobal import * 
from pathlib import Path
import logWindow

class ColorSet(wx.Frame):
    def __init__(self, parent,title, log_window):
        super(ColorSet, self).__init__(parent, title=title)
        # wx.Frame.__init__(self, parent, title="Set Color Window")
        
        base = os.path.abspath(os.path.dirname(__file__))
        self.SetIcon(wx.Icon(base+"/icons/"+IMG_ICON))
        self.Show()
        self.log_window = log_window
        # self.top = top
        self.model = None  # Initialize model variable
        print("model->", self.model)

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
        self.btn_set_red = wx.Button(self.panel, -1, "Calibrate Red", size=(-1, -1))
        self.btn_set_green = wx.Button(self.panel, -1, "Calibrate Green", size=(-1, -1))
        self.btn_set_blue = wx.Button(self.panel, -1, "Calibrate Blue", size=(-1, -1))
        self.color_btn_sizer.Add(self.btn_set_red, 1, wx.ALIGN_CENTER | wx.ALL, 20)
        self.color_btn_sizer.Add(self.btn_set_green, 1, wx.ALIGN_CENTER | wx.ALL, 20)
        self.color_btn_sizer.Add(self.btn_set_blue, 1, wx.ALIGN_CENTER | wx.ALL, 20)
        self.top_vbox.Add(self.color_btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.panel.SetSizer(self.top_vbox)
        self.Centre()
        self.Show()
        self.btn_set_red.Bind(wx.EVT_BUTTON, self.OnsetRed)
        self.btn_set_green.Bind(wx.EVT_BUTTON, self.OnsetGreen)
        self.btn_set_blue.Bind(wx.EVT_BUTTON, self.OnsetBlue)

    def OnsetRed(self, e):
        if self.model is None:
            wx.MessageBox("Please connect to a model first", "Error", wx.OK | wx.ICON_ERROR)
            return
        try:
            print("set red:")
            cr = self.model.set_red()
            self.log_window("set calibrite Red")
            # print("cr:", cr)
            self.log_window(cr)
        except Exception as ex:
            wx.MessageBox(f"Error setting red: {ex}", "Error", wx.OK | wx.ICON_ERROR)
            
    def OnsetGreen(self, e):
        if self.model is None:
            wx.MessageBox("Please connect to a model first", "Error", wx.OK | wx.ICON_ERROR)
            return
        try:
            print("set red:")
            cr = self.model.set_green()
            # print("cr:", cr)
            self.log_window(cr)
        except Exception as ex:
            wx.MessageBox(f"Error setting red: {ex}", "Error", wx.OK | wx.ICON_ERROR)
            
    def OnsetBlue(self, e):
        if self.model is None:
            wx.MessageBox("Please connect to a model first", "Error", wx.OK | wx.ICON_ERROR)
            return
        try:
            cr = self.model.set_blue()
            # print("cr:", cr)
            self.log_window(cr)
        except Exception as ex:
            wx.MessageBox(f"Error setting red: {ex}", "Error", wx.OK | wx.ICON_ERROR)
            
    def connect_to_model(self, port):
        self.model = model2450.Model2450(port)
        if self.model.connect():
            return True
        else:
            return False
    
    def set_model(self, model):
        self.model = model
        print("model set in ColorSet:", self.model)
