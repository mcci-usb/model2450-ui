
##############################################################################
# 
# Module: controlwindow.py
#
# Description:
#      To read the Light and Color values and plotting.
#
# Author:
#     Vinay N, MCCI Corporation May 2025
#
# Revision history:
#     V2.0.0 Mon May 2025 01:00:00   Vinay N 
#       Module created
##############################################################################
import wx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import numpy as np
import csv
import os
from wx import FileDialog, FD_SAVE, FD_OVERWRITE_PROMPT
from uiGlobal import *
from datetime import datetime
import xlsxwriter

#======================================================================
# COMPONENTS
#======================================================================

class PlotPanel(wx.Panel):
    """
    A wx.Panel subclass for plotting RGB and light sensor data using matplotlib.

    Features:
        - Real-time plotting of Red, Green, Blue, and Light values.
        - Checkbox controls to toggle visibility of each data series.
        - Zoom in/out functionality for better data inspection.

    Args:
        parent (wx.Window): The parent wxPython window or panel.
        rgb_data (dict): Dictionary containing lists of 'R', 'G', 'B', and 'Light' values.
    """
    def __init__(self, parent, rgb_data):
        wx.Panel.__init__(self, parent, size=wx.Size(400, 400))
        
        # Add icon to the plot window frame
        self.rgb_data = rgb_data
        self.figure, self.ax = plt.subplots(dpi=80)
        self.ax2 = self.ax.twinx()
        self.canvas = FigureCanvas(self, -1, self.figure)

        # Checkboxes
        self.checkbox_red = wx.CheckBox(self, label="Red")
        self.checkbox_green = wx.CheckBox(self, label="Green")
        self.checkbox_blue = wx.CheckBox(self, label="Blue")
        self.checkbox_light = wx.CheckBox(self, label="Light")

        self.checkbox_red.SetValue(True)
        self.checkbox_green.SetValue(True)
        self.checkbox_blue.SetValue(True)

        self.checkbox_red.Bind(wx.EVT_CHECKBOX, self.update_plot)
        self.checkbox_green.Bind(wx.EVT_CHECKBOX, self.update_plot)
        self.checkbox_blue.Bind(wx.EVT_CHECKBOX, self.update_plot)
        self.checkbox_light.Bind(wx.EVT_CHECKBOX, self.update_plot)

        # Zoom Buttons
        self.zoom_in_btn = wx.Button(self, label="Zoom In")
        self.zoom_out_btn = wx.Button(self, label="Zoom Out")

        self.zoom_in_btn.Bind(wx.EVT_BUTTON, self.on_zoom_in)
        self.zoom_out_btn.Bind(wx.EVT_BUTTON, self.on_zoom_out)

        # Layout
        layout = wx.BoxSizer(wx.VERTICAL)
        control_sizer = wx.BoxSizer(wx.HORIZONTAL)

        control_sizer.Add(self.checkbox_light, 0, wx.ALL, 5)
        control_sizer.Add(self.checkbox_red, 0, wx.ALL, 5)
        control_sizer.Add(self.checkbox_green, 0, wx.ALL, 5)
        control_sizer.Add(self.checkbox_blue, 0, wx.ALL, 5)
        
        control_sizer.Add(self.zoom_in_btn, 0, wx.ALL, 5)
        control_sizer.Add(self.zoom_out_btn, 0, wx.ALL, 5)

        layout.Add(control_sizer)
        layout.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(layout)

        self.update_plot(None)

    def update_plot(self, event):
        """
        Update the matplotlib plot based on current checkbox selections.

        Clears both axes and redraws the RGB and Light data.
        Each RGB channel (Red, Green, Blue) is plotted on the primary Y-axis.
        Light data is plotted on the secondary Y-axis (ax2) in orange.

        Args:
            event (wx.Event): The event object triggering the update. Can be None.
        """
        self.ax.clear()
        self.ax2.clear()
        self.ax.grid(True)
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('RGB Value')
        self.ax2.set_ylabel('Light Value', color='orange')
        self.ax.set_title('RGB and Light Plot')
        

        r = self.rgb_data.get("R", [])
        g = self.rgb_data.get("G", [])
        b = self.rgb_data.get("B", [])
        light = self.rgb_data.get("Light", [])

        min_len = min(len(r), len(g), len(b), len(light))
        times = np.arange(min_len)

        if self.checkbox_red.GetValue():
            self.ax.plot(times, r[:min_len], label='Red', color='red', marker='o')
        if self.checkbox_green.GetValue():
            self.ax.plot(times, g[:min_len], label='Green', color='green', marker='o')
        if self.checkbox_blue.GetValue():
            self.ax.plot(times, b[:min_len], label='Blue', color='blue', marker='o')
        if self.checkbox_light.GetValue():
            self.ax2.plot(times, light[:min_len], label='Light', color='orange', marker='x')

        self.ax.legend()
        self.canvas.draw()

    def on_zoom_in(self, event):
        """Zoom in by adjusting x and y axis limits."""
        self._zoom(factor=0.8)

    def on_zoom_out(self, event):
        """Zoom out by adjusting x and y axis limits."""
        self._zoom(factor=1.2)

    def _zoom(self, factor):
        """Zoom helper."""
        # Zoom on main axis
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2
        x_range = (xlim[1] - xlim[0]) * factor / 2
        y_range = (ylim[1] - ylim[0]) * factor / 2

        self.ax.set_xlim(x_center - x_range, x_center + x_range)
        self.ax.set_ylim(y_center - y_range, y_center + y_range)

        # Zoom on secondary axis
        ylim2 = self.ax2.get_ylim()
        y2_center = (ylim2[0] + ylim2[1]) / 2
        y2_range = (ylim2[1] - ylim2[0]) * factor / 2
        self.ax2.set_ylim(y2_center - y2_range, y2_center + y2_range)

        self.canvas.draw()

# import wx

class ControlPanel(wx.Panel):
    """
    A wx.Panel that allows control of a connected device to read light and color data,
    periodically acquire sensor readings, and plot or save the data.

    Includes buttons for manual reads, interval-based acquisition, and controls to display
    and save RGB and light sensor data.
    """
    def __init__(self, parent, log_window, device=None):
        """
        Initialize the ControlPanel.

        Args:
            parent (wx.Window): The parent window.
            log_window (LogWindow): An instance for logging messages.
            device (optional): An optional connected device instance to interact with.
        """
        super().__init__(parent)
        
        self.timestamps = []
        self.log_window = log_window
        self.device = device
        self.rgb_data = {"R": [], "G": [], "B": [], "Light": []}
        self.plot_window = None
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Light control
        self.light = wx.BoxSizer(wx.HORIZONTAL)
        self.st_light = wx.StaticText(self, label="Light")
        self.tc_light = wx.TextCtrl(self, value="00000", size=(85, 25), style=wx.TE_CENTER | wx.TE_READONLY)
        self.st_msr = wx.StaticText(self, label="lux")
        self.btn_light = wx.Button(self, label="Read Light")

        self.light.Add(self.st_light, flag=wx.ALL, border=10)
        self.light.Add((60, 0))
        self.light.Add(self.tc_light, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=5)
        self.light.Add(self.st_msr, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=2)
        self.light.Add(self.btn_light, flag=wx.ALL, border=10)
        self.main_sizer.Add(self.light, flag=wx.EXPAND)

        # Color control
        self.color = wx.BoxSizer(wx.HORIZONTAL)
        self.st_color = wx.StaticText(self, label="Color (R:G:B)")
        self.tc_color = wx.TextCtrl(self, value="R:G:B", size=(85, 25), style=wx.TE_CENTER | wx.TE_READONLY)
        self.btn_color = wx.Button(self, label="Read Color")

        self.color.Add(self.st_color, flag=wx.ALL, border=10)
        self.color.Add((12, 0))
        self.color.Add(self.tc_color, flag=wx.ALL, border=10)
        self.color.Add((14, 0))
        self.color.Add(self.btn_color, flag=wx.ALL, border=10)
        self.main_sizer.Add(self.color, flag=wx.EXPAND)

        # Interval control
        self.settime = wx.BoxSizer(wx.HORIZONTAL)
        self.st_setint = wx.StaticText(self, label="Interval")
        self.tc_setint = wx.TextCtrl(self, value="2000", size=(85, 25), style=wx.TE_CENTER | wx.TE_PROCESS_ENTER)
        self.tc_setint.Bind(wx.EVT_CHAR, self.on_only_digits)
        self.st_ms = wx.StaticText(self, label="ms")

        self.settime.Add(self.st_setint, flag=wx.ALL, border=10)
        self.settime.Add((44, 0))
        self.settime.Add(self.tc_setint, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=5)
        self.settime.Add(self.st_ms, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=2)
        self.main_sizer.Add(self.settime, flag=wx.EXPAND)

        # Buttons
        self.start_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.start_btn = wx.Button(self, label="Start", size=(70, 25))
        self.stop_btn = wx.Button(self, label="Stop", size=(70, 25))
        
        


        self.start_sizer.Add((90, 0))
        self.start_sizer.AddSpacer(8)  # This will add the 20px gap
        self.start_sizer.Add(self.start_btn, flag=wx.ALL, border=10)
        # self.start_sizer.Add(self.plot_btn, flag=wx.ALL, border=10)
        self.start_sizer.Add(self.stop_btn, flag=wx.ALL, border=10)
        # self.start_sizer.Add(self.save_csv_btn, flag=wx.ALL, border=10)
        self.main_sizer.Add(self.start_sizer, flag=wx.EXPAND)
        
        self.plot_csv = wx.BoxSizer(wx.HORIZONTAL)
        self.plot_btn = wx.Button(self, label="Plot", size=(70, 25))
        self.save_csv_btn = wx.Button(self, label="Save File", size=(80, 25))
        self.plot_csv.Add((100, 0))
        self.plot_csv.Add(self.plot_btn, flag=wx.ALL, border=10)
        self.plot_csv.Add(self.save_csv_btn, flag=wx.ALL, border=10)
        self.main_sizer.Add(self.plot_csv, flag=wx.EXPAND)
        
        

        self.SetSizer(self.main_sizer)

        # Bind events
        self.btn_light.Bind(wx.EVT_BUTTON, self.on_light_read)
        self.btn_color.Bind(wx.EVT_BUTTON, self.on_color_read)
        self.start_btn.Bind(wx.EVT_BUTTON, self.on_start)
        self.stop_btn.Bind(wx.EVT_BUTTON, self.on_stop)
        self.plot_btn.Bind(wx.EVT_BUTTON, self.on_plot) 
        self.save_csv_btn.Bind(wx.EVT_BUTTON, self.on_save_csv)


    def set_device(self, device):
        """
        Set the device instance for the control panel.

        Args:
            device: An object representing the connected device.
        """
        self.device = device
    
    def on_only_digits(self, event):
        keycode = event.GetKeyCode()
        if keycode < wx.WXK_SPACE or keycode == wx.WXK_DELETE or keycode > 255:
            event.Skip()
            return
        char = chr(keycode)
        if char.isdigit():
            event.Skip()  # Allow digit
        # Optional: allow backspace
        elif keycode == wx.WXK_BACK:
            event.Skip()
        else:
            return  # Ignore non-digit key
    
    def on_light_read(self, event):
        """
        Handle the "Read Light" button press.

        Reads ambient light from the device and updates the light text control.
        Logs the result or any errors.
        """
        if self.device:
            try:
                # Check if serial port is open
                if not self.device.ser or not self.device.ser.is_open:
                    self.device.connect()  # or reconnect method

                    return

                light = self.device.get_read()
                self.tc_light.SetValue(str(light))
                self.log_window.log_message(f"Light (lux) -  {light}")

            except Exception as e:
                self.tc_light.SetValue("Read error")
                self.log_window.log_message(f"Error reading light sensor: {e}\n")
        else:
            wx.MessageBox(
                "No device is connected. Please connect a Model2450 device first.",
                "Device Not Connected",
                wx.OK | wx.ICON_WARNING
            )

    def on_color_read(self, event):
        """
        Handle the "Read Color" button press.

        Reads the RGB color data from the device and displays it.
        Logs the result or any errors.
        """
        if self.device:
            try:
                color = self.device.get_color()
                self.tc_color.SetValue(str(color))
                self.log_window.log_message(f"Color (R:G:B) - {color}")
            except Exception as e:
                self.tc_color.SetValue(f"Error: {str(e)}")
        else:
            wx.MessageBox(
                "No device is connected. Please connect a Model2450 device first.",
                "Device Not Connected",
                wx.OK | wx.ICON_WARNING
            )

    def on_start(self, event):
        """
        Start periodic reading using a wx.Timer.

        Uses the interval specified in the interval text control.
        """
        if self.device:
            try:
                interval_ms = int(self.tc_setint.GetValue())
                self.timer.Start(interval_ms)
                # self.log_window.log_message("\nStarted reading data periodically.")
                self.log_window.log_message(f"\nAmbient Light (lux) and Color (R:G:B) data read {interval_ms} ms.")
            except Exception as e:
                self.tc_color.SetValue(f"Error: {str(e)}")
        else:
            self.log_window.log_message(f"Device is not Connected!")

    def on_stop(self, event):
        """
        Stop the periodic reading if it is currently running.
        """
        if self.timer.IsRunning():
            self.timer.Stop()
            self.log_window.log_message("\nStopped reading data.")

    def on_timer(self, event):
        """
        Timer callback for periodic reading.

        Reads light and RGB color data from the device and appends it to the internal dataset.
        Updates display fields and logs the reading.
        """
        if self.device:
            try:
                light = self.device.get_read()
                color = self.device.get_color()

                r, g, b = map(int, color.split(":"))

                self.rgb_data["Light"].append(int(light))
                self.rgb_data["R"].append(r)
                self.rgb_data["G"].append(g)
                self.rgb_data["B"].append(b)
                
                # self.timestamps.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # accurate to milliseconds
                self.timestamps.append(timestamp)

                self.tc_light.SetValue(str(light))
                self.tc_color.SetValue(color)

                # self.log_window.log_message(f"\nTimer read: Light={light}, Color={color}")
                self.log_window.log_message(f"Ambient Light (lux) - {light} ,   Color (R:G:B) - {color}")

            except Exception as e:
                self.log_window.log_message(f"\nError during timer read: {str(e)}")

    def on_plot(self, event):
        """
        Open a plot window to visualize the collected RGB and light sensor data.

        Creates a new PlotPanel in a separate frame if not already visible.
        """
        if self.plot_window is None or not self.plot_window.IsShown():
            self.plot_window = wx.Frame(self, title="RGB and Light Plot", size=(600, 500))
            
            icon_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "icons", IMG_ICON)
            self.plot_window.SetIcon(wx.Icon(icon_path))
            panel = PlotPanel(self.plot_window, self.rgb_data)
            self.plot_window.Show()
    
    def on_save_csv(self, event):
        """
        Ask the user to choose file format (.xlsx or .csv) and save RGB/Light data.
        Excel: writes data in one sheet, and shows charts only in second sheet.
        """
        # import xlsxwriter

        # Ask user for file format
        format_dialog = wx.SingleChoiceDialog(
            self,
            "Choose a file format to save:",
            "Save As",
            ["XLSX (Excel)", "CSV"]
        )

        if format_dialog.ShowModal() != wx.ID_OK:
            return  # User cancelled

        file_type = format_dialog.GetStringSelection()
        wildcard = "Excel files (*.xlsx)|*.xlsx" if "XLSX" in file_type else "CSV files (*.csv)|*.csv"

        with FileDialog(self, "Save File", wildcard=wildcard,
                        style=FD_SAVE | FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # User cancelled

            path = fileDialog.GetPath()
            r = self.rgb_data.get("R", [])
            g = self.rgb_data.get("G", [])
            b = self.rgb_data.get("B", [])
            light = self.rgb_data.get("Light", [])
            timestamps = getattr(self, "timestamps", [])

            min_len = min(len(r), len(g), len(b), len(light), len(timestamps))

            try:
                if "XLSX" in file_type:
                    if not path.endswith(".xlsx"):
                        path += ".xlsx"
                    workbook = xlsxwriter.Workbook(path)

                    # Sheet 1: RGB and Light Data
                    sheet_data = workbook.add_worksheet("RGB and Light Data")
                    # Sheet 2: Charts Only
                    sheet_plot = workbook.add_worksheet("Plotting")

                    header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
                    center_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})

                    headers = ['Index', 'Timestamp', 'Light', 'Red', 'Green', 'Blue']
                    for col, header in enumerate(headers):
                        sheet_data.write(0, col, header, header_format)

                    for i in range(min_len):
                        row = [i, timestamps[i], light[i], r[i], g[i], b[i]]
                        for col, value in enumerate(row):
                            sheet_data.write(i + 1, col, value, center_format)

                    # Column widths
                    sheet_data.set_column('A:A', 8)
                    sheet_data.set_column('B:B', 23)
                    sheet_data.set_column('C:F', 10)

                    # ---------------------- Charts ----------------------

                    # Light Chart (only from Sheet 1)
                    light_chart = workbook.add_chart({'type': 'line'})
                    light_chart.add_series({
                        'name': 'Light',
                        'categories': ['RGB and Light Data', 1, 0, min_len, 0],  # Index
                        'values':     ['RGB and Light Data', 1, 2, min_len, 2],  # Light
                        'line': {'color': 'orange'}
                    })
                    light_chart.set_title({'name': 'Ambient Light Sensor Data'})
                    light_chart.set_x_axis({'name': 'Index'})
                    light_chart.set_y_axis({'name': 'Light (lux)'})
                    light_chart.set_legend({'position': 'bottom'})
                    sheet_plot.insert_chart('B2', light_chart, {'x_scale': 2.0, 'y_scale': 1.2})

                    # RGB Chart
                    rgb_chart = workbook.add_chart({'type': 'line'})
                    rgb_chart.add_series({
                        'name': 'Red',
                        'categories': ['RGB and Light Data', 1, 0, min_len, 0],
                        'values':     ['RGB and Light Data', 1, 3, min_len, 3],
                        'line': {'color': 'red'}
                    })
                    rgb_chart.add_series({
                        'name': 'Green',
                        'categories': ['RGB and Light Data', 1, 0, min_len, 0],
                        'values':     ['RGB and Light Data', 1, 4, min_len, 4],
                        'line': {'color': 'green'}
                    })
                    rgb_chart.add_series({
                        'name': 'Blue',
                        'categories': ['RGB and Light Data', 1, 0, min_len, 0],
                        'values':     ['RGB and Light Data', 1, 5, min_len, 5],
                        'line': {'color': 'blue'}
                    })
                    rgb_chart.set_title({'name': 'RGB Sensor Data'})
                    rgb_chart.set_x_axis({'name': 'Index'})
                    rgb_chart.set_y_axis({'name': 'RGB Values'})
                    rgb_chart.set_legend({'position': 'bottom'})
                    sheet_plot.insert_chart('B22', rgb_chart, {'x_scale': 2.0, 'y_scale': 1.2})

                    workbook.close()

                else:
                    # CSV Export
                    if not path.endswith(".csv"):
                        path += ".csv"
                    with open(path, 'w', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(['Index', 'Timestamp', 'Light', 'Red', 'Green', 'Blue'])
                        for i in range(min_len):
                            writer.writerow([i, f"'{timestamps[i]}", light[i], r[i], g[i], b[i]])

                self.log_window.log_message(f"\nSaved RGB and Light data to: {path}")

            except Exception as e:
                self.log_window.log_message(f"\nFailed to save file: {e}")


            
    # def on_save_csv(self, event):
    #     """
    #     Ask the user to choose file format (.xlsx or .csv) and save RGB/Light data.
    #     """
    #     # import xlsxwriter  # Ensure this import exists at top of file if not already

    #     format_dialog = wx.SingleChoiceDialog(
    #         self,
    #         "Choose a file format to save:",
    #         "Save As",
    #         ["XLSX (Excel)", "CSV"]
    #     )

    #     if format_dialog.ShowModal() != wx.ID_OK:
    #         return  # User cancelled

    #     file_type = format_dialog.GetStringSelection()
    #     wildcard = "Excel files (*.xlsx)|*.xlsx" if "XLSX" in file_type else "CSV files (*.csv)|*.csv"

    #     with FileDialog(self, "Save File", wildcard=wildcard,
    #                     style=FD_SAVE | FD_OVERWRITE_PROMPT) as fileDialog:
    #         if fileDialog.ShowModal() == wx.ID_CANCEL:
    #             return  # User cancelled

    #         path = fileDialog.GetPath()
    #         r = self.rgb_data.get("R", [])
    #         g = self.rgb_data.get("G", [])
    #         b = self.rgb_data.get("B", [])
    #         light = self.rgb_data.get("Light", [])
    #         timestamps = getattr(self, "timestamps", [])

    #         min_len = min(len(r), len(g), len(b), len(light), len(timestamps))

    #         try:
    #             if "XLSX" in file_type:
    #                 if not path.endswith(".xlsx"):
    #                     path += ".xlsx"
    #                 workbook = xlsxwriter.Workbook(path)

    #                 # Sheet 1: Data
    #                 sheet_main = workbook.add_worksheet("RGB and Light Data")
    #                 # Sheet 2: For Plotting
    #                 sheet_plot = workbook.add_worksheet("Plotting")

    #                 # Define formats
    #                 header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
    #                 center_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})

    #                 # Header row
    #                 headers = ['Index', 'Timestamp', 'Light', 'Red', 'Green', 'Blue']
    #                 for col, header in enumerate(headers):
    #                     sheet_main.write(0, col, header, header_format)
    #                     sheet_plot.write(0, col, header, header_format)

    #                 # Data rows
    #                 for i in range(min_len):
    #                     row = [i, timestamps[i], light[i], r[i], g[i], b[i]]
    #                     for col, value in enumerate(row):
    #                         sheet_main.write(i + 1, col, value, center_format)
    #                         sheet_plot.write(i + 1, col, value, center_format)

    #                 # Column widths
    #                 for sheet in (sheet_main, sheet_plot):
    #                     sheet.set_column('A:A', 8)
    #                     sheet.set_column('B:B', 23)
    #                     sheet.set_column('C:F', 10)

    #                 # === Insert line chart in Plotting sheet ===
    #                 chart = workbook.add_chart({'type': 'line'})

    #                 chart.add_series({
    #                     'name':       'Light',
    #                     'categories': ['Plotting', 1, 0, min_len, 0],
    #                     'values':     ['Plotting', 1, 2, min_len, 2],
    #                     'line':       {'color': 'orange'}
    #                 })
    #                 chart.add_series({
    #                     'name':       'Red',
    #                     'categories': ['Plotting', 1, 0, min_len, 0],
    #                     'values':     ['Plotting', 1, 3, min_len, 3],
    #                     'line':       {'color': 'red'}
    #                 })
    #                 chart.add_series({
    #                     'name':       'Green',
    #                     'categories': ['Plotting', 1, 0, min_len, 0],
    #                     'values':     ['Plotting', 1, 4, min_len, 4],
    #                     'line':       {'color': 'green'}
    #                 })
    #                 chart.add_series({
    #                     'name':       'Blue',
    #                     'categories': ['Plotting', 1, 0, min_len, 0],
    #                     'values':     ['Plotting', 1, 5, min_len, 5],
    #                     'line':       {'color': 'blue'}
    #                 })

    #                 chart.set_title({'name': 'RGB and Light Sensor Data'})
    #                 chart.set_x_axis({'name': 'Index'})
    #                 chart.set_y_axis({'name': 'Sensor Values'})
    #                 chart.set_legend({'position': 'bottom'})

    #                 # Place chart in Plotting sheet at cell H2
    #                 sheet_plot.insert_chart('H2', chart, {'x_scale': 2.0, 'y_scale': 1.5})

    #                 workbook.close()

    #             else:
    #                 if not path.endswith(".csv"):
    #                     path += ".csv"
    #                 with open(path, 'w', newline='') as csvfile:
    #                     writer = csv.writer(csvfile)
    #                     writer.writerow(['Index', 'Timestamp', 'Light', 'Red', 'Green', 'Blue'])
    #                     for i in range(min_len):
    #                         writer.writerow([i, f"'{timestamps[i]}", light[i], r[i], g[i], b[i]])

    #             self.log_window.log_message(f"\nSaved RGB and Light data to: {path}")

    #         except Exception as e:
    #             self.log_window.log_message(f"\nFailed to save file: {e}")

    
    # def on_save_csv(self, event):
    #     """
    #     Ask the user to choose file format (.xlsx or .csv) and save RGB/Light data.
    #     """
    #     # Ask user for file format
    #     format_dialog = wx.SingleChoiceDialog(
    #         self,
    #         "Choose a file format to save:",
    #         "Save As",
    #         ["XLSX (Excel)", "CSV"]
    #     )

    #     if format_dialog.ShowModal() != wx.ID_OK:
    #         return  # User cancelled

    #     file_type = format_dialog.GetStringSelection()
    #     wildcard = "Excel files (*.xlsx)|*.xlsx" if "XLSX" in file_type else "CSV files (*.csv)|*.csv"

    #     with FileDialog(self, "Save File", wildcard=wildcard,
    #                     style=FD_SAVE | FD_OVERWRITE_PROMPT) as fileDialog:
    #         if fileDialog.ShowModal() == wx.ID_CANCEL:
    #             return  # User cancelled

    #         path = fileDialog.GetPath()
    #         r = self.rgb_data.get("R", [])
    #         g = self.rgb_data.get("G", [])
    #         b = self.rgb_data.get("B", [])
    #         light = self.rgb_data.get("Light", [])
    #         timestamps = getattr(self, "timestamps", [])

    #         min_len = min(len(r), len(g), len(b), len(light), len(timestamps))

    #         try:
    #             if "XLSX" in file_type:
    #                 if not path.endswith(".xlsx"):
    #                     path += ".xlsx"
    #                 workbook = xlsxwriter.Workbook(path)

    #                 # Sheet 1: Data
    #                 sheet_main = workbook.add_worksheet("RGB and Light Data")
    #                 # Sheet 2: Duplicate for plotting
    #                 sheet_plot = workbook.add_worksheet("Plotting")

    #                 # Define formats
    #                 header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
    #                 center_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})

    #                 # Header row
    #                 headers = ['Index', 'Timestamp', 'Light', 'Red', 'Green', 'Blue']
    #                 for col, header in enumerate(headers):
    #                     sheet_main.write(0, col, header, header_format)
    #                     sheet_plot.write(0, col, header, header_format)

    #                 # Data rows
    #                 for i in range(min_len):
    #                     row = [i, timestamps[i], light[i], r[i], g[i], b[i]]
    #                     for col, value in enumerate(row):
    #                         sheet_main.write(i + 1, col, value, center_format)
    #                         sheet_plot.write(i + 1, col, value, center_format)

    #                 # Column widths
    #                 for sheet in (sheet_main, sheet_plot):
    #                     sheet.set_column('A:A', 8)
    #                     sheet.set_column('B:B', 23)
    #                     sheet.set_column('C:F', 10)

    #                 workbook.close()


    #             else:
    #                 if not path.endswith(".csv"):
    #                     path += ".csv"
    #                 with open(path, 'w', newline='') as csvfile:
    #                     writer = csv.writer(csvfile)
    #                     writer.writerow(['Index', 'Timestamp', 'Light', 'Red', 'Green', 'Blue'])
    #                     for i in range(min_len):
    #                         writer.writerow([i, f"'{timestamps[i]}", light[i], r[i], g[i], b[i]])

    #             self.log_window.log_message(f"\nSaved RGB and Light data to: {path}")

    #         except Exception as e:
    #             self.log_window.log_message(f"\nFailed to save file: {e}")
