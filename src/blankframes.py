##############################################################################
# 
# Module: blankframes.py
#
# Description:
#     Count the number of blinking counts.
#
# Author:
#     Vinay N, MCCI Corporation Aug 2024
#
# Revision history:
#     V1.0.0 Mon Aug 12 2024 01:00:00   Vinay N 
#       Module created
##############################################################################
# import wx
import wx
from model2450lib import model2450

from uiGlobal import * 
from pathlib import Path
import logWindow

class BlinkFrames(wx.Frame):
    def __init__(self, parent, title, log_window):
        super(BlinkFrames, self).__init__(parent, title=title, size=wx.Size(380, 180))

        self.log_window = log_window
        # Set the frame properties
        self.SetTitle("Blink Frames")

        base = os.path.abspath(os.path.dirname(__file__))
        self.SetIcon(wx.Icon(base+"/icons/"+IMG_ICON))
        # self.Show()
        self.SetBackgroundColour("white")
        self.SetSize((380, 180))
        # Create a panel inside the frame
        self.panel = wx.Panel(self)
        self.top_vbox = wx.BoxSizer(wx.VERTICAL)
        # Horizontal box for blink frames controls
        self.hbox_blink_frames = wx.BoxSizer(wx.HORIZONTAL)
        self.st_blink = wx.StaticText(self.panel, label="Blink Frames", size=(-1, -1))
        self.tc_blink = wx.TextCtrl(self.panel, value=" ", size=(-1, -1))
        self.st_sec = wx.StaticText(self.panel, label="ms", size=(-1, -1))
        self.btn_start = wx.Button(self.panel, label="Run", size=(-1, -1))
        
        self.hbox_blink_frames.Add(self.st_blink, 1, wx.ALL, 10)
        self.hbox_blink_frames.Add(self.tc_blink, 1, wx.ALL, 10)
        self.hbox_blink_frames.Add(self.st_sec, 1, wx.ALL, 10)
        self.hbox_blink_frames.Add(self.btn_start, 1, wx.ALL, 10)
        self.top_vbox.Add(self.hbox_blink_frames, 1, wx.ALIGN_CENTER | wx.ALL, 5)

        self.panel.SetSizer(self.top_vbox)
        self.Centre()
        self.Show()

        # Adding tooltips
        self.tc_blink.SetToolTip(wx.ToolTip("1 second is 1000 milliseconds"))
        # self.btn_start.Bind(wx.EVT_BUTTON, self.startBlink)
        self.btn_start.Bind(wx.EVT_BUTTON, self.start_stop_blink)
        # Timer setup
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)
        # Track the button state
        self.is_blinking = False

    def start_stop_blink(self, event):
        if not self.is_blinking:
            # Start blinking
            self.startBlink()
            self.btn_start.SetLabel("Stop")
        else:
            # Stop blinking
            self.stopBlink()
            self.btn_start.SetLabel("Run")

        # Toggle the state
        self.is_blinking = not self.is_blinking
    
    def startBlink(self):
        try:
            interval = int(self.tc_blink.GetValue())
            if interval <= 0:
                raise ValueError("Interval must be positive.")
            
            self.timer.Start(interval)
            print(f"Timer started with interval: {interval} ms")
            self.log_window(f"\nBlinking started with {interval} ms interval.\n")

            if self.model is None:
                self.log_window("Please Connect Model2450:\n")
                return
            # Here you would typically call the device-specific start method
            cr = self.model.set_run()
            # self.log_window("Run Blink Frame:\n")
            self.log_window(cr)

        except ValueError as ex:
            wx.MessageBox(f"Invalid time interval: {ex}", "Error", wx.OK | wx.ICON_ERROR)
  
    def stopBlink(self):
        self.timer.Stop()
        # print("Timer stopped.")
        # self.log_window("Blinking stopped.\n")

        if self.model is None:
            wx.MessageBox("Please connect to a Model2450 first", "Error", wx.OK | wx.ICON_ERROR)
            return

        try:
            cr = self.model.set_stop()
            # self.log_window("Stop Blink Frame:\n")
            self.log_window(cr)
            self.log_window(f"\nBlinking stopped")
        except Exception as ex:
            wx.MessageBox(f"Error setting stop: {ex}", "Error", wx.OK | wx.ICON_ERROR)
    
    def on_timer(self, event):
        print("Timer event triggered, flipping the state.")
        self.start_stop_blink(None)  # Flip the state after the timer completes

    def connect_to_model(self, port):
        self.model = model2450.Model2450(port)
        if self.model.connect():
            return True
        else:
            return False

    def set_model(self, model):
        self.model = model
        # print("Mod set in BlinkFrames:", self.model)