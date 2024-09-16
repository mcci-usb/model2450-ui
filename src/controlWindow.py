
##############################################################################
# 
# Module: controlWindow.py
#
# Description:
#     To read the Light and Color values and plotting.
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
from model2450lib import searchmodel
from model2450lib.model2450 import Model2450
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import numpy as np
import os

import threading

dev_list = searchmodel.get_models()


ID_BTN_READ_LIGHT = 1039
ID_BTN_READ_LEVEL = 1040

ID_TC_SET_LIGHT = 2020
ID_TC_SET_LEVEL = 2021

ID_TC_SET_READ = 3031
ID_BTN_READ_READ = 3032

ID_BTN_START = 4010
ID_BTN_PLOT = 4020
ID_BTN_STOP = 4030
ID_BTN_SET_INTERVAL = 4031

class PlotPanel(wx.Panel):
    def __init__(self, parent, rgb_data):
        wx.Panel.__init__(self, parent, size=wx.Size(380, 480))
        
        #  base = os.path.abspath(os.path.dirname(__file__))
        # self.SetIcon(wx.Icon(base+"/icons/"+IMG_ICON))
        
        self.rgb_data = rgb_data
        self.figure, self.ax = plt.subplots(dpi=80)
        # self.figure, self.ax = plt.subplots(figsize=(3, 2))  # Set figure size
        
        self.ax2 = self.ax.twinx()  # Create a second y-axis sharing the same x-axis
        self.canvas = FigureCanvas(self, -1, self.figure)
        

        # Set the size of the PlotPanel
        # self.SetSize((1000, 600))  # Example size: width=800, height=600
        
        self.SetBackgroundColour("white")
        self.SetSize((380, 480))
        
        # Checkboxes
        self.checkbox_red = wx.CheckBox(self, label="Red")
        self.checkbox_green = wx.CheckBox(self, label="Green")
        self.checkbox_blue = wx.CheckBox(self, label="Blue")
        self.checkbox_light = wx.CheckBox(self, label="Light")

        self.checkbox_red.SetValue(True)
        self.checkbox_green.SetValue(True)
        self.checkbox_blue.SetValue(True)

        self.Bind(wx.EVT_CHECKBOX, self.update_plot)

        # Zoom buttons
        self.zoom_in_btn = wx.Button(self, label="Zoom In")
        self.zoom_out_btn = wx.Button(self, label="Zoom Out")
        self.zoom_in_btn.Bind(wx.EVT_BUTTON, self.zoom_in)
        self.zoom_out_btn.Bind(wx.EVT_BUTTON, self.zoom_out)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.checkbox_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.zoom_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # sizer = wx.BoxSizer(wx.VERTICAL)
        self.checkbox_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.checkbox_sizer.Add(self.checkbox_red, 0, wx.ALL, 5)
        self.checkbox_sizer.Add(self.checkbox_green, 0, wx.ALL, 5)
        self.checkbox_sizer.Add(self.checkbox_blue, 0, wx.ALL, 5)
        self.checkbox_sizer.Add(self.checkbox_light, 0, wx.ALL, 5)

        self.zoom_sizer.Add(self.zoom_in_btn, 0, wx.ALL, 5)
        self.zoom_sizer.Add(self.zoom_out_btn, 0, wx.ALL, 5)

        self.sizer.Add(self.checkbox_sizer, 0, wx.CENTER)
        self.sizer.Add(self.canvas, 1, wx.EXPAND)

        self.sizer.Add(self.zoom_sizer, 0, wx.CENTER)

        self.SetSizer(self.sizer)
        self.update_plot(None)

    def update_plot(self, event):
        
        """update the plot for R:G:B and Light values.
        """
        self.ax.clear()   # Primary axis for RGB
        self.ax2.clear()  # Secondary axis for Light

        # Add grid and background color
        self.ax.grid(True, color='lightblue', linestyle='-', linewidth=1)
        
        self.ax.set_facecolor('black')
        # self.ax2.grid(True, color='lightblue', linestyle='-', linewidth=1)
        self.ax2.set_facecolor('black')

        # Set axis labels
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('RGB Value')
        self.ax2.set_ylabel('Light Value', color='orange')
        self.ax.set_title('RGB and Light Plot')
        
        self.r_values = self.rgb_data.get("R", [])
        self.g_values = self.rgb_data.get("G", [])
        self.b_values = self.rgb_data.get("B", [])
        self.light_values = self.rgb_data.get("Light", [])

        self.min_len_rgb = min(len(self.r_values), len(self.g_values), len(self.b_values))
        self.r_values = self.r_values[:self.min_len_rgb]
        self.g_values = self.g_values[:self.min_len_rgb]
        self.b_values = self.b_values[:self.min_len_rgb]

        self.time_points_rgb = np.arange(self.min_len_rgb)
        self.light_values = self.light_values[:self.min_len_rgb]

        if self.checkbox_red.GetValue():
            self.ax.plot(self.time_points_rgb, self.r_values, label='Red', color='red', marker='o')
        if self.checkbox_green.GetValue():
            self.ax.plot(self.time_points_rgb, self.g_values, label='Green', color='green', marker='o')
        if self.checkbox_blue.GetValue():
            self.ax.plot(self.time_points_rgb, self.b_values, label='Blue', color='blue', marker='o')
        if self.checkbox_light.GetValue():
            self.ax2.plot(self.time_points_rgb, self.light_values, label='Light', color='orange', marker='o')

        self.ax.legend()
        self.canvas.draw()

    def zoom_in(self, event):
        """
        Zoom in the plot by adjusting the x and y axis limits.
        
        This method scales the x-axis and y-axis limits by a factor,
        effectively zooming into the center of the plot. It multiplies
        the current lower limit of the axis by 1.1 (zooming out) and 
        the upper limit by 0.9 (zooming in), reducing the visible 
        range and providing a zoom-in effect.

        Args:
            event: The event that triggers this method (e.g., button click).

        """
        
        if self.ax:
            self.ax.set_xlim(self.ax.get_xlim()[0] * 1.1, self.ax.get_xlim()[1] * 0.9)
            self.ax.set_ylim(self.ax.get_ylim()[0] * 1.1, self.ax.get_ylim()[1] * 0.9)
            self.canvas.draw()

    def zoom_out(self, event):
        """
        Zoom Out the plot by adjusting the x and y axis limits.
        
        This method scales the x-axis and y-axis limits by a factor,
        effectively zooming into the center of the plot. It multiplies
        the current lower limit of the axis by 1.1 (zooming out) and 
        the upper limit by 0.9 (zooming in), reducing the visible 
        range and providing a zoom-in effect.

        Args:
            event: The event that triggers this method (e.g., button click).

        """
        if self.ax:
            self.ax.set_xlim(self.ax.get_xlim()[0] * 0.9, self.ax.get_xlim()[1] * 1.1)
            self.ax.set_ylim(self.ax.get_ylim()[0] * 0.9, self.ax.get_ylim()[1] * 1.1)
            self.canvas.draw()


class ControlWindow(wx.Panel):
    """
    A wxPython panel that serves as the control interface for the application.
    
    The ControlWindow class initializes the control panel within the parent window
    and links it to a log window for displaying logs or messages.

    Attributes:
        log_window (wx.TextCtrl or similar): A reference to the log window where
                                             logs or output messages will be displayed.
    """
    def __init__(self, parent, log_window):
        """
        Initializes the ControlWindow panel.

        Args:
            parent (wx.Window): The parent window or frame in which the control panel is placed.
            log_window (wx.TextCtrl or similar): A reference to the log window to display logs.
        """
        super(ControlWindow, self).__init__(parent)
        self.log_window = log_window

        self.SetBackgroundColour("White")
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.parent = parent

        self.period = 0
        self.timer = wx.Timer(self)  # Timer for repeated execution
        self.rgb_data = {"R": [], "G": [], "B": [], "Time": [], "Light": []}  # Buffer for RGB data

        # Light control
        self.light = wx.BoxSizer(wx.HORIZONTAL)
        self.st_light = wx.StaticText(self, label="Light")
        self.tc_light = wx.TextCtrl(self, ID_TC_SET_READ, "00000", size=(85, 25), style=wx.TE_CENTRE |
                                     wx.TE_PROCESS_ENTER)
        self.st_msr = wx.StaticText(self, label="lux")
        self.btn_light = wx.Button(self, ID_BTN_READ_READ, "Read Light")

        # Adding the widgets with adjustments to spacing and alignment
        self.light.Add(self.st_light, flag=wx.ALL, border=10)
        self.light.Add((60, 0))  # Reduced spacer to 10 pixels width
        self.light.Add(self.tc_light, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=5)  # Added vertical alignment and reduced border
        self.light.Add(self.st_msr, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=2)  # Added vertical alignment and reduced border
        self.light.Add(self.btn_light, flag=wx.ALL, border=10)

        self.main_sizer.Add(self.light, flag=wx.EXPAND)

        # Color control 
        self.color = wx.BoxSizer(wx.HORIZONTAL)
        self.st_color = wx.StaticText(self, label="Color (R:G:B)")
        self.tc_color = wx.TextCtrl(self, ID_TC_SET_LEVEL, "R:G:B", size=(85, 25), style=wx.TE_CENTRE |
                                     wx.TE_PROCESS_ENTER)
        self.btn_color = wx.Button(self, ID_BTN_READ_LEVEL, "Read Color")

        self.color.Add(self.st_color, flag=wx.ALL, border=10)
        self.color.Add((12, 0))  # Add a spacer of 40 pixels width
        self.color.Add(self.tc_color, flag=wx.ALL, border=10)
        self.color.Add((14, 0)) 
        self.color.Add(self.btn_color, flag=wx.ALL, border=10)

        self.main_sizer.Add(self.color, flag=wx.EXPAND)

        # Interval control
        self.settime = wx.BoxSizer(wx.HORIZONTAL)
        self.st_setint = wx.StaticText(self, label="Interval")
        self.tc_setint = wx.TextCtrl(self, ID_TC_SET_LEVEL, "2000", size=(85, 25), style=wx.TE_CENTRE |
                                     wx.TE_PROCESS_ENTER)
        self.st_ms = wx.StaticText(self, label="ms")
        
        self.settime.Add(self.st_setint, flag=wx.ALL, border=10)
        self.settime.Add((44, 0))  # Add a spacer of 40 pixels width
        
        self.settime.Add(self.tc_setint, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=5)  # Added vertical alignment and reduced border
        self.settime.Add(self.st_ms, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=2)  # Added vertical alignment and reduced border
        
        self.main_sizer.Add(self.settime, flag=wx.EXPAND)

        # Start, Plot, Stop buttons
        self.start_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.start_btn = wx.Button(self, ID_BTN_START, "Start", size=(70, 25))
        self.plot_btn = wx.Button(self, ID_BTN_PLOT, "Plot", size=(70, 25))
        self.stop_btn = wx.Button(self, ID_BTN_STOP, "Stop", size=(70, 25))
        self.start_sizer.Add((90, 0))
        self.start_sizer.Add(self.start_btn, flag=wx.ALL, border=10)
        self.start_sizer.Add(self.plot_btn, flag=wx.ALL, border=10)
        self.start_sizer.Add(self.stop_btn, flag=wx.ALL, border=10)

        self.main_sizer.Add(self.start_sizer, flag=wx.EXPAND)

        self.SetSizer(self.main_sizer)

        self.btn_light.Bind(wx.EVT_BUTTON, self.read_light)
        self.btn_color.Bind(wx.EVT_BUTTON, self.read_color)

        # self.start_btn.Bind(wx.EVT_BUTTON, self.start_timer) #on_start
        self.start_btn.Bind(wx.EVT_BUTTON, self.on_start) #on_start
        self.stop_btn.Bind(wx.EVT_BUTTON, self.on_stop) #on_start

        self.plot_btn.Bind(wx.EVT_BUTTON, self.plot_panel)
        # self.stop_btn.Bind(wx.EVT_BUTTON, self.stop_timer) #on_start
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)

        # Create threads
        thread1 = threading.Thread(target=self.start_timer())
        thread2 = threading.Thread(target=self.stop_timer())

        # Start threads
        thread1.start()
        thread2.start()

        # Wait for both threads to complete
        thread1.join()
        thread2.join()

        self.model = None
        self.plot_window = None

    def read_light(self, e):
        """updated the Light values.

        Args:
            e: event handler of light values.
        """
        if self.model is None:
            return
        try:
            self.value = self.model.get_read()
            self.rgb_data["Light"].append(int(self.value))
            self.tc_light.SetValue(str(self.value))
            self.log_window.log_message(f"Light   {self.value}")
        except Exception as ex:
            pass

    def read_color(self, e):
        """updated the color values.

        Args:
            e: event handler of colot values.
        """
        if self.model is None:
            return
        try:
            self.value = self.model.get_color()
            r, g, b = self.value.split(':')
            self.rgb_data["R"].append(int(r))
            self.rgb_data["G"].append(int(g))
            self.rgb_data["B"].append(int(b))
            self.rgb_data["Time"].append(time.time())
            self.tc_color.SetValue(str(self.value))
            self.log_window.log_message(f"Color {self.value}\n")
        except Exception as ex:
            pass

    def get_period(self):
        """
        Retrieves the time interval value from a text control.
        Defaults to 2000 milliseconds.

        Returns:
            int: The time interval in milliseconds.
        """
        tival = self.tc_setint.GetValue()
        if tival == "":
            tival = "2000"  # Default to 2000 ms if empty
        ival = int(tival)
        if ival < 1000:
            ival = 2000  # Minimum 2000 ms
            print("IVAL:", ival)
        return ival
    
    def on_start(self, e):
        """
        Handles the start event for the timer.

        Parameters:
            e: The event parameter (usually provided by wxPython event handling system).
        """
        self.start_timer()
        # self.log_window.log_message("Timer started\n")

    def start_timer(self):
        """
        Starts the timer with the period obtained from get_period.
        """
         # Time start
        period = self.get_period()
        self.timer.Start(period)
    
    def on_stop(self, e):
        """
        Handles the stop event for the timer.

        Parameters:
            e: The event parameter (usually provided by wxPython event handling system).
        """
        self.stop_timer()

    def stop_timer(self):
        """
        Stops the timer if it is currently running.
        """
        # stop timer
        self.timer.Stop()

    def on_timer(self, e):
        """
        Timer event handler. This method is called when the timer triggers.

        Parameters:
            e: The event parameter (usually provided by wxPython event handling system).
        """
        self.read_color(None)
        self.read_light(None)

    def plot_panel(self, e):
        """Show the window of Plot

        Args:
            e: event handler of the plot button.
        """
        # Destroy existing plot window if it exists
        if self.plot_window is not None:
            try:
                if self.plot_window.IsShown():
                    self.plot_window.Destroy()
            except RuntimeError:
                pass  # Ignore RuntimeError if the window has already been destroyed
            self.plot_window = None

        # Create a new plot window
        self.plot_window = wx.Frame(None, title="RGB and Light Value Plot", size=wx.Size(650, 580))
        
        # Divide R, G, B values by 100
        # self.rgb_data = {key: [val  for val in values] for key, values in self.rgb_data.items()}
        # print("R:G:B-DATA:", self.rgb_data)
        self.rgb_data = {key: [round(val / 10, 1) if key in ['R', 'G', 'B'] else val for val in values] for key, values in self.rgb_data.items()}
        # Send the updated data to the plot
        plot_panel = PlotPanel(self.plot_window, self.rgb_data)
        self.plot_window.Show()

    def set_model(self, model):
        self.model = model
        self.model.set_control_window(self)

    def connect_to_model(self, port):
        """Connect the Model2450 Back kit.

        Args:
            port: read the port number
        Returns:
           Connect to the model 2450
        """
        self.model = Model2450(port)
        if self.model.connect():
            return True
        else:
            return False
        