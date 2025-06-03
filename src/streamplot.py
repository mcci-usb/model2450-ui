import wx
import serial
import threading
from uiGlobal import *
import matplotlib
import time
from model2450lib import model2450
import os

matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib import gridspec
import math
from matplotlib.ticker import AutoMinorLocator
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
    
    def __init__(self, parent, device=None):
        super(StreamPlotFrame, self).__init__(parent)
        self.SetIcon(wx.Icon(os.path.join(os.path.abspath(os.path.dirname(__file__)), "icons", IMG_ICON)))
        self.device = device
        self.start_time = time.time()

        self.SetTitle("RGB and Light Value Plot")
        self.SetSize((1200, 800))
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
        
        self.slider = wx.Slider(panel, value=0, minValue=0, maxValue=1, style=wx.SL_HORIZONTAL | wx.SL_LABELS, size=(300, -1))

        # Cursor position label to show mouse coordinates on plot
        self.cursor_text = wx.StaticText(panel, label="Cursor: ")
        # Set bold font
        font = self.cursor_text.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.cursor_text.SetFont(font)

        cb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        for cb in [self.red_cb, self.green_cb, self.blue_cb, self.light_cb]:
            cb_sizer.Add(cb, 0, wx.ALL, 5)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        for btn in [self.start_btn, self.stop_btn, self.zoom_in_btn, self.zoom_out_btn, self.slider]:
            btn_sizer.Add(btn, 0, wx.ALL, 5)

        # Add cursor_text label after buttons in btn_sizer
        btn_sizer.Add(self.cursor_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 20)

        self.figure = Figure(facecolor='black')
        
        gs = self.figure.add_gridspec(3, 1, height_ratios=[1, 0.2, 2])
        self.ax_rgb = self.figure.add_subplot(gs[0, 0])
        # gs[1, 0] is left empty as a gap
        self.ax_light = self.figure.add_subplot(gs[2, 0])
        self.figure.subplots_adjust(hspace=0)  # set hspace to 0 since height_ratios control spacing

        
        self.ax_rgb.set_facecolor('black')
        self.ax_light.set_facecolor('black')
        
        self.figure.subplots_adjust(hspace=0.3)
        self.canvas = FigureCanvas(panel, -1, self.figure)
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)

        self.slider.Disable()  # Disabled initially
        self.slider.Bind(wx.EVT_SLIDER, self.on_slider_scroll)

        plot_sizer = wx.BoxSizer(wx.VERTICAL)
        plot_sizer.Add(cb_sizer, 0, wx.CENTER)
        plot_sizer.Add(self.canvas, 1, wx.EXPAND | wx.ALL, 5)
        plot_sizer.Add(btn_sizer, 0, wx.CENTER)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
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
            self.slider.SetValue(0)
            self.slider.Enable()

    def scale_rgb_value(self, value):
        return max(0, min(255, value))
    
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
                                    self.time_data_rgb.append(time.time() - self.start_time)
                        else:
                            try:
                                light = int(decoded_str)
                                with self.data_lock:
                                    self.light_data.append(light)
                                    self.time_data_light.append(time.time() - self.start_time)
                            except ValueError:
                                pass
            except Exception as e:
                print(f"Error reading serial: {e}")

    def update_plot(self, event):
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
        
        # Set axis labels here
        self.ax_rgb.set_ylabel("R:G:B value", color='white')
        self.ax_rgb.set_xlabel("Time (s)", color='white')

        self.ax_light.set_ylabel("Light Value", color='white')
        self.ax_light.set_xlabel("Time (s)", color='white')
        
        for ax in [self.ax_rgb, self.ax_light]:
            ax.set_facecolor('black')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            # ax.grid(True, color='gray', linestyle='--', linewidth=0.5)  # <-- Add this line

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

        self.ax_rgb.set_title("R:G:B", color='white')
        if self.ax_rgb.lines:
            self.ax_rgb.legend()
        
        if self.light_cb.GetValue() and light_slice:
            self.ax_light.plot(time_slice_light, light_slice, color='yellow', label='Light')

            max_light = max(light_slice)

            base_ylim = 800000
            step = 200000

            if max_light > base_ylim:
                ylim_max = ((max_light // step) + 1) * step
            else:
                ylim_max = base_ylim

            self.ax_light.set_ylim(0, ylim_max)
            ticks = list(range(0, ylim_max + step, step))
            self.ax_light.set_yticks(ticks)

            from matplotlib.ticker import FuncFormatter
            def no_scientific(x, pos):
                return f"{int(x):,}"  # Adds commas, no scientific notation

            self.ax_light.yaxis.set_major_formatter(FuncFormatter(no_scientific))

            self.ax_light.set_title("Light", color='white')
            if self.ax_light.lines:
                self.ax_light.legend()

        self.canvas.draw()

    def on_slider_scroll(self, event):
        if not self.keep_running:
            self.update_plot(None)

    def zoom_in(self, event):
        self.zoom_scale = max(0.5, self.zoom_scale * 0.8)

    def zoom_out(self, event):
        self.zoom_scale = min(5.0, self.zoom_scale * 1.2)

    def OnClose(self, event):
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
    
    def on_mouse_move(self, event):
        if not event.inaxes or event.xdata is None:
            self.cursor_text.SetLabel("Cursor: ")
            return

        x = event.xdata

        with self.data_lock:
            if event.inaxes == self.ax_rgb:
                # Find nearest time index for RGB
                if self.time_data_rgb:
                    time_array = self.time_data_rgb
                    idx = min(range(len(time_array)), key=lambda i: abs(time_array[i] - x))
                    r = self.r_data[idx] if idx < len(self.r_data) else 0
                    g = self.g_data[idx] if idx < len(self.g_data) else 0
                    b = self.b_data[idx] if idx < len(self.b_data) else 0
                    self.cursor_text.SetLabel(f"Cursor: Time={x:.2f} | R={r}, G={g}, B={b}")
                else:
                    self.cursor_text.SetLabel("Cursor: No RGB data")

            elif event.inaxes == self.ax_light:
                # Find nearest time index for Light
                if self.time_data_light:
                    time_array = self.time_data_light
                    idx = min(range(len(time_array)), key=lambda i: abs(time_array[i] - x))
                    light = self.light_data[idx] if idx < len(self.light_data) else 0
                    self.cursor_text.SetLabel(f"Cursor: Time={x:.2f} | Light={light}")
                else:
                    self.cursor_text.SetLabel("Cursor: No Light data")
    