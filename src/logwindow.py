##############################################################################
# 
# Module: logwindow.py
#
# Description:
#     View the device log.
#
# Author:
#     Vinay N, MCCI Corporation February 2026
#
# Revision history:
#     V2.2.0 Fri Feb 2026 20:02:2026   Vinay N
#       Module created
#
##############################################################################

# Built-in imports
import os
from datetime import datetime

# Third-party imports
import wx


__author__ = "Vinay N"
__copyright__ = "Copyright 2025, MCCI Corporation"
__version__ = "2.0.0"
__status__ = "Development"


class LogWindow(wx.Window):
    """
    Log display window for device communication messages.

    Provides timestamp option, clear functionality,
    and export-to-file capability.
    """

    def __init__(self, parent):
        """
        Initialize LogWindow UI components and layout.

        Args:
            parent:
                Parent wx window.

        Returns:
            None
        """
        super().__init__(parent)

        static_box = wx.StaticBox(self, -1, "Log Window")
        self.vbox = wx.StaticBoxSizer(static_box, wx.VERTICAL)

        self.cb_timestamp = wx.CheckBox(
            self, -1, "Timestamp"
        )
        self.cb_timestamp.SetToolTip(
            wx.ToolTip(
                "Include timestamp in log messages"
            )
        )

        self.btn_save = wx.Button(
            self, -1, "Save", size=(60, -1)
        )

        self.btn_clear = wx.Button(
            self, -1, "Clear", size=(60, 25)
        )

        self.btn_save.SetToolTip(
            wx.ToolTip(
                "Save log content to a text file"
            )
        )

        self.btn_clear.SetToolTip(
            wx.ToolTip("Clear log messages")
        )

        self.scb = wx.TextCtrl(
            self,
            -1,
            style=wx.TE_MULTILINE | wx.TE_READONLY
        )

        self.scb.SetBackgroundColour((255, 255, 255))

        self._create_layout()
        self._bind_events()

    def _create_layout(self):
        """
        Create and arrange UI layout.

        Returns:
            None
        """
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.cb_timestamp, 0, wx.RIGHT, 30)
        hbox.Add(self.btn_clear, 0, wx.RIGHT, 30)
        hbox.Add(self.btn_save, 1, wx.RIGHT, 180)

        szr_top = wx.BoxSizer(wx.VERTICAL)
        szr_top.Add(self.scb, 1, wx.EXPAND)

        self.vbox.AddSpacer(10)
        self.vbox.Add(hbox, 0, wx.ALIGN_LEFT)
        self.vbox.AddSpacer(10)
        self.vbox.Add(szr_top, 1, wx.EXPAND)

        self.SetSizer(self.vbox)
        self.Layout()

    def _bind_events(self):
        """
        Bind button events to handlers.

        Returns:
            None
        """
        self.btn_clear.Bind(wx.EVT_BUTTON,
                            self.clear_log_window)
        self.btn_save.Bind(wx.EVT_BUTTON,
                           self.save_log_window)

    def log_message(self, message):
        """
        Append a log message to the window.

        If timestamp option is enabled, a formatted
        timestamp is prefixed to the message.

        Args:
            message:
                Message string to append.

        Returns:
            None
        """
        try:
            if self.cb_timestamp.IsChecked():
                current_time = datetime.now()
                timestamp = current_time.strftime(
                    "%Y-%m-%d  %H:%M:%S.%f"
                )
                message = (
                    f"[{timestamp[:-3]}]  {message}"
                )

            self.scb.AppendText(message + "\n")

        except Exception as exc:
            print(f"Log message error: {exc}")

    def log_inline(self, message):
        """
        Append text without adding a newline.

        Args:
            message:
                Message string to append.

        Returns:
            None
        """
        try:
            self.scb.AppendText(message)
        except Exception as exc:
            print(f"Log inline error: {exc}")

    def clear_log_window(self, event):
        """
        Clear all log messages from the window.

        Args:
            event:
                wx button event object.

        Returns:
            None
        """
        self.scb.SetValue("")

    def save_log_window(self, event):
        """
        Save current log content to a file.

        Args:
            event:
                wx button event object.

        Returns:
            None
        """
        content = self.scb.GetValue()
        self._save_file(content, "*.txt")

    def _save_file(self, contents, extension):
        """
        Save provided contents to a selected file.

        Args:
            contents:
                Text content to save.

            extension:
                File extension filter.

        Returns:
            None

        Raises:
            OSError:
                If file cannot be written.
        """
        dlg = wx.FileDialog(
            self,
            "Save as",
            "",
            "",
            extension,
            wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )

        if dlg.ShowModal() == wx.ID_OK:
            wx.BeginBusyCursor()

            directory = dlg.GetDirectory()
            filename = os.path.join(
                directory,
                dlg.GetFilename()
            )

            try:
                with open(filename, "w") as file:
                    file.write(contents)
            except OSError as exc:
                wx.MessageBox(
                    f"Error saving file:\n\n{exc}",
                    "Error",
                    wx.OK | wx.ICON_ERROR
                )

            wx.EndBusyCursor()

        dlg.Destroy()