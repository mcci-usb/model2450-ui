##############################################################################
# 
# Module: uiMainApp.py
#
# Description:
#      Main Application body for the MCCI Model 2450 GUI Application
#
# Author:
#     Vinay N, MCCI Corporation Aug 2024
#
# Revision history:
#     V1.0.0 Mon Aug 12 2024 01:00:00   Vinay N 
#       Module created

##############################################################################
import wx
from uiGlobal import * 
from aboutDialog import *

from pathlib import Path

import controlWindow
import firmwareWindow

from comDialog import ComDialog

import webbrowser

# from controlWindow import ControlWindow
import logWindow

# import login
# from login import LogIn
from colorset import ColorSet



# from cricketlib import searchswitch

# from model2450lib import switch2450
# from model2450lib import searchswitch

class MultiStatus (wx.StatusBar):
    """
    A class Multistatus with init method
    This code pattern is run common in all Python files that
    to be executed as a script imported in another modules.
    """
    def __init__ (self, parent):
        """
        Associates a status bar with the frame.

        Args:
            self: The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
            parent: Pointer to a parent window.
        Returns:
            None
        """
        wx.StatusBar.__init__(self, parent, -1)
        # Sets the number of field count "5"
        self.SetFieldsCount(3)
        # Sets the widths of the fields in the status bar.
        self.SetStatusWidths([-2, -2, -10])
        

# uiMainapp.py

class UiMainFrame(wx.Frame):
    """
    A UiMainFrame is a window of size and position usually changed by user
    """
    def __init__(self, parent, title):
        """
        MainFrame initialization

        Args:
            self:The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
            parent: Pointer to a parent window.
            title: Ui title name uodate
        Returns:
            None
        """
        wx.Frame.__init__(self, None, size=(540,650))
        
        self.switch = None

        self.SetBackgroundColour("White")
        self.SetTitle('MCCI Model 2450 UI - Version 1.0.0')
        
        base = os.path.abspath(os.path.dirname(__file__))
        self.SetIcon(wx.Icon(base+"/icons/"+IMG_ICON))
        self.Show()

        self.declare_globals()

        self.logPan = logWindow.LogWindow(self, parent)

        self.nb = wx.Notebook(self)
        self.controlPan = controlWindow.ControlWindow(self.nb, self.logPan)

        self.firmwarePan = firmwareWindow.FirmwareWindow(self.nb, self.logPan)

        self.nb.AddPage(self.controlPan, "Control Mode")
        self.nb.AddPage(self.firmwarePan, "Firmware Update")

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.main_sizer.Add(self.nb, 1, wx.EXPAND | wx.ALL, 10)
        self.main_sizer.Add(self.logPan, 1, wx.EXPAND | wx.ALL, 10)

        self.SetSizer(self.main_sizer)

        self.CreateStatusBar()
        self.init_statusBar()

        self.menu_bar = wx.MenuBar()

        self.file_menu = wx.Menu()
        self.file_menu.Append(wx.ID_EXIT, "Close")
        self.menu_bar.Append(self.file_menu, "File")

        self.connect_menu = wx.Menu()
        self.connect_menu.Append(wx.ID_ANY, "Connect")
        self.connect_menu.Append(wx.ID_ANY, "Disconnect")
        self.menu_bar.Append(self.connect_menu, "Select Switch")

        configure_menu = wx.Menu()
        configure_menu.Append(wx.ID_ANY, "Configure")
        self.menu_bar.Append(configure_menu, "Configure")

        self.helpMenu = wx.Menu()
        self.helpMenu.Append(wx.ID_ABOUT, "About...")
        self.menu_bar.Append(self.helpMenu, "Help")

        self.SetMenuBar(self.menu_bar)
        self.Centre()
        self.Show()

        self.build_help_menu()

        self.Bind(wx.EVT_MENU, self.OnCloseWindow, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.OnAboutWindow, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.OnConnect, id=self.connect_menu.FindItem("Connect"))
        self.Bind(wx.EVT_MENU, self.OnDisconnect, id=self.connect_menu.FindItem("Disconnect"))
        self.Bind(wx.EVT_MENU, self.OnsetColor, id=configure_menu.FindItem("Configure"))


    def build_help_menu(self):
        """
        Build the help menu.

        Description:
            - Appends menu items to visit different MCCI USB Switch models.
        """
        # Creating the help menu
        self.abc = self.helpMenu.Append(ID_MENU_HELP_2450, "Visit MCCI Model 2450 BACK")
        self.helpMenu.Append(ID_MENU_HELP_3141, "Visit MCCI USB Switch 3141")
        self.helpMenu.Append(ID_MENU_HELP_3201, "Visit MCCI USB Switch 3201")
        self.helpMenu.Append(ID_MENU_HELP_2101, "Visit MCCI USB Switch 2101")
        self.helpMenu.Append(ID_MENU_HELP_2301, "Visit MCCI USB Switch 2301")
        self.helpMenu.AppendSeparator()
        self.helpMenu.Append(ID_MENU_HELP_WEB, "MCCI Website")
        self.helpMenu.Append(ID_MENU_HELP_PORT, "MCCI Support Portal")
        self.helpMenu.AppendSeparator()
        
        self.Bind(wx.EVT_MENU, self.OnClickHelp, id=ID_MENU_HELP_2450)
        self.Bind(wx.EVT_MENU, self.OnClickHelp, id=ID_MENU_HELP_3141)
        self.Bind(wx.EVT_MENU, self.OnClickHelp, id=ID_MENU_HELP_3201)
        self.Bind(wx.EVT_MENU, self.OnClickHelp, id=ID_MENU_HELP_2101)
        self.Bind(wx.EVT_MENU, self.OnClickHelp, id=ID_MENU_HELP_2301)
        self.Bind(wx.EVT_MENU, self.OnClickHelp, id=ID_MENU_HELP_WEB)
        self.Bind(wx.EVT_MENU, self.OnClickHelp, id=ID_MENU_HELP_PORT)
    
    def init_statusBar(self):
        """
        Initializes the status bar for the main application window.

       Notes:
            - The status bar is created using the MultiStatus class.
            - The initial status is set to display information about ports.
        """
         # Create the statusbar
        self.statusbar = MultiStatus(self)
        self.SetStatusBar(self.statusbar)
        self.UpdateAll(["COM", "", ""])
        
    
    def UpdateAll (self, textList):
        """
        Status bar update - All fields

        Args:
            self:The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
            textList: set the status bar
        Returns:
            None
        """
        for i in range(len(textList)):
            self.SetStatusText(textList[i], i)
        self.UpdateStatusBar()
    
    def UpdateStatusBar (self):
        """
        Update the device status in status bar, when connect/disconnect

        Args:
            self:The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
        Returns:
            None
        """
        self.statusbar.Refresh()
        self.statusbar.Update()

    def declare_globals(self):
        """
        Initializes global variables.

        Notes:
            - Assumes the need for global variables 'init_flg' and 'ldata'.

        """
        global app
        app = self

    def on_exit(self, event):
        self.Close()

    def OnAboutWindow(self, event):
        """
        Virtual event handlers, overide them in your derived class
        About UI Software

        Args:
           self:The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
            event:event handler for about menu window
        Returns:
            None
        """
        dlg = AboutDialog(self, self)
        dlg.ShowModal()
        dlg.Destroy()

    def OnClickHelp(self, event):
        """
        Virtual event handlers, overide them in your derived class
        Args:
            self:The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
            event: event handler for helpmenu
        Returns:
            None
        """
        id = event.GetId()
        if (id == ID_MENU_HELP_2450):
            webbrowser.open("https://store.mcci.com/products/model-2450-brightness-and-color-kit",
                            new=0, autoraise=True)
        elif(id == ID_MENU_HELP_3141):
            webbrowser.open("https://mcci.com/usb/dev-tools/model-3141/",
                            new=0, autoraise=True)
        elif(id == ID_MENU_HELP_3201):
            webbrowser.open("https://mcci.com/usb/dev-tools/3201-enhanced"
                            "-type-c-connection-exerciser/",
                            new=0, autoraise=True)
        elif(id == ID_MENU_HELP_2101):
            webbrowser.open(
            "https://mcci.com/usb/dev-tools/2101-usb-connection-exerciser/",
                            new=0, autoraise=True)
        elif(id == ID_MENU_HELP_2301):
            webbrowser.open("https://mcci.com/usb/dev-tools/model-2301/",
                            new=0, autoraise=True)       
        elif(id == ID_MENU_HELP_WEB):
            webbrowser.open("https://mcci.com/", new=0, autoraise=True)
        elif(id == ID_MENU_HELP_PORT):
            webbrowser.open("https://portal.mcci.com/portal/home", new=0,
                            autoraise=True)
        elif(id == ID_MENU_HELP_ABOUT):
            self.OnAboutWindow(event)

    def OnConnect(self, event):
        """
        click on Connect sub menu under the manage model menu, 
        shows the dialog box with connecting device.
        Args:
            self: The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
            event: search and connect event.
        Returns:
            None
        """
        dialog = ComDialog(self, title="Select COM Port", control_window=self.controlPan, firmware_window=self.firmwarePan)
        dialog.ShowModal()

        dialog.Destroy()
    
    def OnsetColor(self, e):
        if not self.controlPan.switch:
            wx.MessageBox("No switch connected.", "Error", wx.OK | wx.ICON_ERROR)
            return

        dialog = ColorSet(self, "Color Normalization", self.log_message)  # Pass log_message instead of self
        dialog.set_switch(self.controlPan.switch)  # Pass the switch to ColorSet
        dialog.Show()
    
    def OnCloseWindow(self, event):
        """
        Virtual event handlers, overide them in your derived class
        for Window Close

        Args:
            self:The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
            event:event handler for window close
        Returns:
            None
        """ 
        self.Close()

    def log_message(self, message):
        """
        Updates the status log menu based on the selected configuration.
        """
        self.logPan.log_message(message)
    
    def OnDisconnect(self, event):
        """
         click on disconnect menu the connecting device is disconnect.
         Args:
             self: The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
             event: event handling on disconnect menu.
         Returns:
             None
         """
        if self.controlPan.switch:
            self.controlPan.switch.disconnect()  # Assuming the switch object has a disconnect method
            self.statusbar.SetStatusText('Disconnected from the COM port')
            self.log_message("\nSuccessfully Disconnected COM Port...")
            # print("COM port disconnected.")
        else:
            wx.MessageBox("\nNo COM port is currently connected.", "Disconnect", wx.OK | wx.ICON_INFORMATION)


class UiApp(wx.App):
    """
    UiApp wx.App object has been created in order to ensure 
    that the gui platform and wx Widgets have been fully initialized.
    """
    def OnInit(self):
        frame = UiMainFrame(parent=None, title="MCCI - Model2450 UI")
        self.SetTopWindow(frame)
        return True

def run():
    """
    Enty point of the application which initialise the UiApp Class
    
    Args: None
    Returns: None
    """
    app = UiApp(False)
    app.MainLoop()
