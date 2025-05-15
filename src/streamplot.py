##############################################################################
# 
# Module: streamplot.py
#
# Description:
#     Plotting the stream data.
#
# Author:
#     Vinay N, MCCI Corporation Aug 2024
#
# Revision history:
#     V1.0.0 Mon Aug 12 2024 01:00:00   Vinay N 
#       Module created

##############################################################################
import wx
import serial
import threading
from uiGlobal import *
import matplotlib
import time
from model2450lib import model2450
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

def decode_packet(packet_bytes):
    if len(packet_bytes) < 2:
        raise ValueError("Packet too short to decode header.")

    header_byte_0 = packet_bytes[0]
    header_byte_1 = packet_bytes[1]

    start_bit = (header_byte_0 >> 7) & 0x01
    end_bit = (header_byte_0 >> 6) & 0x01
    reserved = (header_byte_0 >> 5) & 0x01
    command = header_byte_0 & 0x1F

    sequence = (header_byte_1 >> 5) & 0x07
    length = header_byte_1 & 0x1F

    if len(packet_bytes) < length:
        raise ValueError(f"Packet length mismatch. Expected {length}, got {len(packet_bytes)}")

    payload = packet_bytes[2:length]

    return {
        "start_bit": start_bit,
        "end_bit": end_bit,
        "reserved": reserved,
        "command": command,
        "sequence": sequence,
        "length": length,
        "payload": payload
    }

def read_packet_from_serial(ser):
    header = ser.read(2)
    if len(header) < 2:
        return None

    length = header[1] & 0x1F
    remaining = length - 2

    # Read the remaining payload robustly
    payload = b""
    while len(payload) < remaining:
        more = ser.read(remaining - len(payload))
        if not more:
            return None
        payload += more

    return header + payload

class StreamPlotFrame(wx.Frame):
    def __init__(self, parent, device=None):
        super(StreamPlotFrame, self).__init__(parent)
        self.SetIcon(wx.Icon(os.path.join(os.path.abspath(os.path.dirname(__file__)), "icons", IMG_ICON)))
        self.device = device

        self.SetTitle("RGB and Light Value Plot")
        self.SetSize((800, 700))
        panel = wx.Panel(self)

        # Controls
        self.red_cb = wx.CheckBox(panel, label="Red")
        self.green_cb = wx.CheckBox(panel, label="Green")
        self.blue_cb = wx.CheckBox(panel, label="Blue")
        self.light_cb = wx.CheckBox(panel, label="Light")
        for cb in [self.red_cb, self.green_cb, self.blue_cb, self.light_cb]:
            cb.SetValue(True)

        self.start_btn = wx.Button(panel, label="Start Stream")
        self.stop_btn = wx.Button(panel, label="Stop Stream")
        self.zoom_in_btn = wx.Button(panel, label="Zoom In")
        self.zoom_out_btn = wx.Button(panel, label="Zoom Out")

        cb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        cb_sizer.Add(self.red_cb, 0, wx.ALL, 5)
        cb_sizer.Add(self.green_cb, 0, wx.ALL, 5)
        cb_sizer.Add(self.blue_cb, 0, wx.ALL, 5)
        cb_sizer.Add(self.light_cb, 0, wx.ALL, 5)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(self.start_btn, 0, wx.ALL, 5)
        btn_sizer.Add(self.stop_btn, 0, wx.ALL, 5)
        btn_sizer.Add(self.zoom_in_btn, 0, wx.ALL, 5)
        btn_sizer.Add(self.zoom_out_btn, 0, wx.ALL, 5)

        self.figure = Figure(facecolor='black')
        self.ax_rgb = self.figure.add_subplot(211)
        self.ax_light = self.figure.add_subplot(212)
        
        # Adjust the layout for more space between subplots
        self.figure.subplots_adjust(hspace=0.5)  # Adjust the vertical space between the plots

        self.canvas = FigureCanvas(panel, -1, self.figure)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(cb_sizer, 0, wx.CENTER)
        vbox.Add(self.canvas, 1, wx.EXPAND | wx.ALL, 5)
        vbox.Add(btn_sizer, 0, wx.CENTER)
        panel.SetSizer(vbox)

        self.r_data, self.g_data, self.b_data = [], [], []
        self.light_data, self.time_data = [], []
        self.zoom_scale = 1.0
        self.serial_thread = None
        self.keep_running = False

        self.Bind(wx.EVT_BUTTON, self.start_stream, self.start_btn)
        self.Bind(wx.EVT_BUTTON, self.stop_stream, self.stop_btn)
        self.Bind(wx.EVT_BUTTON, self.zoom_in, self.zoom_in_btn)
        self.Bind(wx.EVT_BUTTON, self.zoom_out, self.zoom_out_btn)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_plot, self.timer)
        self.timer.Start(500)
    
    def start_stream(self, event):
        # print("Start stream triggered")
        if not self.keep_running:
            # print("keep_running is False")
            if self.device:
                # print("Device exists")
                try:
                    self.ser = self.device.ser
                    self.ser.write(b"stream 3\r\n")
                    self.keep_running = True
                    self.serial_thread = threading.Thread(target=self.read_serial_data)
                    self.serial_thread.start()
                except Exception as e:
                    wx.MessageBox(f"Failed to start stream:\n{e}", "Error", wx.ICON_ERROR)
            else:
                print("Device is None")

    def stop_stream(self, event):
        if self.keep_running:
            self.keep_running = False
            self.ser.write(b"stream 0\r\n")
            # self.ser.close()

    # Normalize RGB values to a 0-255 range for better visualization (if needed)
    def scale_rgb_value(self, value):
        """Scale RGB values to the 0-255 range."""
        return max(0, min(255, value))  # Ensure values are clamped between 0 and 255

    # In the read_serial_data function, apply the scaling
    def read_serial_data(self):
        buffer = b""
        while self.keep_running:
            packet = read_packet_from_serial(self.ser)
            try:
                if packet:
                    decoded = decode_packet(packet)
                    payload = decoded["payload"]
                    buffer += payload
                    
                    while b'\r\n' in buffer:
                        line, buffer = buffer.split(b'\r\n', 1)
                        full_line = line + b'\r\n'
                        # print(f"Actual payload: {full_line}")
                        
                    try:
                        # Try decoding as RGB values
                        decoded_str = full_line.decode("utf-8").strip()

                        # Check if the payload matches the RGB pattern (e.g., '255 : 255 : 25')
                        if ':' in decoded_str:
                            parts = decoded_str.split(":")
                            if len(parts) >= 3:
                                r = int(parts[0].strip())
                                g = int(parts[1].strip())
                                b = int(parts[2].strip())

                                # Normalize to 0-255 range
                                r = self.scale_rgb_value(r)
                                g = self.scale_rgb_value(g)
                                b = self.scale_rgb_value(b)

                                # Append the RGB values
                                self.r_data.append(r)
                                self.g_data.append(g)
                                self.b_data.append(b)
                                self.time_data.append(time.time())
                        else:
                            # Otherwise, treat it as a light value (e.g., '5\r\n')
                            light_value = int(decoded_str)
                            self.light_data.append(light_value)
                            self.time_data.append(time.time())

                    except Exception as parse_err:
                        print(f"Error parsing payload: {parse_err}")
            except Exception as e:
                print(f"Error reading data: {e}")



    def update_plot(self, event):
        # Clear axes
        self.ax_rgb.clear()
        self.ax_light.clear()
        

        # Set background color to black
        for ax in [self.ax_rgb, self.ax_light]:
            ax.set_facecolor('black')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')

        # Apply zoom to the last 'n' data points
        n = int(100 * self.zoom_scale)
        time_data = self.time_data[-n:]
        r_data = self.r_data[-n:]
        g_data = self.g_data[-n:]
        b_data = self.b_data[-n:]

        min_len = min(len(time_data), len(r_data), len(g_data), len(b_data))
        if min_len == 0:
            self.canvas.draw()
            return

        # Truncate all lists to the minimum length
        time_data = time_data[-min_len:]
        r_data = r_data[-min_len:]
        g_data = g_data[-min_len:]
        b_data = b_data[-min_len:]
        
        # Plot RGB values if selected
        if self.red_cb.GetValue() or self.green_cb.GetValue() or self.blue_cb.GetValue():
            if self.red_cb.GetValue():
                self.ax_rgb.plot(time_data, r_data, color='red', label='Red', linewidth=1)
            if self.green_cb.GetValue():
                self.ax_rgb.plot(time_data, g_data, color='green', label='Green', linewidth=1)
            if self.blue_cb.GetValue():
                self.ax_rgb.plot(time_data, b_data, color='blue', label='Blue', linewidth=1)

        # Set the title for the RGB plot
        self.ax_rgb.set_title("R:G:B", color='white')
        self.ax_rgb.legend(loc='upper right')

        # Plot the light data if selected
        if self.light_cb.GetValue() and len(self.light_data) > 0:
            light_data = self.light_data[-min_len:]
            self.ax_light.plot(time_data, light_data, color='yellow', label="Light", linewidth=1)
            
            # Dynamically adjust y-axis range based on light data
            light_min = min(light_data)
            light_max = max(light_data)
            padding = (light_max - light_min) * 0.1  # 10% padding for better visualization
            self.ax_light.set_ylim(light_min - padding, light_max + padding)

            self.ax_light.set_title("Light", color='white')
            self.ax_light.legend(loc='upper right')

        # Draw the updated plot
        self.canvas.draw()

    def zoom_in(self, event):
        self.zoom_scale = max(0.5, self.zoom_scale * 0.8)

    def zoom_out(self, event):
        self.zoom_scale = min(5.0, self.zoom_scale * 1.2)

    def OnClose(self, event):
        self.keep_running = False
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.write(b"stream 0\r\n")
            self.ser.close()
        if self.serial_thread:
            self.serial_thread.join()
        self.Destroy()

    def set_device(self, device):
        """Sets the device for the control panel."""
        self.device = device
