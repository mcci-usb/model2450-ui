##############################################################################
# 
# Module: logwindow.py
#
# Description:
#     view the device log.
#
# Author:
#     Vinay N, MCCI Corporation Aug 2024
#
# Revision history:
#     V1.0.0 Mon Aug 12 2024 01:00:00   Vinay N 
#       Module created

##############################################################################
# Lib imports
import wx

# Own modules
from uiGlobal import *
from datetime import datetime

class LogWindow(wx.Window):
    """
    A class logWindow with init method

    To show the all actions while handling ports of devices 
    """
    def __init__(self, parent, top):
        """
        logWindow values displayed for all Models 3201, 3141,2101 
        Args:
            self: The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
            parent: Pointer to a parent window.
            top: creates an object
        Returns:
            None
        """
        wx.Window.__init__(self, parent)
        # SET BACKGROUND COLOUR TO White
        self.SetBackgroundColour("White")

        self.top = top
        # Create static box with naming of Log Window
        sb = wx.StaticBox(self, -1,"Log Window")
        

        # Create StaticBoxSizer as vertical
        self.vbox = wx.StaticBoxSizer(sb, wx.VERTICAL)

        
        
        self.btn_save = wx.Button(self, ID_BTN_AUTO, "Save",
                                        size=(60, -1))  
        self.btn_clear = wx.Button(self, ID_BTN_CLEAR, "Clear",
                                         size=(60, 25))
        
        # set tooltip for switching interval and auto buttons.
        self.btn_save.SetToolTip(wx.
                      ToolTip("Save Log content into a text file"))
        
        self.btn_clear.SetToolTip(wx.
                      ToolTip("Clear the Logs"))
        
        
        self.scb = wx.TextCtrl(self, -1, style= wx.TE_MULTILINE | wx.TE_READONLY, size=(-1,-1))
        self.scb.SetEditable(False)
        self.scb.SetBackgroundColour((255,255,255))
        
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        
        self.hbox.Add(self.btn_clear, 0, flag=wx.RIGHT ,border = 30)
 
        self.hbox.Add(self.btn_save,1 , flag=wx.RIGHT , border = 180)
        
        # Bind the button event to handler
        self.btn_clear.Bind(wx.EVT_BUTTON, self.ClearLogWindow)
        self.btn_save.Bind(wx.EVT_BUTTON, self.SaveLogWindow)
        
        self.szr_top = wx.BoxSizer(wx.VERTICAL)
        
        self.szr_top.AddMany([
            (5,0,0),
            (self.scb, 1, wx.EXPAND),
            (5,0,0)
            ])
        
        self.vbox.AddMany([
            (40,5,0),
            (self.hbox, 0, wx.ALIGN_LEFT),
            (10,5,0),
            (self.szr_top, 1, wx.EXPAND),
            (0,0,0)
            ])
        
        self.SetSizer(self.vbox)
        self.vbox.Fit(self)
        self.Layout()
        
    def log_message(self, message):
        """
        print the data in Logwindow
        Args:
            self: The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
            strin: USB device list in String format.
        Returns:
            None
        """
        self.scb.AppendText(message)
    
    def ClearLogWindow(self, e):
        """
        Event handler for Clear button
        Clear the data in USB Device Tree View Window

        Args:
            self: The self parameter is a reference to the current 
            insance of the class,and is used to access variables
            that belongs to the class.
            e: Type of the event
        Returns:
            None
        """
       
        self.scb.SetValue("")
    
    def SaveLogWindow(self, e):
        """
        Event handler for the save button
        Save the usb tree view Window content in a file under a directory

        Args:
            self: The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
            e: Type of the event
        Returns:
            None
        """
        
        # Get the content of the control
        content = self.scb.GetValue()
        self.save_file(content, "*.txt")
        
    
    def save_file (self, contents, extension):
        """
        Export the LogWindow/USBTreeWindow content to a file
        Called by LogWindow and USB Tree View Window

        Args:
            self:The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
        Returns: 
            return- success for file save in directiry
        """
        # Save a file
        self.dirname=""
        dlg = wx.FileDialog(self, "Save as", self.dirname, "", extension, 
                            wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            wx.BeginBusyCursor()

            dirname = dlg.GetDirectory()
            filename = os.path.join(dirname, dlg.GetFilename())

            if (os.path.isdir(dirname) and os.access(dirname, os.X_OK | 
                                                     os.W_OK)):
                self.dirname = dirname
            try:
                f = open(filename, 'w')
                f.write(contents)
                f.close()
            except IOError:
                options = wx.OK | wx.ICON_ERROR
                dlg_error = wx.MessageDialog(self,
                                           "Error saving file\n\n" + strerror,
                                           "Error",
                                           options)
                dlg_error.ShowModal()
                dlg_error.Destroy()

        dlg.Destroy()

        if (wx.IsBusy()):
            wx.EndBusyCursor()
        return
