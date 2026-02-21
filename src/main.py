##############################################################################
# 
# Module: main.py
#
# Description:
#     Main program entry point.
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
import webbrowser

# Third-party imports
import wx

# Local application imports
from controlwindow import ControlPanel
from firmwarewindow import FirmwarePanel
import logwindow
from comdialog import ComDialog
from streamplot import StreamPlotFrame
from blockframe import Blockframe
from uiGlobal import *
from aboutDialog import AboutDialog
from colorset import ColorSet


__author__ = "Vinay N"
__copyright__ = "Copyright 2024, MCCI Corporation"
__version__ = "1.0.0"
__status__ = "Development"


class MainFrame(wx.Frame):
    """
    Main application window for Model2450 UI.

    This frame manages menu operations, device
    connection handling, tool windows, tab views,
    and application logging.
    """

    def __init__(self, parent):
        """
        Initialize the main application frame.

        This method creates menus, status bar,
        notebook tabs, logging window, and binds
        all application events.

        Args:
            parent:
                Parent wx window.

        Returns:
            None
        """
        super().__init__(
            None,
            title="MCCI Model2450 UI - Version 2.2.0",
            size=(600, 700)
        )

        self.SetIcon(
            wx.Icon(
                os.path.join(
                    os.path.abspath(os.path.dirname(__file__)),
                    "icons",
                    IMG_ICON
                )
            )
        )

        self._create_status_bar()
        self._create_menu_bar()
        self._create_main_layout()

        self.Centre()

    def _create_status_bar(self):
        """
        Create and initialize the status bar.

        Returns:
            None
        """
        self.CreateStatusBar(3)
        self.SetStatusWidths([150, 150, 150])
        self.SetStatusText("No COM", 0)
        self.SetStatusText("Disconnected", 1)
        self.SetStatusText("SN", 2)

    def _create_menu_bar(self):
        """
        Create application menu bar and bind events.

        Returns:
            None
        """
        self.menu_bar = wx.MenuBar()

        self.file_menu = wx.Menu()
        self.model_menu = wx.Menu()
        self.config_menu = wx.Menu()
        self.help_menu = wx.Menu()

        # Device menu
        self.model_2450 = self.model_menu.Append(
            wx.ID_ANY, "Connect - Alt+N"
        )
        self.model_2450_id = self.model_2450.GetId()

        self.model_disconnect = self.model_menu.Append(
            wx.ID_ANY, "Disconnect - Alt+I"
        )
        self.model_disconnect_id = self.model_disconnect.GetId()

        self.Bind(wx.EVT_MENU, self.on_select,
                  id=self.model_2450_id)
        self.Bind(wx.EVT_MENU, self.on_disconnect,
                  id=self.model_disconnect_id)

        # Tools menu
        self.stream_plot_item = self.config_menu.Append(
            wx.ID_ANY, "Stream Plot"
        )
        self.Bind(wx.EVT_MENU,
                  self.on_stream_plot,
                  self.stream_plot_item)

        self.color_set = self.config_menu.Append(
            wx.ID_ANY, "Calibration"
        )
        self.Bind(wx.EVT_MENU,
                  self.on_set_color,
                  self.color_set)

        self.block_frame = self.config_menu.Append(
            wx.ID_ANY, "Block Frame Scan"
        )
        self.Bind(wx.EVT_MENU,
                  self.on_set_blockframe,
                  self.block_frame)

        # Help menu
        self.model_about = self.help_menu.Append(
            wx.ID_ANY, "About"
        )
        self.Bind(wx.EVT_MENU,
                  self.on_about_window,
                  self.model_about)

        self.help_menu.Append(
            ID_MENU_HELP_2450,
            "Visit MCCI Model 2450"
        )
        self.help_menu.Append(
            ID_MENU_HELP_MODEL2450LIB,
            "Visit Model2450lib"
        )

        self.help_menu.AppendSeparator()
        self.help_menu.Append(
            ID_MENU_HELP_WEB,
            "MCCI Website"
        )
        self.help_menu.Append(
            ID_MENU_HELP_PORT,
            "MCCI Support Portal"
        )

        self.Bind(wx.EVT_MENU,
                  self.on_click_help,
                  id=ID_MENU_HELP_2450)
        self.Bind(wx.EVT_MENU,
                  self.on_click_help,
                  id=ID_MENU_HELP_MODEL2450LIB)
        self.Bind(wx.EVT_MENU,
                  self.on_click_help,
                  id=ID_MENU_HELP_WEB)
        self.Bind(wx.EVT_MENU,
                  self.on_click_help,
                  id=ID_MENU_HELP_PORT)

        # File menu
        close_item = wx.MenuItem(
            self.file_menu,
            wx.ID_EXIT,
            "Close\tCtrl+Q",
            "Close the application"
        )
        self.file_menu.Append(close_item)
        self.Bind(wx.EVT_MENU,
                  self.on_close_app,
                  close_item)

        # Append menus
        self.menu_bar.Append(self.file_menu, "File")
        self.menu_bar.Append(self.model_menu, "Select Device")
        self.menu_bar.Append(self.config_menu, "Tools")
        self.menu_bar.Append(self.help_menu, "Help")

        self.SetMenuBar(self.menu_bar)

    def _create_main_layout(self):
        """
        Create notebook tabs and logging layout.

        Returns:
            None
        """
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        log_window = logwindow.LogWindow(panel)

        notebook = wx.Notebook(panel)

        self.control_tab = ControlPanel(
            notebook,
            log_window=log_window
        )

        self.firmware_tab = FirmwarePanel(
            notebook,
            log_window=log_window
        )

        notebook.AddPage(self.control_tab, "Control Mode")
        notebook.AddPage(self.firmware_tab, "Firmware Update")

        main_sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 5)

        self.logPan = log_window
        main_sizer.Add(
            self.logPan,
            1,
            wx.EXPAND | wx.ALL,
            5
        )

        panel.SetSizer(main_sizer)

    def on_stream_plot(self, event):
        """
        Launch real-time stream plotting window.

        Args:
            event:
                wx menu event object.

        Returns:
            None
        """
        device = self.control_tab.device
        frame = StreamPlotFrame(parent=None,
                                device=device)
        frame.Show()

    def on_set_color(self, event):
        """
        Launch color calibration window.

        Args:
            event:
                wx menu event object.

        Returns:
            None
        """
        device = self.control_tab.device
        frame = ColorSet(parent=None,
                         log_window=self.logPan,
                         device=device)
        frame.Show()

    def on_set_blockframe(self, event):
        """
        Launch block frame detection window.

        Args:
            event:
                wx menu event object.

        Returns:
            None
        """
        device = self.control_tab.device
        frame = Blockframe(parent=None,
                           log_window=self.logPan,
                           device=device)
        frame.Show()

    def on_close_app(self, event):
        """
        Close the application.

        Args:
            event:
                wx menu event object.

        Returns:
            None
        """
        self.Close()

    def on_select(self, event):
        """
        Open COM dialog and connect device.

        Args:
            event:
                wx menu event object.

        Returns:
            None
        """
        dialog = ComDialog(self)

        if dialog.ShowModal() == wx.ID_OK:
            device = dialog.device
            self.control_tab.set_device(device)

            self.SetStatusText(device.port, 0)
            self.SetStatusText("Connected", 1)
            self.SetStatusText(f"{device.sn}", 2)

        dialog.Destroy()

    def on_disconnect(self, event):
        """
        Disconnect currently connected device.

        Args:
            event:
                wx menu event object.

        Returns:
            None
        """
        if self.control_tab.device is not None:
            try:
                self.control_tab.device.disconnect()
                self.control_tab.device = None

                self.SetStatusText("No COM", 0)
                self.SetStatusText("Disconnected", 1)
                self.SetStatusText("SN", 2)

                wx.MessageBox(
                    "Device disconnected successfully.",
                    "Info",
                    wx.OK | wx.ICON_INFORMATION
                )

            except Exception as exc:
                wx.MessageBox(
                    f"Error during disconnect: {exc}",
                    "Error",
                    wx.OK | wx.ICON_ERROR
                )
        else:
            wx.MessageBox(
                "No device is currently connected.",
                "Info",
                wx.OK | wx.ICON_INFORMATION
            )

    def on_about_window(self, event):
        """
        Display About dialog window.

        Args:
            event:
                wx menu event object.

        Returns:
            None
        """
        dlg = AboutDialog(self, self)
        dlg.ShowModal()
        dlg.Destroy()

    def on_click_help(self, event):
        """
        Open help resources based on menu selection.

        Args:
            event:
                wx menu event object.

        Returns:
            None
        """
        menu_id = event.GetId()

        if menu_id == ID_MENU_HELP_2450:
            webbrowser.open(
                "https://store.mcci.com/products/"
                "model-2450-brightness-and-color-kit"
            )

        elif menu_id == ID_MENU_HELP_MODEL2450LIB:
            webbrowser.open(
                "https://github.com/mcci-usb/model2450lib"
            )

        elif menu_id == ID_MENU_HELP_WEB:
            webbrowser.open("https://mcci.com/")

        elif menu_id == ID_MENU_HELP_PORT:
            webbrowser.open(
                "https://portal.mcci.com/portal/home"
            )


class MyApp(wx.App):
    """
    Application bootstrap class.
    """

    def OnInit(self):
        """
        Initialize and show main frame.

        Returns:
            bool:
                True if initialization succeeds.
        """
        frame = MainFrame(parent=None)
        frame.Show()
        return True


if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()
