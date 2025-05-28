##############################################################################
# 
# Module: streamplot.py
#
# Description:
#     plotting the stream 3\r\n data(both RGB and Light values).
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

#======================================================================
# COMPONENTS
#======================================================================

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
    payload = b""
    while len(payload) < remaining:
        more = ser.read(remaining - len(payload))
        if not more:
            return None
        payload += more
    return header + payload

class StreamPlotFrame(wx.Frame):
    """
    A wx.Frame subclass that streams and plots RGB and light sensor data from a connected device.

    This GUI interface is designed to:
    - Connect to a Model2450 device over serial.
    - Start and stop data streaming.
    - Plot RGB (Red, Green, Blue) and ambient light values in real time using matplotlib.
    - Support zooming and reviewing historical data via a slider after streaming stops.
    - Allow toggling visibility of each data channel (RGB/Light) via checkboxes.

    Attributes:
        device: The Model2450 device object (must expose a .ser Serial connection).
        start_time: Timestamp when the stream frame was initialized (used for time axis).
        keep_running: A boolean flag for controlling the serial reading thread.
        data_lock: A threading lock to protect access to shared data buffers.
        timer: A wx.Timer used to trigger periodic plot updates.
        serial_thread: Background thread for reading packets from the serial port.

    Note:
        This class expects a specific data format from the device, decoded with a custom protocol.
    """
    def __init__(self, parent, device=None):
        super(StreamPlotFrame, self).__init__(parent)
        self.SetIcon(wx.Icon(os.path.join(os.path.abspath(os.path.dirname(__file__)), "icons", IMG_ICON)))
        self.device = device
        self.start_time = time.time()


        self.SetTitle("RGB and Light Value Plot")
        self.SetSize((800, 700))
        panel = wx.Panel(self)

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
        
        self.slider = wx.Slider(panel, value=0, minValue=0, maxValue=1, style=wx.SL_HORIZONTAL | wx.SL_LABELS,size=(300, -1))
        

        cb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        for cb in [self.red_cb, self.green_cb, self.blue_cb, self.light_cb]:
            cb_sizer.Add(cb, 0, wx.ALL, 5)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        for btn in [self.start_btn, self.stop_btn, self.zoom_in_btn, self.zoom_out_btn, self.slider]:
            btn_sizer.Add(btn, 0, wx.ALL, 5)

        self.figure = Figure(facecolor='black')
        self.ax_rgb = self.figure.add_subplot(211)
        self.ax_light = self.figure.add_subplot(212)
        
        # Ensure initial background is black
        self.ax_rgb.set_facecolor('black')
        self.ax_light.set_facecolor('black')
        
        self.figure.subplots_adjust(hspace=0.5)
        self.canvas = FigureCanvas(panel, -1, self.figure)

        self.slider.Disable()  # Disabled initially
        self.slider.Bind(wx.EVT_SLIDER, self.on_slider_scroll)

        plot_sizer = wx.BoxSizer(wx.VERTICAL)
        plot_sizer.Add(cb_sizer, 0, wx.CENTER)
        plot_sizer.Add(self.canvas, 1, wx.EXPAND | wx.ALL, 5)
        plot_sizer.Add(btn_sizer, 0, wx.CENTER)
        # plot_sizer.Add(self.slider, 0, wx.EXPAND | wx.ALL, 5)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        # main_sizer.Add(serial_sizer, 0, wx.ALL, 5)
        main_sizer.Add(plot_sizer, 1, wx.EXPAND)
        panel.SetSizer(main_sizer)

        self.Bind(wx.EVT_BUTTON, self.start_stream, self.start_btn)
        self.Bind(wx.EVT_BUTTON, self.stop_stream, self.stop_btn)
        self.Bind(wx.EVT_BUTTON, self.zoom_in, self.zoom_in_btn)
        self.Bind(wx.EVT_BUTTON, self.zoom_out, self.zoom_out_btn)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_plot, self.timer)
        self.timer.Start(500)

        # Data lists and separate timestamps for RGB and Light
        self.r_data, self.g_data, self.b_data = [], [], []
        self.time_data_rgb = []
        self.light_data, self.time_data_light = [], []

        self.zoom_scale = 1.0
        self.ser = None
        self.keep_running = False
        self.serial_thread = None
        self.data_lock = threading.Lock()

    def start_stream(self, event):
        """
        Starts the data stream from the connected device.

        This method:
        - Sends a stream command to the device over serial to begin streaming data.
        - Spawns a background thread to continuously read and decode incoming packets.
        - Disables the timeline slider during active streaming to prevent manual scrolling.

        Args:
            event: The wxPython event that triggered this method (e.g., button press).

        Raises:
            Displays a message box on failure if the serial write or thread creation fails.
        """
        if not self.keep_running:
            if self.device:
                try:
                    self.ser = self.device.ser
                    self.ser.write(b"stream 3\r\n")
                    self.keep_running = True
                    self.slider.Disable()
                    self.serial_thread = threading.Thread(target=self.read_serial_data, daemon=True)
                    self.serial_thread.start()
                except Exception as e:
                    wx.MessageBox(f"Stream failed:\n{e}", "Error", wx.ICON_ERROR)
            else:
                print("Device is None")

    def stop_stream(self, event):
        """
        Stops the ongoing data stream from the device.

        This method:
        - Sends a command to the device to stop streaming.
        - Sets the `keep_running` flag to False to stop the reading thread.
        - Updates and enables the timeline slider for reviewing the collected data after streaming stops.

        Args:
            event: The wxPython event that triggered this method (e.g., button press).
        """
        self.keep_running = False
        if self.ser:
            self.ser.write(b"stream 0\r\n")
        with self.data_lock:
            length_rgb = len(self.time_data_rgb)
            length_light = len(self.time_data_light)
            length = max(length_rgb, length_light)
        if length:
            self.slider.SetMin(0)
            self.slider.SetMax(length - 1)
            # self.slider.SetValue(length - 1)
            self.slider.SetValue(0)
            self.slider.Enable()

    def scale_rgb_value(self, value):
        """
        Clamps an RGB value to the valid range [0, 255].

        Args:
            value (int): The raw RGB value.

        Returns:
            int: A value between 0 and 255 inclusive.
        """
        return max(0, min(255, value))

    def read_serial_data(self):
        """
        Continuously reads data packets from the serial device while streaming is active.

        Decodes each packet, extracts RGB or light values, and appends them to corresponding data lists.
        Uses a buffer to accumulate and split incoming serial data lines.
        """
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
                        decoded_str = full_line.decode("utf-8").strip()
                        if ':' in decoded_str:
                            parts = decoded_str.split(":")
                            if len(parts) >= 3:
                                r = self.scale_rgb_value(int(parts[0].strip()))
                                g = self.scale_rgb_value(int(parts[1].strip()))
                                b = self.scale_rgb_value(int(parts[2].strip()))
                                with self.data_lock:
                                    self.r_data.append(r)
                                    self.g_data.append(g)
                                    self.b_data.append(b)
                                    # self.time_data_rgb.append(time.time())
                                    self.time_data_rgb.append(time.time() - self.start_time)
                        else:
                            try:
                                light = int(decoded_str)
                                with self.data_lock:
                                    self.light_data.append(light)
                                    # self.time_data_light.append(time.time())
                                    self.time_data_light.append(time.time() - self.start_time)
                            except ValueError:
                                # Not a valid light integer, ignore
                                pass
            except Exception as e:
                print(f"Error reading serial: {e}")

    def update_plot(self, event):
        """
        Updates the RGB and Light plots with current data.

        Uses a lock to safely copy data for plotting. Handles live updates during streaming
        and uses the slider position for navigating through data after streaming has stopped.
        Applies zoom scaling to control how many data points are displayed.
        """
        with self.data_lock:
            r_data = self.r_data[:]
            g_data = self.g_data[:]
            b_data = self.b_data[:]
            time_data_rgb = self.time_data_rgb[:]

            light_data = self.light_data[:]
            time_data_light = self.time_data_light[:]

        if not time_data_rgb and not time_data_light:
            return

        self.ax_rgb.clear()
        self.ax_light.clear()
        for ax in [self.ax_rgb, self.ax_light]:
            ax.set_facecolor('black')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')

        # Determine how many points to show based on zoom
        n_rgb = int(100 * self.zoom_scale)
        n_light = int(100 * self.zoom_scale)

        total_points_rgb = len(time_data_rgb)
        total_points_light = len(time_data_light)

        if self.keep_running:
            start_index_rgb = max(0, total_points_rgb - n_rgb)
            start_index_light = max(0, total_points_light - n_light)
        else:
            slider_pos = self.slider.GetValue()
            start_index_rgb = max(0, min(slider_pos, max(0, total_points_rgb - n_rgb)))
            start_index_light = max(0, min(slider_pos, max(0, total_points_light - n_light)))
            start_index_rgb = slider_pos
            # start_index_light = slider_pos

        end_index_rgb = min(start_index_rgb + n_rgb, total_points_rgb)
        end_index_light = min(start_index_light + n_light, total_points_light)

        r_slice = r_data[start_index_rgb:end_index_rgb]
        g_slice = g_data[start_index_rgb:end_index_rgb]
        b_slice = b_data[start_index_rgb:end_index_rgb]
        time_slice_rgb = time_data_rgb[start_index_rgb:end_index_rgb]

        light_slice = light_data[start_index_light:end_index_light]
        time_slice_light = time_data_light[start_index_light:end_index_light]

        if self.red_cb.GetValue() and r_slice:
            self.ax_rgb.plot(time_slice_rgb, r_slice, color='red', label='Red')
        if self.green_cb.GetValue() and g_slice:
            self.ax_rgb.plot(time_slice_rgb, g_slice, color='green', label='Green')
        if self.blue_cb.GetValue() and b_slice:
            self.ax_rgb.plot(time_slice_rgb, b_slice, color='blue', label='Blue')
        # self.ax_rgb.set_title("R:G:B", color='white')
        # self.ax_rgb.legend()
        self.ax_rgb.set_title("R:G:B", color='white')
        if self.ax_rgb.lines:
            self.ax_rgb.legend()

        if self.light_cb.GetValue() and light_slice:
            self.ax_light.plot(time_slice_light, light_slice, color='yellow', label='Light')
            light_min = min(light_slice)
            light_max = max(light_slice)
            padding = (light_max - light_min) * 0.1
            self.ax_light.set_ylim(light_min - padding, light_max + padding)
            # self.ax_light.set_title("Light", color='white')
            # self.ax_light.legend()
            self.ax_light.set_title("Light", color='white')
            if self.ax_light.lines:
                self.ax_light.legend()

        self.canvas.draw()

    def on_slider_scroll(self, event):
        """
        Handles slider movement events.

        When streaming is stopped, allows users to scroll through and view recorded data
        by updating the plot based on the slider's position.
        """
        if not self.keep_running:
            self.update_plot(None)

    def zoom_in(self, event):
        """
        Zooms into the plot by decreasing the zoom scale.

        Limits the zoom level to a minimum of 0.5x to prevent excessive zooming in.
        """
        self.zoom_scale = max(0.5, self.zoom_scale * 0.8)

    def zoom_out(self, event):
        """
        Zooms out of the plot by increasing the zoom scale.

        Limits the zoom level to a maximum of 5.0x to prevent excessive zooming out.
        """
        self.zoom_scale = min(5.0, self.zoom_scale * 1.2)

    def OnClose(self, event):
        """
        Handles the window close event.

        Stops the data stream, closes the serial connection, waits for the
        serial thread to finish, and then destroys the frame.
        """
        self.keep_running = False
        if self.ser:
            try:
                self.ser.write(b"stream 0\r\n")
                self.ser.close()
            except:
                pass
        if self.serial_thread:
            self.serial_thread.join(timeout=2)
        self.Destroy()
    
    def set_device(self, device):
        """
        Assigns the specified device object to the panel.

        Parameters:
            device: A device object that provides access to a serial interface.
        """
        self.device = device