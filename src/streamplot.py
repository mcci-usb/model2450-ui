import wx
import serial
import threading
import time
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector
from matplotlib.ticker import MaxNLocator
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
from matplotlib.ticker import FuncFormatter
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
from matplotlib.ticker import ScalarFormatter
from matplotlib.ticker import AutoMinorLocator
import xlsxwriter
import os
import numpy as np

from uiGlobal import *
# import mplcursors
import csv
import os

# === Packet Decoding ===
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

def format_seconds_millis(x, _):
    seconds = int(x)
    millis = int((x - seconds) * 1000)
    return f"{seconds}.{millis:03d}s"

class StreamPlotFrame(wx.Frame):
    def __init__(self, parent, device=None):
        super(StreamPlotFrame, self).__init__(parent)
        self.device = device
        self.keep_running = False
        self.SetSize((1000, 800))
        self.SetTitle("Stream Plot")
        self.SetIcon(wx.Icon(os.path.join(os.path.abspath(os.path.dirname(__file__)), "icons", IMG_ICON)))
    
        self.r_data = []
        self.g_data = []
        self.b_data = []
        self.light_data = []
        self.time_data_rgb = []
        self.time_data_light = []
        self.data_lock = threading.Lock()
        self.zoom_scale = 1.0
        self.start_time = time.time()
        
        self.zoom_fit_mode = False

        self.rgb_ylim = [0, 300]
        self.light_ylim = [0, 3000000]
        self.figure = Figure(figsize=(6, 6), facecolor='black')
        self.figure.subplots_adjust(hspace=0.6)  #
        self.ax_rgb = self.figure.add_subplot(211)
        # self.figure.subplots_adjust(hspace=0.4)  #
        self.ax_light = self.figure.add_subplot(212)
        self.canvas = FigureCanvas(self, -1, self.figure)
        # Add this block to make grid appear on first load 
        # Add minor locators
        self.ax_rgb.xaxis.set_minor_locator(AutoMinorLocator(2))
        self.ax_rgb.yaxis.set_minor_locator(AutoMinorLocator(2))
        
        self.ax_light.xaxis.set_major_locator(MultipleLocator(10))
        self.ax_light.xaxis.set_minor_locator(AutoMinorLocator(2))
        self.ax_light.yaxis.set_major_locator(MultipleLocator(500000))
        self.ax_light.yaxis.set_minor_locator(AutoMinorLocator(2))
        self.ax_light.grid(True, which='major', color='gray', linestyle='--', linewidth=0.5)
        self.ax_light.grid(True, which='minor', color='gray', linestyle=':', linewidth=0.3)
        
        self.ax_rgb.set_ylim(self.rgb_ylim)
        self.ax_light.set_ylim(self.light_ylim)
        self.ax_rgb.set_xlim(0, 10)
        self.ax_light.set_xlim(0, 10)

        for ax in [self.ax_rgb, self.ax_light]:
            ax.set_facecolor('black')
            ax.grid(True, color='gray', linestyle='--', linewidth=0.5)
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')

        self.canvas.draw()  # Initial draw to show grid and background
       
        self.span_rgb = SpanSelector(
            self.ax_rgb, self.on_rgb_range_select, 'horizontal',
            useblit=True, props=dict(alpha=0.3, facecolor='white'), interactive=True
        )

        self.span_light = SpanSelector(
            self.ax_light, self.on_light_range_select, 'horizontal',
            useblit=True, props=dict(alpha=0.3, facecolor='yellow'), interactive=True
        )

        self.red_cb = wx.CheckBox(self, label="Red")
        self.green_cb = wx.CheckBox(self, label="Green")
        self.blue_cb = wx.CheckBox(self, label="Blue")
        self.light_cb = wx.CheckBox(self, label="Light")
        for cb in (self.red_cb, self.green_cb, self.blue_cb, self.light_cb):
            cb.SetValue(True)
            cb.Bind(wx.EVT_CHECKBOX, self.on_checkbox_toggle)

        self.slider = wx.Slider(self, style=wx.SL_HORIZONTAL)
        self.start_btn = wx.Button(self, label="Start")
        self.stop_btn = wx.Button(self, label="Stop")
        self.zoom_in_btn = wx.Button(self, label="Zoom Out")
        self.zoom_out_btn = wx.Button(self, label="Zoom In")
        
        self.zoom_fit_btn = wx.Button(self, label="Zoom Fit")
        
        self.save_btn = wx.Button(self, label="Save File") 
        self.reset_btn = wx.Button(self, label="Reset")
        self.reset_btn.Bind(wx.EVT_BUTTON, self.on_reset)
        self.start_btn.Bind(wx.EVT_BUTTON, self.on_start)
        self.stop_btn.Bind(wx.EVT_BUTTON, self.on_stop)
        self.zoom_fit_btn.Bind(wx.EVT_BUTTON, self.on_zoom_fit)
        self.zoom_in_btn.Bind(wx.EVT_BUTTON, lambda evt: self.adjust_zoom(0.5))
        self.zoom_out_btn.Bind(wx.EVT_BUTTON, lambda evt: self.adjust_zoom(2.0))
        self.slider.Bind(wx.EVT_SLIDER, self.on_slider_scroll)
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save_csv)

        self.info_text = wx.StaticText(self, label=" RGB/Light data")
        self.info_text.SetForegroundColour(wx.Colour("white"))

        control_sizer = wx.BoxSizer(wx.HORIZONTAL)
        for item in [self.start_btn, self.stop_btn, self.zoom_in_btn, self.zoom_out_btn,self.zoom_fit_btn,
                     self.light_cb, self.red_cb, self.green_cb, self.blue_cb, self.reset_btn, self.save_btn]:
            control_sizer.Add(item, 0, wx.ALL, 5)
            # control_sizer.Add(self.zoom_fit_btn, 0, wx.ALL, 5)


        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.info_text, 0, wx.ALIGN_CENTER | wx.TOP, 5)
        main_sizer.Add(self.canvas, 1, wx.EXPAND)
        main_sizer.Add(self.slider, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(control_sizer, 0, wx.CENTER)
        self.axis_collapse = self.make_axis_collapse_panel()
        main_sizer.Add(self.axis_collapse, 0, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(main_sizer)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_plot, self.timer)
        self.canvas.mpl_connect("motion_notify_event", self.on_hover_motion)

    def on_rgb_hover(self, sel):
        x = sel.target[0]
        try:
            index = min(range(len(self.time_data_rgb)), key=lambda i: abs(self.time_data_rgb[i] - x))
            r = self.r_data[index]
            g = self.g_data[index]
            b = self.b_data[index]
            self.info_text.SetLabel(f"RGB → R: {r}, G: {g}, B: {b}")
        except Exception:
            self.info_text.SetLabel("RGB: No data")

    def on_light_hover(self, sel):
        x = sel.target[0]
        try:
            index = min(range(len(self.time_data_light)), key=lambda i: abs(self.time_data_light[i] - x))
            light = self.light_data[index]
            self.info_text.SetLabel(f"Light → {light}")
        except Exception:
            self.info_text.SetLabel("Light: No data")

    # Remaining methods unchanged (make_axis_row, make_axis_box, read_serial, update_plot, etc.)
    def make_axis_row(self, parent, label):
        row_sizer = wx.BoxSizer(wx.HORIZONTAL)

        row_sizer.Add(wx.StaticText(parent, label=f"{label} Y min:"), 0,
                    wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        y_min_ctrl = wx.TextCtrl(parent, name=f"{label.lower()}_ymin",
                                style=wx.TE_PROCESS_ENTER)
        y_min_ctrl.Bind(wx.EVT_CHAR, self.on_char_numeric_only)
        row_sizer.Add(y_min_ctrl, 0, wx.RIGHT, 10)

        row_sizer.Add(wx.StaticText(parent, label="Y max:"), 0,
                    wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        y_max_ctrl = wx.TextCtrl(parent, name=f"{label.lower()}_ymax",
                                style=wx.TE_PROCESS_ENTER)
        y_max_ctrl.Bind(wx.EVT_CHAR, self.on_char_numeric_only)
        row_sizer.Add(y_max_ctrl, 0, wx.RIGHT, 10)

        set_btn = wx.Button(parent, label=f"Set {label} Axis")
        set_btn.Bind(wx.EVT_BUTTON, self.on_axis_set)
        set_btn.SetName(label.lower())
        row_sizer.Add(set_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        return row_sizer
    
    def on_hover_motion(self, event):
        if event.inaxes == self.ax_rgb:
            try:
                with self.data_lock:
                    if not self.time_data_rgb:
                        return

                    # Reconstruct x_vals and filter exactly like in plot
                    if self.zoom_fit_mode:
                        x_vals = [t - self.time_data_rgb[0] for t in self.time_data_rgb]
                        x_vals = [x_vals[-1] - x for x in x_vals]
                        duration = max(x_vals)
                    else:
                        current_time = self.time_data_rgb[-1] if self.keep_running else self.time_data_rgb[min(self.slider.GetValue(), len(self.time_data_rgb)-1)]
                        x_vals = [current_time - t for t in self.time_data_rgb]
                        duration = 60 / self.zoom_scale

                    # Filter points within visible X range
                    filtered_indices = [i for i, x in enumerate(x_vals) if 0 <= x <= duration]
                    x_vals_filtered = [x_vals[i] for i in filtered_indices]
                    r_vals = [self.r_data[i] for i in filtered_indices]
                    g_vals = [self.g_data[i] for i in filtered_indices]
                    b_vals = [self.b_data[i] for i in filtered_indices]

                    # Remove zero-only RGB points (like in plot)
                    non_zero_indices = [i for i in range(len(r_vals)) if r_vals[i] > 0 or g_vals[i] > 0 or b_vals[i] > 0]
                    if not non_zero_indices:
                        return
                    x_vals_filtered = [x_vals_filtered[i] for i in non_zero_indices]
                    r_vals = [r_vals[i] for i in non_zero_indices]
                    g_vals = [g_vals[i] for i in non_zero_indices]
                    b_vals = [b_vals[i] for i in non_zero_indices]

                    x = event.xdata
                    if x is None or not x_vals_filtered:
                        return

                    index = min(range(len(x_vals_filtered)), key=lambda i: abs(x_vals_filtered[i] - x))
                    r = r_vals[index]
                    g = g_vals[index]
                    b = b_vals[index]
                self.info_text.SetLabel(f"RGB → R: {r}, G: {g}, B: {b}")
            except Exception:
                self.info_text.SetLabel("RGB: No data")

        elif event.inaxes == self.ax_light:
            try:
                with self.data_lock:
                    if not self.time_data_light:
                        return

                    if self.zoom_fit_mode:
                        x_vals = [t - self.time_data_light[0] for t in self.time_data_light]
                        x_vals = [x_vals[-1] - x for x in x_vals]
                    else:
                        current_time = self.time_data_light[-1] if self.keep_running else self.time_data_light[min(self.slider.GetValue(), len(self.time_data_light)-1)]
                        x_vals = [current_time - t for t in self.time_data_light]

                    x = event.xdata
                    if x is None or not x_vals:
                        return

                    index = min(range(len(x_vals)), key=lambda i: abs(x_vals[i] - x))
                    light = self.light_data[index]
                self.info_text.SetLabel(f"Light → {light}")
            except Exception:
                self.info_text.SetLabel("Light: No data")
        else:
            self.info_text.SetLabel("Hover over plot to see RGB/Light data")


    
    def make_axis_collapse_panel(self):
        # Create the collapsible pane
        collapse = wx.CollapsiblePane(self,
                                    label="Set Axis Limit >",
                                    style=wx.CP_DEFAULT_STYLE)
        # collapse.SetBackgroundColour(wx.BLACK)
        pane = collapse.GetPane()
        # pane.SetBackgroundColour(wx.BLACK)
        frame_w, _ = self.GetClientSize().Get()
        collapse.SetMinSize((frame_w - 20, -1))
        # When collapsed or expanded, re-layout everything so the outer frame stays the same size
        collapse.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_pane_changed)

        # Build the two rows inside the pane
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.make_axis_row(pane, "RGB"), 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(self.make_axis_row(pane, "Light"), 0, wx.ALL | wx.EXPAND, 5)
        pane.SetSizer(sizer)
        return collapse
    def on_pane_changed(self, event):
        # Keep the frame size locked, just rearrange children
        self.Layout()
        event.Skip()
    # ... rest of your methods unchanged (on_axis_set, on_start, on_stop, update_plot, etc.)
    def make_axis_box(self, label):
        box = wx.StaticBox(self, label=label + " Axis Limits")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        row_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # Y min
        row_sizer.Add(wx.StaticText(self, label="Y min:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        y_min_ctrl = wx.TextCtrl(self, name=f"{label.lower()}_ymin", style=wx.TE_PROCESS_ENTER)
        y_min_ctrl.Bind(wx.EVT_CHAR, self.on_char_numeric_only)
        row_sizer.Add(y_min_ctrl, 0, wx.RIGHT, 15)

        # Y max
        row_sizer.Add(wx.StaticText(self, label="Y max:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        y_max_ctrl = wx.TextCtrl(self, name=f"{label.lower()}_ymax", style=wx.TE_PROCESS_ENTER)
        y_max_ctrl.Bind(wx.EVT_CHAR, self.on_char_numeric_only)
        row_sizer.Add(y_max_ctrl, 0, wx.RIGHT, 15)
        # Set button
        set_btn = wx.Button(self, label=f"Set {label} Axis")
        set_btn.Bind(wx.EVT_BUTTON, self.on_axis_set)
        set_btn.SetName(label.lower())
        row_sizer.Add(set_btn, 0, wx.ALIGN_CENTER_VERTICAL)

        sizer.Add(row_sizer, 0, wx.ALL, 5)
        return sizer
    
    def on_char_numeric_only(self, event):
        keycode = event.GetKeyCode()
        if keycode < wx.WXK_SPACE or keycode == wx.WXK_DELETE or keycode > 255:
            event.Skip()
            return

        char = chr(keycode)
        allowed = "0123456789.-"
        ctrl = event.GetEventObject()
        value = ctrl.GetValue()
        if char == '.' and '.' in value:
            return
        if char == '-' and (len(value) > 0 or '-' in value):
            return
        if char in allowed:
            event.Skip()
            
    def on_axis_set(self, event):
        btn = event.GetEventObject()
        label = btn.GetName()  # 'rgb' or 'light'
        limits = {"ymin": None, "ymax": None}
        for key in limits:
            ctrl = self.FindWindowByName(f"{label}_{key}")
            if ctrl:
                try:
                    limits[key] = float(ctrl.GetValue())
                except ValueError:
                    pass

        if label == "rgb":
            # if limits["xmin"] is not None and limits["xmax"] is not None:
            #     self.ax_rgb.set_xlim(limits["xmin"], limits["xmax"])
            if limits["ymin"] is not None and limits["ymax"] is not None:
                self.rgb_ylim = [limits["ymin"], limits["ymax"]]
                self.ax_rgb.set_ylim(self.rgb_ylim)
        elif label == "light":
            # if limits["xmin"] is not None and limits["xmax"] is not None:
            #     self.ax_light.set_xlim(limits["xmin"], limits["xmax"])
            if limits["ymin"] is not None and limits["ymax"] is not None:
                self.light_ylim = [limits["ymin"], limits["ymax"]]
                self.ax_light.set_ylim(self.light_ylim)
        self.canvas.draw()

    def on_start(self, event):
        self.ser = self.device.ser
        self.ser.write(b"stream 3\r\n")

        if not self.keep_running:
            self.keep_running = True
            # Don't reset start_time to preserve continuity
            threading.Thread(target=self.read_serial, daemon=True).start()
            self.timer.Start(500)
    
    def on_reset(self, event):
        with self.data_lock:
            self.r_data.clear()
            self.g_data.clear()
            self.b_data.clear()
            self.light_data.clear()
            self.time_data_rgb.clear()
            self.time_data_light.clear()
        self.start_time = time.time()
        self.canvas.draw()
    
    def on_stop(self, event):
        self.keep_running = False
        if self.ser:
            self.ser.write(b"stream 0\r\n")
        self.timer.Stop()
        with self.data_lock:
            self.slider.SetMax(max(0, len(self.time_data_rgb) - 1))
            self.slider.SetValue(self.slider.GetMax())
    
    def adjust_zoom(self, factor):
        if self.keep_running:
            print("[Zoom] Ignored during streaming")
            return  # Do not zoom while streaming

        self.zoom_scale *= factor
        self.zoom_scale = max(0.1, self.zoom_scale)  # only lower limit
        # print(f"[Zoom] Scale: {self.zoom_scale:.2f}, Window: {60 / self.zoom_scale:.2f}s")
        self.update_plot(None)
     
    def on_zoom_fit(self, event):
        self.keep_running = False
        self.zoom_fit_mode = True
        with self.data_lock:
            # Use max length among RGB and Light to update slider
            max_len = max(len(self.time_data_rgb), len(self.time_data_light))
            if max_len > 0:
                self.slider.SetMax(max_len - 1)
                self.slider.SetValue(self.slider.GetMax())
        self.update_plot(None)



    def on_slider_scroll(self, event):
        self.update_plot(None)
        # if not self.keep_running:
        #     self.update_plot(None)

    def on_checkbox_toggle(self, event):
        if not self.keep_running:
            self.update_plot(None)
    def read_serial(self):
        buffer = b""
        while self.keep_running:
            packet = read_packet_from_serial(self.ser)
            if not packet:
                continue
            try:
                decoded = decode_packet(packet)
            except Exception as e:
                print(f"[Decode Error] {e}")
                continue

            payload = decoded["payload"]
            buffer += payload
            while b'\r\n' in buffer:
                line, buffer = buffer.split(b'\r\n', 1)
                full_line = line.decode("utf-8", errors="ignore").strip()
                r = g = b = light = 0
                if ':' in full_line:
                    parts = full_line.split(":")
                    if len(parts) == 3 and all(p.strip().isdigit() for p in parts):
                        r, g, b = map(int, parts)
                elif ',' in full_line:
                    parts = full_line.split(',')
                    if len(parts) == 4 and all(p.strip().isdigit() for p in parts):
                        r, g, b, light = map(int, parts)
                elif full_line.strip().isdigit():
                    light = int(full_line.strip())
                else:
                    continue
                ts = round(time.time() - self.start_time, 2)
                with self.data_lock:
                    self.r_data.append(r)
                    self.g_data.append(g)
                    self.b_data.append(b)
                    self.light_data.append(light)
                    self.time_data_rgb.append(ts)
                    self.time_data_light.append(ts)

                    maxlen = 1000000
                    for buf in [self.r_data, self.g_data, self.b_data, self.light_data,
                                self.time_data_rgb, self.time_data_light]:
                        if len(buf) > maxlen:
                            buf[:] = buf[-maxlen:]
    
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

        for ax in [self.ax_rgb, self.ax_light]:
            ax.set_facecolor('black')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')

        if self.zoom_fit_mode:
            # print("Zoom fit clicked:")
            # RGB Plot (Zoom Fit)
            if time_data_rgb:
                duration_rgb = time_data_rgb[-1] - time_data_rgb[0]
                duration_rgb = max(duration_rgb, 1.0)
                # print(f"RGB Duration: {duration_rgb}")
                self.ax_rgb.set_xlim(duration_rgb, 0)
                self.ax_rgb.xaxis.set_major_locator(MultipleLocator(10))
                self.ax_rgb.xaxis.set_minor_locator(AutoMinorLocator(2))

            else:
                duration_rgb = 60
                self.ax_rgb.set_xlim(duration_rgb, 0)
                self.ax_rgb.set_xticks([duration_rgb, 0])
                self.ax_rgb.set_xticklabels(["10", "0"])

            if time_data_light:
                duration_light = time_data_light[-1] - time_data_light[0]
                # print(f"Light Duration: {duration_light}")
                x_vals = [t - time_data_light[0] for t in time_data_light]
                x_vals = [duration_light - x for x in x_vals]

                self.ax_light.clear()
                self.ax_light.plot(x_vals, light_data, color='yellow')

                self.ax_light.set_xlim(duration_light, 0)
                self.ax_light.set_xticks([duration_light, 0])
                self.ax_light.set_xticklabels([f"{duration_light:.0f}", "0"])
                self.ax_light.set_autoscale_on(False)
                self.ax_light.set_ylim(bottom=0)

                self.ax_light.set_ylabel("Lux")
                self.ax_light.set_title("Light Intensity", color='white')
                self.ax_light.set_facecolor("black")

            else:
                duration_light = 60
                self.ax_light.set_xlim(duration_light, 0)
                self.ax_light.set_xticks([duration_light, 0])
                self.ax_light.set_xticklabels(["10", "0"])
        else:
            plot_window = 60 / self.zoom_scale
            current_time = time_data_rgb[-1] if (time_data_rgb and self.keep_running) else time_data_rgb[min(self.slider.GetValue(), len(time_data_rgb)-1)] if time_data_rgb else 0
            self.ax_rgb.set_xlim(plot_window, 0)
            self.ax_rgb.set_xticks([plot_window, 0])
            self.ax_rgb.set_xticklabels([str(int(plot_window)), "0"])

            current_time_l = time_data_light[-1] if (time_data_light and self.keep_running) else time_data_light[min(self.slider.GetValue(), len(time_data_light)-1)] if time_data_light else 0
            self.ax_light.set_xlim(plot_window, 0)
            self.ax_light.set_xticks([plot_window, 0])
            self.ax_light.set_xticklabels([str(int(plot_window)), "0"])

        if self.red_cb.GetValue() or self.green_cb.GetValue() or self.blue_cb.GetValue():
            if time_data_rgb:
                if self.zoom_fit_mode:
                    x_vals = [t - time_data_rgb[0] for t in time_data_rgb]
                    x_vals = [x_vals[-1] - x for x in x_vals]
                    duration = max(x_vals)
                else:
                    current_time = time_data_rgb[-1] if self.keep_running else time_data_rgb[min(self.slider.GetValue(), len(time_data_rgb)-1)]
                    x_vals = [current_time - t for t in time_data_rgb]
                    duration = plot_window

                filtered_indices = [i for i, x in enumerate(x_vals) if 0 <= x <= duration]
                x_vals_filtered = [x_vals[i] for i in filtered_indices]
                r_vals = [r_data[i] for i in filtered_indices]
                g_vals = [g_data[i] for i in filtered_indices]
                b_vals = [b_data[i] for i in filtered_indices]

                non_zero_indices = [i for i in range(len(r_vals)) if r_vals[i] > 0 or g_vals[i] > 0 or b_vals[i] > 0]
                x_vals_filtered = [x_vals_filtered[i] for i in non_zero_indices]
                r_vals = [r_vals[i] for i in non_zero_indices]
                g_vals = [g_vals[i] for i in non_zero_indices]
                b_vals = [b_vals[i] for i in non_zero_indices]
                
                # self.ax_rgb.plot(time_slice_rgb, b_slice, color='blue', label='Blue', linewidth=1.5, alpha=0.8)
                if self.red_cb.GetValue() and r_vals:
                    self.ax_rgb.plot(x_vals_filtered, r_vals, color='red', linewidth=1.2)
                if self.green_cb.GetValue() and g_vals:
                    self.ax_rgb.plot(x_vals_filtered, g_vals, color='green', linewidth=1.2)
                if self.blue_cb.GetValue() and b_vals:
                    self.ax_rgb.plot(x_vals_filtered, b_vals, color= 'blue', linewidth=1.2)

                self.ax_rgb.set_ylim(self.rgb_ylim)
                self.ax_rgb.set_title("Color Intensity", color='white')
                self.ax_rgb.set_ylabel("R : G : B", color='white')
                self.ax_rgb.set_xlabel("Time (s)", color='white')

                # Add locators to force both vertical and horizontal grid lines
                self.ax_rgb.xaxis.set_major_locator(MultipleLocator(10))      # vertical lines
                self.ax_rgb.xaxis.set_minor_locator(AutoMinorLocator(2))      # vertical minor
                self.ax_rgb.yaxis.set_minor_locator(AutoMinorLocator(2))      # horizontal minor

                # Grid lines: both major and minor
                self.ax_rgb.grid(True, which='major', axis='both', color='gray', linestyle='--', linewidth=0.7)
                self.ax_rgb.grid(True, which='minor', axis='both', color='gray', linestyle=':', linewidth=0.5)


        if self.light_cb.GetValue() and time_data_light:
            if self.zoom_fit_mode:
                duration_light = time_data_light[-1] - time_data_light[0]
                duration_light = max(duration_light, 1.0)
                x_vals_all = [t - time_data_light[0] for t in time_data_light]
                x_vals_all = [duration_light - x for x in x_vals_all]
                plot_duration = duration_light
            else:
                current_time = time_data_light[-1] if self.keep_running else time_data_light[min(self.slider.GetValue(), len(time_data_light)-1)]
                x_vals_all = [current_time - t for t in time_data_light]
                plot_duration = plot_window

            # y_vals_all = light_data
            # display_indices = [i for i, x in enumerate(x_vals_all) if 0 <= x <= plot_duration]

            # x_vals = np.array([x_vals_all[i] for i in display_indices])
            # y_vals = np.array([y_vals_all[i] for i in display_indices])
            
            y_vals_all = np.array(light_data, dtype=np.float32)
            y_vals_all[y_vals_all == 0] = np.nan  # Convert 0 to NaN

            display_indices = [i for i, x in enumerate(x_vals_all) if 0 <= x <= plot_duration]

            x_vals = np.array([x_vals_all[i] for i in display_indices])
            y_vals = np.array([y_vals_all[i] for i in display_indices])


            if len(x_vals) > 0:
                self.ax_light.plot(x_vals, y_vals, color='yellow', linewidth=0.5)
                self.ax_light.set_ylim(self.light_ylim)
                self.ax_light.yaxis.set_major_formatter(ScalarFormatter(useMathText=False))
                self.ax_light.ticklabel_format(style='plain', axis='y')
                self.ax_light.xaxis.set_major_locator(MultipleLocator(10))
                self.ax_light.xaxis.set_minor_locator(AutoMinorLocator(2))
                self.ax_light.yaxis.set_major_locator(MultipleLocator(500000))
                self.ax_light.yaxis.set_minor_locator(AutoMinorLocator(2))
                self.ax_light.grid(True, which='major', axis='both', color='gray', linestyle='--', linewidth=0.7)
                self.ax_light.grid(True, which='minor', axis='both', color='gray', linestyle=':', linewidth=0.5)

        self.ax_light.set_title("Light Intensity", color='white')
        self.ax_light.set_ylabel("Lux", color='white')
        self.ax_light.set_xlabel("Time (s)", color='white')
        self.canvas.draw()

        if not self.keep_running:
            self.zoom_fit_mode = False

    def filter_rgb_nonzero(x_vals, r_data, g_data, b_data, indices):
        return zip(*[
            (x_vals[i], r_data[i], g_data[i], b_data[i])
            for i in indices
            if r_data[i] != 0 or g_data[i] != 0 or b_data[i] != 0
        ]) if any(r_data[i] or g_data[i] or b_data[i] for i in indices) else ([], [], [], [])

    def on_rgb_range_select(self, xmin, xmax):
        # pass
        self.ax_rgb.set_xlim(xmin, xmax)
        self.canvas.draw()

    def on_light_range_select(self, xmin, xmax):
        # pass
        self.ax_light.set_xlim(xmin, xmax)
        self.canvas.draw()
    
    def on_save_csv(self, event):
        with self.data_lock:
            r_data = self.r_data[:]
            g_data = self.g_data[:]
            b_data = self.b_data[:]
            light_data = self.light_data[:]

        if not (r_data or g_data or b_data or light_data):
            wx.MessageBox("No data to save!", "Warning", wx.OK | wx.ICON_WARNING)
            return

        with wx.FileDialog(
            self,
            "Save Data",
            wildcard="CSV files (*.csv)|*.csv|Excel files (*.xlsx)|*.xlsx",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            path = fileDialog.GetPath()
            file_type = fileDialog.GetFilterIndex()  # 0 = CSV, 1 = XLSX

            try:
                if file_type == 0 or path.endswith(".csv"):
                    if not path.endswith(".csv"):
                        path += ".csv"
                    with open(path, 'w', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(['Light', 'R', 'G', 'B'])
                        for light, r, g, b in zip(light_data, r_data, g_data, b_data):
                            if r == 0 and g == 0 and b == 0 and light == 0:
                                writer.writerow([light, 'null', 'null', 'null'])
                            else:
                                writer.writerow([light, r, g, b])
                else:
                    if not path.endswith(".xlsx"):
                        path += ".xlsx"
                    workbook = xlsxwriter.Workbook(path)
                    worksheet = workbook.add_worksheet("Sensor Data")
                    headers = ['Light', 'R', 'G', 'B']
                    for col, header in enumerate(headers):
                        worksheet.write(0, col, header)
                    for row, (light, r, g, b) in enumerate(zip(light_data, r_data, g_data, b_data), start=1):
                        if r == 0 and g == 0 and b == 0:
                            worksheet.write(row, 0, light)
                            worksheet.write(row, 1, 'null')
                            worksheet.write(row, 2, 'null')
                            worksheet.write(row, 3, 'null')
                        else:
                            worksheet.write(row, 0, light)
                            worksheet.write(row, 1, r)
                            worksheet.write(row, 2, g)
                            worksheet.write(row, 3, b)
                    workbook.close()

                wx.MessageBox(f"Data saved to {os.path.basename(path)}", "Success", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f"Failed to save file:\n{e}", "Error", wx.OK | wx.ICON_ERROR)