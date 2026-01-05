
##############################################################################
# 
# Module: main.py
#
# Description:
#     Main program entry point.
#
# Author:
#     Vinay N, MCCI Corporation Aug 2024
#
# Revision history:
#     V1.0.0 Mon Aug 12 2024 01:00:00   Vinay N 
#       Module created

##############################################################################
import wx
from controlwindow import ControlPanel
from firmwarewindow import FirmwarePanel
import logwindow  # Import the logwindow module
from comdialog import ComDialog  # Import the ComDialog
from streamplot import StreamPlotFrame  # Import the StreamPlotFrame class
from blockframe import Blockframe
from uiGlobal import * 
from aboutDialog import *
import webbrowser
from colorset import ColorSet

#======================================================================
# COMPONENTS
#======================================================================
class MainFrame(wx.Frame):
    def __init__(self, parent):
        """Initialize the main application frame, menus, tabs, and log window."""
        super().__init__(None, title="MCCI Model2450 UI - Version 2.1.0", size=(600, 700))
        
        self.SetIcon(wx.Icon(os.path.join(os.path.abspath(os.path.dirname(__file__)), "icons", IMG_ICON)))
        # Create a status bar    
        self.CreateStatusBar(3)
        self.SetStatusWidths([150, 150, 150])  # Adjust width as needed
        self.SetStatusText("No COM", 0)
        self.SetStatusText("Disconnected", 1)
        self.SetStatusText("SN", 2)
        # Create a menu bar
        self.menu_bar = wx.MenuBar()
        self.file_menu = wx.Menu()
        self.model_menu = wx.Menu()
        self.config_menu = wx.Menu()
        self.help_menu = wx.Menu()

        # Add submenu items under "Select Model"
        self.model_2450 = self.model_menu.Append(wx.ID_ANY, "Connect - Alt+N")
        self.model_2450_id = self.model_2450.GetId()
        # self.model_4931 = self.model_menu.Append(wx.ID_ANY, "Model 4931")
        self.model_disconnect = self.model_menu.Append(wx.ID_ANY, "Disconnect - ALt+I")  # <-- New disconnect menu
        self.model_disconnect_id = self.model_disconnect.GetId()

        # Add submenu under Configure -> Stream Plot
        self.stream_plot_item = self.config_menu.Append(wx.ID_ANY, "Stream Plot")
        self.Bind(wx.EVT_MENU, self.on_stream_plot, self.stream_plot_item)
        
        #---- OnsetColor
        # Add submenu under Configure -> Stream Plot
        self.color_set = self.config_menu.Append(wx.ID_ANY, "Calibration")
        self.Bind(wx.EVT_MENU, self.OnsetColor, self.color_set) 
        self.block_frame = self.config_menu.Append(wx.ID_ANY, "BlockFrameScan")
        self.Bind(wx.EVT_MENU, self.OnsetBlockframe, self.block_frame)

        # Bind events
        # self.Bind(wx.EVT_MENU, self.on_select, self.model_2450)
        self.Bind(wx.EVT_MENU, self.on_select, id=self.model_2450_id)
        self.Bind(wx.EVT_MENU, self.on_disconnect, id=self.model_disconnect_id)

        

        # HELP
        self.model_about = self.help_menu.Append(wx.ID_ANY, "About")
        self.Bind(wx.EVT_MENU, self.OnAboutWindow, self.model_about) 
        
        # Creating the help menu
        self.abc = self.help_menu.Append(ID_MENU_HELP_2450, "Visit MCCI Model 2450 BACK")
        self.help_menu.Append(ID_MENU_HELP_MODEL2450LIB, "Visit Model2450lib")
        
        self.help_menu.AppendSeparator()
        self.help_menu.Append(ID_MENU_HELP_WEB, "MCCI Website")
        self.help_menu.Append(ID_MENU_HELP_PORT, "MCCI Support Portal")
        self.help_menu.AppendSeparator()
        
        self.Bind(wx.EVT_MENU, self.OnClickHelp, id=ID_MENU_HELP_2450)
        self.Bind(wx.EVT_MENU, self.OnClickHelp, id=ID_MENU_HELP_MODEL2450LIB)
       
        self.Bind(wx.EVT_MENU, self.OnClickHelp, id=ID_MENU_HELP_WEB)
        self.Bind(wx.EVT_MENU, self.OnClickHelp, id=ID_MENU_HELP_PORT)
        
        # Create the Close menu item
        close_item = wx.MenuItem(self.file_menu, wx.ID_EXIT, "Close\tCtrl+Q", "Close the application")
        self.file_menu.Append(close_item)
        self.new_window_item = self.file_menu.Append(wx.ID_ANY, "New Window\tCtrl+N")
        self.new_window_id = self.new_window_item.GetId()
        self.Bind(wx.EVT_MENU, self.on_new_window, id=self.new_window_id)


        # Bind the Close menu item to an event handler
        self.Bind(wx.EVT_MENU, self.on_close_app, close_item)

        # Append menus to the menu bar
        self.menu_bar.Append(self.file_menu, "File")
        self.menu_bar.Append(self.model_menu, "Select Device")
        self.menu_bar.Append(self.config_menu, "Tools")
        self.menu_bar.Append(self.help_menu, "Help")

        self.SetMenuBar(self.menu_bar)
        
        accel_tbl = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('N'), self.new_window_id),
            (wx.ACCEL_ALT, ord('N'), self.model_2450_id),
            (wx.ACCEL_ALT, ord('I'), self.model_disconnect_id),
            
        ])
        self.SetAcceleratorTable(accel_tbl)
        
        # Create the main panel
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Initialize log window
        log_window = logwindow.LogWindow(panel)
        # Tabs
        notebook = wx.Notebook(panel)
        self.control_tab = ControlPanel(notebook, log_window=log_window)
        self.firmware_tab = FirmwarePanel(notebook, log_window=log_window)
        notebook.AddPage(self.control_tab, "Control Mode")
        notebook.AddPage(self.firmware_tab, "Firmware Update")
        main_sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 5)

        # Log window
        self.logPan = log_window
        main_sizer.Add(self.logPan, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        panel.SetSizer(main_sizer)
        self.Centre()
    
    def on_new_window(self, event):
        """Open a new instance of the main window."""
        new_frame = MainFrame(parent=None)
        new_frame.Show()


    def on_stream_plot(self, event):
        """Launch the StreamPlotFrame for real-time plotting."""
        device = self.control_tab.device
        stream_plot_frame = StreamPlotFrame(parent=None, device=device)
        stream_plot_frame.Show()

    def OnsetColor(self, e):
        """Launch the ColorSet calibration window."""
        device = self.control_tab.device
        color_set_frame = ColorSet(parent=None, log_window=self.logPan, device=device)
        color_set_frame.Show()
    
    def OnsetBlockframe(self, e):
        """Launch the Blockframe scanning window."""
        device = self.control_tab.device
        color_set_frame = Blockframe(parent=None, log_window=self.logPan, device=device)
        color_set_frame.Show()

    def on_close_app(self, event):
        """Handler to close the application."""
        self.Close()  # This triggers the EVT_CLOSE event and calls OnClose if defined

    def on_select(self, event):
        """Show COM dialog to select and connect a device."""
        dialog = ComDialog(self)
        if dialog.ShowModal() == wx.ID_OK:
            device = dialog.device
            # self.control_tab.set_device(device)
            self.control_tab.set_device(device)
            # self.SetStatusText(f"{device.port} | Connected")
            self.SetStatusText(device.port, 0)
            self.SetStatusText("Connected", 1)
            self.SetStatusText(f"{device.sn}", 2)
        dialog.Destroy()
    
    def on_disconnect(self, event):
        """Handle disconnecting the currently connected device."""
        if self.control_tab.device is not None:
            try:
                self.control_tab.device.disconnect()  # Disconnect the device
                self.control_tab.device = None
                # self.firmware_tab.clear_device()  # Clear device info from firmware tab
                self.SetStatusText("No COM", 0)
                self.SetStatusText("Disconnected", 1)
                self.SetStatusText("SN", 2)
                wx.MessageBox("Device disconnected successfully.", "Info", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f"Error during disconnect: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
        else:
            wx.MessageBox("No device is currently connected.", "Info", wx.OK | wx.ICON_INFORMATION)

    def OnAboutWindow(self, event):
        """Show the About dialog."""
        dlg = AboutDialog(self, self)
        dlg.ShowModal()
        dlg.Destroy()
        
    def OnClickHelp(self, event):
        """Open appropriate help URLs based on menu item selection."""
        id = event.GetId()
        if (id == ID_MENU_HELP_2450):
            webbrowser.open("https://store.mcci.com/products/model-2450-brightness-and-color-kit",
                            new=0, autoraise=True)
        elif(id == ID_MENU_HELP_MODEL2450LIB):
            webbrowser.open("https://github.com/mcci-usb/model2450lib",
                            new=0, autoraise=True)
        elif(id == ID_MENU_HELP_WEB):
            webbrowser.open("https://mcci.com/", new=0, autoraise=True)
        elif(id == ID_MENU_HELP_PORT):
            webbrowser.open("https://portal.mcci.com/portal/home", new=0,
                            autoraise=True)
        elif(id == ID_MENU_HELP_ABOUT):
            self.OnAboutWindow(event)

class MyApp(wx.App):
    """Application initialization — creates and shows the main window."""
    def OnInit(self):
        frame = MainFrame(parent=None)
        frame.Show()
        return True

if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()
