import wx
from model2450lib import model2450
import os
from uiGlobal import *
import json
import time

CONFIG_FILE = "config.json"  # Configuration file to store the light threshold value

class BlinkFrames(wx.Frame):
    def __init__(self, parent, title, log_window):
        super(BlinkFrames, self).__init__(parent, title=title, size=wx.Size(380, 180))
       
        self.start_time = None
        self.running = False

        self.log_window = log_window
        self.model = None  # To store the model connection object
        self.config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), CONFIG_FILE)
        self.config = self.load_config()  # Load the configuration
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        # Set the frame properties
        self.SetTitle("Blackframe Scan")
        self.SetIcon(wx.Icon(os.path.join(os.path.abspath(os.path.dirname(__file__)), "icons", IMG_ICON)))
        self.SetBackgroundColour("white")
        self.SetSize((380, 180))

        # Create a panel inside the frame
        self.panel = wx.Panel(self)
        self.top_vbox = wx.BoxSizer(wx.VERTICAL)

        # Horizontal box for blink frames controls
        self.hbox_blink_frames = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox_run = wx.BoxSizer(wx.HORIZONTAL)
        
        # Add "Connect" button
        self.st_lth = wx.StaticText(self.panel, label="Light Value Threshold", size=(-1, -1))
        self.tc_lth = wx.TextCtrl(self.panel, value="", size=(-1, -1), style=wx.TE_CENTRE |
                                     wx.TE_PROCESS_ENTER)  # Default value for testing
        self.btn_lth = wx.Button(self.panel, label="Update", size=(-1, -1))

        self.btn_run = wx.Button(self.panel, label="Run", size=(-1, -1))
        self.btn_stop = wx.Button(self.panel, label="Stop", size=(-1, -1))
        self.tc_time = wx.TextCtrl(self.panel, value="%H:%M:%S", size=(-1, -1), style=wx.TE_CENTRE |
                                     wx.TE_PROCESS_ENTER)

        # Add controls to the layout
        self.hbox_blink_frames.Add(self.st_lth, 1, wx.ALL, 10)
        self.hbox_blink_frames.Add(self.tc_lth, 1, wx.ALL, 10)
        self.hbox_blink_frames.Add(self.btn_lth, 1, wx.ALL, 10)

        self.hbox_run.Add(self.btn_run, 1, wx.ALL, 10)
        self.hbox_run.Add(self.btn_stop, 1, wx.ALL, 10)
        self.hbox_run.Add(self.tc_time, 1, wx.ALL, 10)

        self.top_vbox.Add(self.hbox_blink_frames, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        self.top_vbox.Add(self.hbox_run, 1, wx.ALIGN_CENTER | wx.ALL, 5)

        self.panel.SetSizer(self.top_vbox)
        self.Centre()
        self.Show()

        # Bind button events
        self.btn_lth.Bind(wx.EVT_BUTTON, self.on_update)
        self.btn_run.Bind(wx.EVT_BUTTON, self.on_start)
        self.btn_stop.Bind(wx.EVT_BUTTON, self.on_stop)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_time, self.timer)

        # Load the light threshold value from config
        self.load_light_threshold()
    
    def load_config(self):
        """Load the config.json file."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as file:
                try:
                    return json.load(file)
                except json.JSONDecodeError:
                    wx.MessageBox("Error reading config file.", "Error", wx.OK | wx.ICON_ERROR)
                    return {}
        else:
            return {}
    
    def load_light_threshold(self):
        """Load the light_threshold value into the TextCtrl."""
        light_threshold = self.config.get("light_threshold", "")
        self.tc_lth.SetValue(str(light_threshold))
    
    def save_config(self):
        """Saves the current configuration to a JSON file."""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def on_update(self, event):
        """Handles the 'Update' button click event."""
        if self.model is None:
            wx.MessageBox("Please connect to a model first", "Error", wx.OK | wx.ICON_ERROR)
            return
        try:
            # Get the value entered in the TextCtrl (light threshold)
            self.level_value = int(self.tc_lth.GetValue())
            # Call the model's set_level method with the entered value
            self.cr = self.model.set_level(self.level_value)
            # Log the response
            self.log_window(f"Level set to {self.level_value}\n")
            # Save value to config
            self.config['light_threshold'] = self.level_value
            self.save_config()
        except ValueError:
            wx.MessageBox("Please enter a valid integer for the level.", "Error", wx.OK | wx.ICON_ERROR)
        except Exception as ex:
            wx.MessageBox(f"Error setting level: {ex}", "Error", wx.OK | wx.ICON_ERROR)
            
    def on_start(self, e):
        if self.model is None:
            self.log_window("Please Connect Model2450:\n")
            return
        try:
            cr = self.model.set_run()
            self.log_window(f"\nBlinking started.\n")
            self.log_window(cr)
            self.start_timer()
        except Exception as ex:
            wx.MessageBox(f"Error starting blink: {ex}", "Error", wx.OK | wx.ICON_ERROR)
    
    def on_stop(self, e):
        if self.model is None:
            self.log_window("Please Connect Model2450:\n")
            return
        try:
            cr = self.model.set_stop()
            self.log_window(cr)
            self.log_window(f"\nBlinking stopped.\n")
            self.stop_timer()
        except Exception as ex:
            wx.MessageBox(f"Error stopping blink: {ex}", "Error", wx.OK | wx.ICON_ERROR)
        
    def connect_to_model(self, port):
        self.model = model2450.Model2450(port)
        return self.model.connect()
    
    def set_model(self, model):
        self.model = model
    
    def start_timer(self):
        """Start the timer and update the button label."""
        self.start_time = time.time()
        self.timer.Start(1000)  # Update every second
        self.btn_run.Disable()
        self.btn_stop.Enable()

    def stop_timer(self):
        """Stop the timer and update the button label."""
        self.timer.Stop()
        self.btn_run.Enable()
        self.btn_stop.Disable()
        # Display start and stop times
        stop_time = time.strftime('%H:%M:%S', time.localtime(time.time()))
        start_time = time.strftime('%H:%M:%S', time.localtime(self.start_time))
        self.log_window(f"\nStart Time: {start_time} and Stop Time: {stop_time}\n")
        

    def update_time(self, event):
        """Update the time display every second."""
        if self.start_time:
            current_time = time.strftime('%H:%M:%S', time.localtime())
            self.tc_time.SetValue(f"{current_time}")
