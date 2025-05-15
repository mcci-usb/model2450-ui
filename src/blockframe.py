
##############################################################################
# 
# Module: blockfrmae.py
#
# Description:
#      Block frames
#
# Author:
#     Vinay N, MCCI Corporation May 2025
#
# Revision history:
#     V2.0.0 Mon May 2025 01:00:00   Vinay N 
#       Module created
##############################################################################
import wx
import os
import json
from pathlib import Path
from uiGlobal import *
import threading
from model2450lib import model2450
import time

def decode_packet(packet_bytes):
    """
    Decode a binary packet into a structured format.

    Parameters:
        packet_bytes (bytes): The raw bytes received from the device.

    Returns:
        dict: A dictionary containing decoded data fields such as command, payload, etc.

    Raises:
        ValueError: If the packet format is invalid or cannot be decoded.
    """
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
    """
    Read a complete packet from the serial port.

    Parameters:
        serial_port (serial.Serial): An open pySerial Serial object.

    Returns:
        bytes: The raw bytes of the received packet.

    Raises:
        TimeoutError: If a complete packet is not received within the expected time.
        ValueError: If the packet structure is invalid or corrupted.
    """
    header = ser.read(2)
    if len(header) < 2:
        return None

    length = header[1] & 0x1F
    remaining = length - 2
    payload = ser.read(remaining)
    if len(payload) < remaining:
        return None

    return header + payload

class Blockframe(wx.Frame):
    def __init__(self, parent, log_window, device=None):
        super(Blockframe, self).__init__(parent)
        self.SetIcon(wx.Icon(os.path.join(os.path.abspath(os.path.dirname(__file__)), "icons", IMG_ICON)))
        self.device = device
        self.log_window = log_window
        self.config_path = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")), "MCCI2450", "config.json")

        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        self.config = self.load_config()
        self.keep_running = False
        self.block_frame_count = 0  # Initialize block frame counter
        self.setup_ui()

    def setup_ui(self):
        self.SetTitle("Color Set Window")
        self.SetBackgroundColour("white")
        self.SetSize((380, 180))

        self.panel = wx.Panel(self)
        self.top_vbox = wx.BoxSizer(wx.VERTICAL)

        self.hbox_blink_frames = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox_run = wx.BoxSizer(wx.HORIZONTAL)

        self.st_lth = wx.StaticText(self.panel, label="Light Value Threshold")
        self.tc_lth = wx.TextCtrl(self.panel, value="", style=wx.TE_CENTRE | wx.TE_PROCESS_ENTER)
        self.btn_lth = wx.Button(self.panel, label="Update")

        self.btn_run = wx.Button(self.panel, label="Run")
        self.btn_stop = wx.Button(self.panel, label="Stop")
        self.tc_time = wx.TextCtrl(self.panel, value="%H:%M:%S", style=wx.TE_CENTRE | wx.TE_PROCESS_ENTER)

        self.hbox_blink_frames.AddMany([(self.st_lth, 1, wx.ALL, 10), (self.tc_lth, 1, wx.ALL, 10), (self.btn_lth, 1, wx.ALL, 10)])
        self.hbox_run.AddMany([(self.btn_run, 1, wx.ALL, 10), (self.btn_stop, 1, wx.ALL, 10), (self.tc_time, 1, wx.ALL, 10)])

        self.top_vbox.Add(self.hbox_blink_frames, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.top_vbox.Add(self.hbox_run, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.panel.SetSizer(self.top_vbox)
        self.Centre()

        # Event Bindings
        self.btn_lth.Bind(wx.EVT_BUTTON, self.on_update)
        self.btn_run.Bind(wx.EVT_BUTTON, self.on_start)
        self.btn_stop.Bind(wx.EVT_BUTTON, self.on_stop)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_time, self.timer)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Load Threshold
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

    def save_config(self):
        """Save the current configuration to JSON."""
        with open(self.config_path, 'w') as file:
            json.dump(self.config, file, indent=4)

    def load_light_threshold(self):
        """Load threshold into TextCtrl."""
        light_threshold = self.config.get("light_threshold", "")
        self.tc_lth.SetValue(str(light_threshold))

    def on_update(self, event):
        """Handle update threshold."""
        try:
            level_value = int(self.tc_lth.GetValue())
            
            # Save threshold to config file
            self.config['light_threshold'] = level_value
            self.save_config()
            
            if self.device is not None:
                # Run device update in a separate thread!
                threading.Thread(target=self.update_device_level, args=(level_value,), daemon=True).start()
            else:
                self.log_window.log_message(f"Saved threshold locally: {level_value} (device not connected)")

        except ValueError:
            wx.MessageBox("Please enter a valid integer.", "Error", wx.OK | wx.ICON_ERROR)
        except Exception as ex:
            wx.MessageBox(f"Error during update: {ex}", "Error", wx.OK | wx.ICON_ERROR)

    def update_device_level(self, level_value):
        """Update the device level in a background thread."""
        try:
            response = self.device.set_level(level_value)
            wx.CallAfter(self.log_window.log_message, f"Sent level {level_value}, response: {response}")
        except Exception as ex:
            wx.CallAfter(wx.MessageBox, f"Device update error: {ex}", "Error", wx.OK | wx.ICON_ERROR)

    def OnClose(self, event):
        self.stop_timer()
        self.Destroy()
        event.Skip()  # Good practice to allow wxWidgets to fully process close event

    def on_start(self, event):
        if not self.keep_running:
            if self.device is None:
                wx.MessageBox("Please connect a device first.", "Error", wx.OK | wx.ICON_ERROR)
                return

            self.keep_running = True
            self.block_frame_count = 0  # Reset counter on start
            self.ser = self.device.ser
            self.ser.write(b"run\r\n")
            self.serial_thread = threading.Thread(target=self.read_serial_data)
            self.serial_thread.start()

            # Set the timeout (10 or 15 seconds)
            self.timeout_seconds = 10  # Modify this value as needed
            self.timeout_timer = threading.Timer(self.timeout_seconds, self.on_stop)
            self.timeout_timer.start()

            # Optionally start a timer to update the time in the text field
            self.start_timer()
    
    def on_stop(self, event):
        if self.keep_running:
            self.keep_running = False
            self.ser.write(b"stop\r\n")
    
    def read_serial_data(self):
        buffer = b""
        buffered_payload = b""  # Ensure initialization of buffered_payload
        while self.keep_running:
            packet = read_packet_from_serial(self.ser)
            if packet:
                try:
                    decoded = decode_packet(packet)
                    payload = decoded.get("payload", b"")
                    start_bit = decoded["start_bit"]
                    end_bit = decoded["end_bit"]
                    reserved_bit = decoded["reserved"]
                    command = decoded["command"]
                    sequence = decoded["sequence"]
                    length = decoded["length"]

                    if start_bit:
                        buffered_payload = payload
                    else:
                        buffered_payload += payload

                    if end_bit or len(payload) < decoded["length"] - 2:
                        try:
                            ascii_payload = buffered_payload.decode("ascii").strip()
                            print("ascii-payload:", ascii_payload)
                            self.log_window.log_message(ascii_payload)

                            if ascii_payload and ascii_payload[0].isalpha():
                                pass
                            elif ':' in ascii_payload:
                                print(f"Structured Data: {ascii_payload}")
                        except UnicodeDecodeError:
                            print(f"payload: {buffered_payload.hex()} (non-ascii)")

                        buffered_payload = b""  # Reset after processing

                        # Increment block frame count
                        self.block_frame_count += 1
                        wx.CallAfter(self.update_ui_count)

                except Exception as decode_err:
                    print("Decode error:", decode_err)

            time.sleep(0.0006)

    def update_ui_count(self):
        """Update the block frame count in the GUI."""
        self.SetTitle(f"Color Set Window - Frames: {self.block_frame_count}")

    def start_timer(self):
        """Start the timer.""" 
        self.timer.Start(1000)  # every 1 second

    def stop_timer(self):
        """Stop the timer.""" 
        self.timer.Stop()

    def update_time(self, event):
        """Update time field."""
        import time
        current_time = time.strftime("%H:%M:%S")
        self.tc_time.SetValue(current_time)
    
    def OnClose(self, event=None):
        self.keep_running = False
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.write(b"stop\r\n")
            self.ser.close()
        if self.serial_thread:
            self.serial_thread.join()
        # self.Destroy()