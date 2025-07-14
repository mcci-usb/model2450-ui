
##############################################################################
# 
# Module: aboutDialog.py
#
# Description:
#      Dialog to display copyright information
#
# Author:
#     Vinay N, MCCI Corporation May 2025
#
# Revision history:
#     V2.0.0 Mon May 2025 01:00:00   Vinay N 
#       Module created
##############################################################################
import wx

from uiGlobal import *

#======================================================================
# COMPONENTS
#======================================================================

class AboutWindow(wx.Window):
    """
    A  class AboutWindow with init method
    The AboutWindow navigate to MCCI Logo with naming of 
    application UI "Criket",Version and copyright info.  
    """
    def __init__ (self, parent, top):
        """
        AboutWindow that contains the about dialog elements.

        Args:
            self: The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
            parent: Pointer to a parent window.
            top: creates an object
        Returns:
            None
        """
        wx.Window.__init__(self, parent, -1,
                           size=wx.Size(100,100),
                           style=wx.CLIP_CHILDREN,
                           name="About")

        self.top = top

        bmp = wx.Image("./icons/mcci_logo_about.png").ConvertToBitmap()
        self.image = wx.StaticBitmap(self, ID_ABOUT_IMAGE, bmp,
                                     wx.DefaultPosition, wx.DefaultSize)

        self.text = [ wx.StaticText(self, -1, VERSION_NAME),
                      wx.StaticText(self, -1, VERSION_ID ),
                      wx.StaticText(self, -1,  VERSION_STR),
                      wx.StaticText(self, -1, VERSION_COPY),
                      wx.StaticText(self, -1, "All rights reserved.\n\n")
                    ]
        self.image.Bind(wx.EVT_LEFT_UP, self.OnClick)
        for i in self.text:
            #i.SetBackgroundColour('White')
            i.Bind(wx.EVT_LEFT_UP, self.OnClick)
        self.Bind(wx.EVT_LEFT_UP, self.OnClick)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        # Define layout
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        widgets = [ (self.image, 1, wx.EXPAND) ]
        for i in self.text:
            widgets.extend([ (i, 0, wx.CENTER) ])
        
        self.sizer.AddMany(widgets)

        self.SetSizerAndFit(self.sizer)
        self.SetAutoLayout(True)

    def OnClick (self, evt):
        """
        OnClick() event handler function retrieves the label of 
        source button, which caused the click event. 
        That label is printed on the console.

        Args:
            self: The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
            evt: The event parameter in the OnClick() method is an 
            object specific to a particular event type.
        Returns:
            None        
        """
        self.GetParent().OnOK(evt)

    def OnSize (self, evt):
        """
        OnSize() event handler function retrieves the about window size. 

        Args:
            self: The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
            evt: The event parameter in the OnClick() method is an 
            object specific to a particular event type.
        Returns:
            None        
        """
        self.Layout()
        
class AboutDialog(wx.Dialog):
    """
    wxWindows application must have a class derived from wx.Dialog.
    """
    def __init__ (self, parent, top):
        """
        A AboutDialog is Window an application creates to 
        retrieve Cricket UI Application input.

        Args:
            self: The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
            parent: Pointer to a parent window.
            top: create a object
        Returns:
            None
        """
        wx.Dialog.__init__(self, parent, -1, "About",
                           size=wx.Size(100, 100),
                           style=wx.STAY_ON_TOP|wx.DEFAULT_DIALOG_STYLE,
                           name="About Dialog")

        self.top = top
        self.win = AboutWindow(self, top)

        self.Fit()
        self.CenterOnParent(wx.BOTH)

    def OnOK (self, evt):
        """
        OnOK() event handler function retrieves the label of 
        source button, which caused the click event. 

        Args:
            self: The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
            evt: The event parameter in the OnOK() method is an 
            object specific to a particular event type.
        Returns:
            None        
        """
        self.EndModal(wx.ID_OK)

    def OnSize (self, evt):
        """
        OnSize() event handler function retrieves the about window size. 
        
        Args:
            self: The self parameter is a reference to the current 
            instance of the class,and is used to access variables
            that belongs to the class.
            evt: The event parameter in the OnSize() method is an 
            object specific to a particular event type.
        Returns:
            None        
        """ 
        self.Layout()