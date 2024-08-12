import wx
from uiGlobal import *
from model2450lib import searchswitch
from model2450lib.switch2450 import Switch2450
import time

dev_list = searchswitch.get_switches()
print(dev_list)

ID_BTN_READ_LIGHT = 1039
ID_BTN_READ_LEVEL = 1040

ID_TC_SET_LIGHT = 2020
ID_TC_SET_LEVEL = 2021

ID_TC_SET_READ = 3031
ID_BTN_READ_READ = 3032

ID_BTN_START = 4010
ID_BTN_PLOT = 4020
ID_BTN_STOP = 4030

class ControlWindow(wx.Panel):
    def __init__(self, parent, log_window):
        super(ControlWindow, self).__init__(parent)
        self.log_window = log_window

        self.SetBackgroundColour("White")
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.parent = parent
        
        # Light control
        self.light = wx.BoxSizer(wx.HORIZONTAL)
        self.st_light = wx.StaticText(self, label="Light:")
        self.tc_light = wx.TextCtrl(self, ID_TC_SET_LIGHT, "0000")
        self.btn_light = wx.Button(self, ID_BTN_READ_LIGHT, "Read Light")
        
        self.light.Add(self.st_light, flag=wx.ALL, border=10)
        self.light.Add((40, 0))  # Add a spacer of 40 pixels width
        self.light.Add(self.tc_light, flag=wx.ALL, border=10)
        self.light.Add(self.btn_light, flag=wx.ALL, border=10)
        self.main_sizer.Add(self.light, flag=wx.EXPAND)
        
        # READ COMMAND
        self.rd = wx.BoxSizer(wx.HORIZONTAL)
        self.st_read = wx.StaticText(self, label="Read:")
        self.tc_read = wx.TextCtrl(self, ID_TC_SET_READ, "00000")
        self.btn_read = wx.Button(self, ID_BTN_READ_READ, "Read Value")
        
        self.rd.Add(self.st_read, flag=wx.ALL, border=10)
        self.rd.Add((40, 0))  # Add a spacer of 40 pixels width
        self.rd.Add(self.tc_read, flag=wx.ALL, border=10)
        self.rd.Add(self.btn_read, flag=wx.ALL, border=10)

        self.main_sizer.Add(self.rd, flag=wx.EXPAND)
       
        # Color control 
        self.color = wx.BoxSizer(wx.HORIZONTAL)
        self.st_color = wx.StaticText(self, label="Color:")
        self.tc_color = wx.TextCtrl(self, ID_TC_SET_LEVEL, "R:G:B")
        self.btn_color = wx.Button(self, ID_BTN_READ_LEVEL, "Read Color")

        self.color.Add(self.st_color, flag=wx.ALL, border=10)
        self.color.Add((40, 0))  # Add a spacer of 40 pixels width
        self.color.Add(self.tc_color, flag=wx.ALL, border=10)
        self.color.Add(self.btn_color, flag=wx.ALL, border=10)

        self.main_sizer.Add(self.color, flag=wx.EXPAND)
        
        # Color control 
        self.settime = wx.BoxSizer(wx.HORIZONTAL)
        self.st_setint = wx.StaticText(self, label="Read Interval:")
        self.tc_setint = wx.TextCtrl(self, ID_TC_SET_LEVEL, "0000", size=(70, 25))
        self.st_ms = wx.StaticText(self, label="ms")
        self.btn_setint = wx.Button(self, ID_BTN_READ_LEVEL, "Set")
        self.settime.Add(self.st_setint, flag=wx.ALL, border=10)
        self.settime.Add(self.tc_setint, flag=wx.ALL, border=10)
        self.settime.Add(self.st_ms, flag=wx.ALL, border=10)
        self.settime.Add(self.btn_setint, flag=wx.ALL, border=10)

        self.main_sizer.Add(self.settime, flag=wx.EXPAND)
        
        self.start_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.start_btn = wx.Button(self, ID_BTN_START, "Start")
        self.plot_btn = wx.Button(self, ID_BTN_PLOT, "Plot")
        self.stop_btn = wx.Button(self, ID_BTN_STOP, "Stop")
        self.start_sizer.Add((60, 0))
        self.start_sizer.Add(self.start_btn, flag=wx.ALL, border=10)
        self.start_sizer.Add(self.plot_btn, flag=wx.ALL, border=10)
        self.start_sizer.Add(self.stop_btn, flag=wx.ALL, border=10)

        self.main_sizer.Add(self.start_sizer, flag=wx.EXPAND)

        self.SetSizer(self.main_sizer)
        self.btn_light.Bind(wx.EVT_BUTTON, self.read_light) 
        self.btn_read.Bind(wx.EVT_BUTTON, self.read_value)
        self.btn_color.Bind(wx.EVT_BUTTON, self.read_color)
        self.switch = None

    def read_light(self, e):
        if self.switch is None:
            # wx.MessageBox("Please connect to a switch first", "Error", wx.OK | wx.ICON_ERROR)
            pass
            return
        try:
            self.value = self.switch.level_read() #get_read color_read
            self.tc_light.SetValue(str(self.value))
            self.log_window.log_message(f"\nLight Value {self.value}")
        except Exception as ex:
            self.log_window.log_message(f"Error reading light: {ex}")
            print(ex)

    def read_value(self, e):
        if self.switch is None:
            # wx.MessageBox("Please connect to a switch first", "Error", wx.OK | wx.ICON_ERROR)
            pass
            return
        try:
            # time.sleep(1)
            self.value = self.switch.get_read() #get_read color_read
            
            self.tc_read.SetValue(str(self.value))
            self.log_window.log_message(f"Read Value {self.value}")
            print(self.value)
        except Exception as ex:
            self.log_window.log_message(f"Error reading value: {ex}")
            print(ex)
            
    def read_color(self, e):
        if self.switch is None:
            # wx.MessageBox("Please connect to a switch first", "Error", wx.OK | wx.ICON_ERROR)
            pass
            return

        try:
            self.value = self.switch.color_read() #get_read color_read
            self.tc_color.SetValue(str(self.value))
            self.log_window.log_message(f"Color Value  {self.value}")
            # print(self.value)
        except Exception as ex:
            self.log_window.log_message(f"Error reading value: {ex}")
            print(ex)
    
    #######################################################################
    def connect_to_switch(self, port):
        self.switch = Switch2450(port)
        if self.switch.connect():
            return True
        else:
            return False
