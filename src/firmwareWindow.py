
##############################################################################
# 
# Module: firmwarewindow.py
#
# Description:
#      Update the firmware file.
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
import devControl
from model2450lib.serial import searchmodelboot
from model2450lib.serial import models2450

import serial.tools.list_ports
import os
import sys

ID_TC_GET_VERSION = 1000
ID_BTN_GET_VERSION = 1001

DO_RESET         = 1
INIT_AVR_PORT = 2
READ_AVAIL_PORTS = 3
GET_SW_IDENTIFIER = 4
GET_PROG_TYPE = 5
GET_SW_VERSION = 6
CHECK_AUTO_INC = 7
CHECK_BLOCK_SUPPORT = 8
GET_DEV_CODE = 9
SELECT_DEV_TYPE = 10
GET_INTO_PROGMODE = 11
READ_DEV_SIGNATURE = 12
READ_LFUSE = 13
READ_HFUSE = 14
READ_EFUSE = 15
SET_ADDRESS = 16
WRITE_BLOCK = 17
LEAVE_PROGMODE = 18
EXIT_BOOTLOADER = 19

CMD_GET_SWIDENTIFIER = 'S'  # 0x53
CMD_GET_SWVERSION = 'V'     # 0x56
CMD_GET_PROGTYPE = 'p'      # 0x53
CMD_CHECK_AUTOINCR = 'a'    # 0x61
CMD_CHECK_BLOCKSUPP = 'b'   # 0x62
CMD_GET_DEVCODE = 't'       # 0x74
CMD_GET_PROGMODE = 'P'      # 0x50
CMD_READ_DEVSIG = 's'       # 0x73     # 's'
CMD_READ_LFUSE = 'F'        # 0x46      # 'F'
CMD_READ_HFUSE = 'N'        # 0x4E      # 'N'
CMD_READ_EFUSE = 'Q'        # 0x51      # 'Q'
CMD_LEAVE_PROGMODE = 'L'    # 0x4C
CMD_EXIT_BOOTLOADER = 'E'   # 0x45


CMD_SET_ADDRESS = 0x41     # 'A'
CMD_WRITE_FLASH = 0x42     # 'B'
CMD_READ_FLASH = 0x67      # 'g'
CMD_LEAVE_PROGMODE = 0x4C  # 'C

# class FirmwareUpdate(wx.PyEvent):
class FirmwareUpdate(wx.PyEvent):
    def __init__(self, data):
        
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data


class FirmwarePanel(wx.Panel):
    def __init__(self, parent, log_window, device=None):
        super(FirmwarePanel, self).__init__(parent)
        self.SetBackgroundColour("White")
        self.parent = parent
        self.device = device
        self.log_window = log_window
        
        self.wait_flg = True

        self.fw_seq = None
        self.fw_port = None
        self.sw = None

        self.avrHand = None
        self.rx_flg = False
        self.pageSize = 0
        self.hexPath = None
        self.mem_flash = {}
        self.mem_addr = []
        self.flash_addr = 0
        self.byte_addr = 0
        self.flash_flg = False

        self.dlist = []
        self.clist = []
        self.modellist = []
        self.addmodellist = []
        self.dlist = "COM3"


        vbox = wx.BoxSizer(wx.VERTICAL)

        # --- Top Section: Model Selection ---
        self.szr_top = wx.BoxSizer(wx.HORIZONTAL)
        self.st_Sw = wx.StaticText(self, -1, "Select Model")
        self.fst_lb = wx.ComboBox(self, size=(110, -1))
        self.btn_scan = wx.Button(self, -1, "Search", size=(77, 25))
        self.szr_top.Add(self.st_Sw, 0, wx.ALL | wx.CENTER, 5)
        self.szr_top.AddSpacer(30)  # This will add the 20px gap
        self.szr_top.Add(self.fst_lb, 0, wx.ALL, 5)
        self.szr_top.Add(self.btn_scan, 0, wx.ALL, 5)

        # --- Middle Section: Hex File Selection self.port_text.Select(0)  # Select the first port in the list---
        self.szr_load = wx.BoxSizer(wx.HORIZONTAL)
        self.st_seqname = wx.StaticText(self, -1, "Browse the hex file")
        self.tc_bloc = wx.TextCtrl(self, -1, size=(250, -1), 
                                   style=wx.TE_CENTRE | wx.TE_PROCESS_ENTER)
        self.btn_load = wx.Button(self, -1, "Load", size=(60, 25))
        self.szr_load.Add(self.st_seqname, 0, wx.ALL | wx.CENTER, 5)
        self.szr_load.Add(self.tc_bloc, 0, wx.ALL, 5)
        self.szr_load.Add(self.btn_load, 0, wx.ALL, 5)

        # --- Bottom Section: Update / Cancel Buttons ---
        self.szr_update = wx.BoxSizer(wx.HORIZONTAL)
        self.st_mty = wx.StaticText(self, -1, " ")  # Optional: You can remove this if you don't want extra space
        self.btn_up_start = wx.Button(self, -1, "Update", size=(70, 25))
        self.btn_cancel = wx.Button(self, -1, "Cancel", size=(70, 25))

        # Add the buttons and align them to the center
        self.szr_update.Add(self.st_mty,  0, wx.ALL | wx.ALIGN_CENTER, 5)  # This can be removed if not needed
        self.szr_update.AddSpacer(95)  # This will add the 20px gap
        self.szr_update.Add(self.btn_up_start, 0, wx.ALL | wx.ALIGN_CENTER, 5)
        # Add spacer with a width of 20 pixels
        self.szr_update.AddSpacer(20)  # This will add the 20px gap
        self.szr_update.Add(self.btn_cancel, 0, wx.ALL | wx.ALIGN_CENTER, 5)


        # --- Version Display ---
        self.version_text = wx.StaticText(self, label="Version (F:H):    No version")

        # --- Add to Main Vertical BoxSizer ---
        vbox.Add(self.version_text, 0, wx.ALL, 10)
        vbox.Add(self.szr_top, 0, wx.EXPAND | wx.ALL, 5)
        vbox.Add(self.szr_load, 0, wx.EXPAND | wx.ALL, 5)
        
        vbox.Add(self.szr_update, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(vbox)

        # Event Bindings
        self.btn_load.Bind(wx.EVT_BUTTON, self.LoadBatch)
        self.btn_scan.Bind(wx.EVT_BUTTON, self.ScanDevice)
        self.btn_up_start.Bind(wx.EVT_BUTTON, self.update_start)
        self.btn_cancel.Bind(wx.EVT_BUTTON, self.update_cancel)
        
        # The Timer class allows you to execute code at specified intervals.
        self.timer_lp = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.SearchTimer, self.timer_lp)
        
        self.timer_fu = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.FwUpdateTimer, self.timer_fu)
        
        EVT_RESULT(self, self.SearchEvent)

        if self.device:
            self.update_version()

    def update_version(self):
        """Fetch the version from the device and update the StaticText."""
        if self.device:
            try:
                version = self.device.get_version()
                # print("Version(F:H):", version)
                self.version_text.SetLabel(f"Version (F:H):   {version}")
            except Exception as e:
                self.version_text.SetLabel(f"Error fetching version: {str(e)}")
        else:
            self.version_text.SetLabel("Device not connected")

    def set_device(self, device):
        """Set the device and update the version."""
        self.device = device
        self.update_version()
    
    def ScanDevice(self, evt):
        wx.PostEvent(self, FirmwareUpdate("print"))
        wx.PostEvent(self, FirmwareUpdate("search"))
        wx.BeginBusyCursor()
    
    def clear_device(self):
        """Clear the device and version information."""
        self.device = None
        self.version_text.SetLabel("Version (F:H):    No version")

    def SearchTimer(self, evt):
        wx.PostEvent(self, FirmwareUpdate("search"))
        self.timer_lp.Stop()
   
    def load_file(self):
        self.dirname=""
        dlg = wx.FileDialog(self, "Load File", self.dirname, "", "*.hex", 
                                wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        
        if dlg.ShowModal() == wx.ID_CANCEL:
            return
        
        pathname = dlg.GetPath()
        self.tc_bloc.SetValue(pathname)
        try:
            self.mappedSw = {}
            self.main_flg = False
            self.end_flg = False
            self.finseq = []
            if os.path.exists(pathname):
                with open(pathname) as fobj:
                    for line in fobj:
                        pass
        except IOError:
            wx.LogError("Can not open file '%s', " % pathname)
        return pathname
    
    
    def SearchEvent(self, event):
        if event.data is None:
            print("No Search event\n")
            # self.top.print_on_log("No Search event\n")
        elif event.data == "search":
            #self.btn_scan.Enable(False)
            self.btn_scan.Unbind(wx.EVT_BUTTON)
            # self.get_devices()
            self.get_boot()
            wx.GetApp().Yield()
            self.btn_scan.Bind(wx.EVT_BUTTON, self.ScanDevice)
        elif event.data == "print":
            self.log_window.log_message("\nSearching Devices ...")
    
    def get_boot(self):
        b = searchmodelboot.find_switch()
        
        if (wx.IsBusy()):
            wx.EndBusyCursor()
        self.fst_lb.Clear()
        self.fst_lb.Append(b)
        self.fst_lb.SetSelection(0)
            
    def get_devices(self):    
        # devlist = get_models()
        devlist = devControl.search_device()
        print("dev :", devlist)
        print(devlist)
        if (wx.IsBusy()):
            wx.EndBusyCursor()

        dev_list = devlist["models"]
        if(len(dev_list) == 0):
            # self.top.print_on_log("No Devices found\n")
            self.log_window.log_message("\nNo Devices found")
            self.fst_lb.Clear()
        else:
            key_list = []
            val_list = []

            nlist = []
            
            for i in range(len(dev_list)):
                key_list.append(dev_list[i]["port"])
                val_list.append(dev_list[i]["model"])
            
            self.fst_lb.Clear()

            for i in range(len(val_list)):
                str1 = val_list[i]+"("+key_list[i]+")"
                if val_list[i] == '2450' or val_list[i] == '2450':
                    self.fst_lb.Clear()
                    nlist.append(val_list[i]+"("+key_list[i]+")")
                    self.fst_lb.Append(nlist)
                    self.fst_lb.SetSelection(0)
    
    
    def FwUpdateTimer(self, evt):
        self.timer_fu.Stop()
        if self.fw_seq == DO_RESET:
            self.sw.do_reset()
            self.fw_seq = READ_AVAIL_PORTS
            self.timer_fu.Start(1500)
        elif self.fw_seq == READ_AVAIL_PORTS:
            plist = devControl.get_avail_ports(self)
            self.fw_port = self.get_avrdude(plist)
            if self.fw_port != None:
                self.fw_seq = INIT_AVR_PORT
                self.timer_fu.Start(500)
            else:
                print("No AVRdude found!!")
        elif self.fw_seq == INIT_AVR_PORT:
            if self.open_avr_port():
                self.get_sw_identifier()
                self.timer_fu.Start(500)
        elif self.fw_seq == GET_SW_IDENTIFIER:
            if self.parse_sw_identifier():
                self.get_programmer_type()
                self.timer_fu.Start(100)
        elif self.fw_seq == GET_PROG_TYPE:
            if self.parse_programmer_type():
                self.get_sw_version()
                self.timer_fu.Start(100)
        elif self.fw_seq == GET_SW_VERSION:
            if self.parse_sw_version():
                self.check_auto_incr()
                self.timer_fu.Start(100)
        elif self.fw_seq == CHECK_AUTO_INC:
            if self.parse_auto_incr():
                self.check_block_support()
                self.timer_fu.Start(100)
        elif self.fw_seq == CHECK_BLOCK_SUPPORT:
            if self.parse_block_support():
                self.get_dev_code()
                self.timer_fu.Start(100)
        elif self.fw_seq == GET_DEV_CODE:
            if self.parse_dev_code():
                self.select_dev_type()
                self.timer_fu.Start(100)
        elif self.fw_seq == SELECT_DEV_TYPE:
            if self.parse_dev_type():
                self.get_into_progmode()
                self.timer_fu.Start(100)
        elif self.fw_seq == GET_INTO_PROGMODE:
            if self.parse_get_progmode():
                self.read_dev_signature()
                self.timer_fu.Start(100)
        elif self.fw_seq == READ_DEV_SIGNATURE:
            if self.parse_dev_signature():
                self.read_lfuse()
                self.timer_fu.Start(100)
        elif self.fw_seq == READ_LFUSE:
            if self.parse_lfuse():
                self.read_hfuse()
                self.timer_fu.Start(100)
        elif self.fw_seq == READ_HFUSE:
            if self.parse_hfuse():
                self.read_efuse()
                self.timer_fu.Start(100)
        elif self.fw_seq == READ_EFUSE:
            if self.parse_efuse():
                if self.flash_flg:
                    self.flash_flg = False
                    self.leave_prog_mode()
                    self.timer_fu.Start(100)
                else: 
                    self.log_window.log_message(f"writing flash (" + str(len(self.mem_addr)) + ") bytes")
                    self.flash_addr = self.mem_addr[0]
                    self.byte_addr = self.mem_addr[0]
                    self.log_window.log_inline(".")
                
                    self.set_address()
                    self.timer_fu.Start(100)
        elif self.fw_seq == SET_ADDRESS:
            if self.parse_set_address():
                self.load_block_flash()
                self.timer_fu.Start(100)
        elif self.fw_seq == WRITE_BLOCK:
            if self.parse_set_address():
                if self.byte_addr <= len(self.mem_addr):
                    self.log_window.log_inline(".")
                    self.flash_addr += 0x40
                    self.set_address()
                    self.timer_fu.Start(100)
                else:
                    self.flash_flg = True
                    self.read_lfuse()
                    self.timer_fu.Start(100)
        elif self.fw_seq == LEAVE_PROGMODE:
            if self.parse_set_address():
                self.exit_boot_loader()
                self.timer_fu.Start(100)
        elif self.fw_seq == EXIT_BOOTLOADER:
            if self.parse_set_address():
                # self.top.print_on_log("Firmware update success!\n")
                self.log_window.log_message(f"Firmware update success!\n")
    
    def parse_set_address(self):
        resp = self.read_avr_oned()
        if resp == b'\r':
            return True
        else:
            self.log_window.log_message(f"Error when setting flash address\n")
            return False
    
    def parse_efuse(self):
        resp = self.read_avr_ba()
        if resp != None:
            # bsize = resp[0]
            bsize = (format(resp[0], '#x'))
            self.log_window.log_message(f"efuse reads as: "+str(bsize)+"\n")
            return True
        else:
            print("Error when reading efuse\n")
            return False
    
    def parse_hfuse(self):
        resp = self.read_avr_ba()
        if resp != None:
            # bsize = resp[0]
            bsize = (format(resp[0], '#x'))
            self.log_window.log_message(f"hfuse reads as: "+str(bsize)+"\n")
            return True
        else:
            print("Error when reading hfuse\n")
            return False
    
    def parse_lfuse(self):
        resp = self.read_avr_ba()
        if resp != None:
            # bsize = resp[0]
            bsize = (format(resp[0], '#x'))
            if self.flash_flg:
                print("\n")
            self.log_window.log_message(f"lfuse reads as: "+str(bsize)+"\n")
            return True
        else:
            print("Error when reading lfuse\n")
            return False
    
    def parse_dev_signature(self):
        resp = self.read_avr_ba()
        if resp != None:
            bsize1 = (format(resp[0], '#x'))
            bsize2 = (format(resp[1], '#x'))
            bsize3 = (format(resp[2], '#x'))
            # print("Device Signature = "+bsize1+bsize2+bsize3+"\n")
            self.log_window.log_message(f"Device Signature = "+bsize1+bsize2+bsize3+"\n")
            return True
        else:
            self.log_window.log_message(f"Error when reading dev signature\n")
            print("Error when reading dev signature\n")
            return False
    
    def parse_get_progmode(self):
        resp = self.read_avr_oned()
        if resp == b'\r':
            self.log_window.log_message(f"Enter into Program mode success\n")
            return True
        else:
            self.log_window.log_message(f"Error when entering into prog mode\n")
            return False
        
    def parse_dev_type(self):
        resp = self.read_avr_oned()
        if resp == b'\r':
            self.log_window.log_message(f"Dev code selected = 0x44\n")
            return True
        else:
            print("Error when checking the supported device list\n")
            self.log_window.log_message(f"Error when checking the supported device list\n")
            return False
    
    def parse_dev_code(self):
        resp = self.read_avr_ba()
        if resp != None:
            # bsize = resp[0]
            bsize = (format(resp[0], '#x'))
            self.log_window.log_message(f"Programmer supports the following devices: "+bsize+"\n")
            return True
        else:
            self.log_window.log_message(f"Error when checking the supported device list\n")
            return False
    
    def parse_block_support(self):
        resp = self.read_avr_ba()
        if resp != None:
            bsize = resp[1:3]
            bsize = bsize.hex()
            self.pageSize = bsize
            self.log_window.log_message(f"Programmer supports buffered memory access with buffer size = "+str(int(bsize, 16))+" bytes\n")
            return True
        else:
            self.log_window.log_message(f"Error when checking block support\n")
            return False

    def parse_auto_incr(self):
        resp = self.read_avr()
        if resp != None:
            if resp[0] == 'Y':
                self.log_window.log_message(f"Programmer supports auto addr increment\n")
            else:
                self.log_window.log_message(f"Programmer supports auto addr increment!\n")
            return True
        else:
            self.log_window.log_message(f"Error when checking auto addr incement support\n")
            return False
    
    def parse_sw_version(self):
        resp = self.read_avr()
        if resp != None:
            resp = int(resp, 16)
            resp = resp / 16
            self.log_window.log_message(f"Software Version = "+str(resp)+"\n")
            return True
        else:
            self.log_window.log_message(f"Software Version read error\n")
            return False

    def parse_programmer_type(self):
        resp = self.read_avr()
        if resp != None:
            self.log_window.log_message(f"Programmer Type:  "+resp+"\n")
            return True
        else:
            self.log_window.log_message(f"Programmer type not found\n")
            return False

    def parse_sw_identifier(self):
        resp = self.read_avr()
        if resp == "CATERIN":
            self.log_window.log_message(f" --------------   Firmware update   ------------------\n")
            self.log_window.log_message(f"Found Programmer Id = "+resp+"\n")
            return True
        else:
            self.log_window.log_message(f"Programmer Id read error = "+resp+"\n")
            return False
    
    def open_avr_port(self):
        try:
            self.avrHand = serial.Serial(
                port=self.fw_port,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            if self.avrHand.is_open:
                self.log_window.log_message(f"Opened port {self.fw_port}\n")
                return True
            else:
                self.log_window.log_message(f"Failed to open port {self.fw_port}\n")
                return False
        except Exception as e:
            self.log_window.log_message(f"Error opening port {self.fw_port}: {e}\n")
            return False
        
    def get_sw_identifier(self):
        self.rx_flg = True
        self.write_avr(CMD_GET_SWIDENTIFIER)
        self.fw_seq = GET_SW_IDENTIFIER
    
    def get_programmer_type(self):
        self.write_avr(CMD_GET_PROGTYPE)
        self.fw_seq = GET_PROG_TYPE
    
    def get_sw_version(self):
        self.write_avr(CMD_GET_SWVERSION)
        self.fw_seq = GET_SW_VERSION
    
    def get_dev_code(self):
        self.write_avr(CMD_GET_DEVCODE)
        self.fw_seq = GET_DEV_CODE
    
    def check_auto_incr(self):
        self.write_avr(CMD_CHECK_AUTOINCR)
        self.fw_seq = CHECK_AUTO_INC
    
    def check_block_support(self):
        self.write_avr(CMD_CHECK_BLOCKSUPP)
        self.fw_seq = CHECK_BLOCK_SUPPORT
    
    def get_dev_code(self):
        self.write_avr(CMD_GET_DEVCODE)
        self.fw_seq = GET_DEV_CODE
    
    def select_dev_type(self):
        self.write_avr_ba("TD")
        self.fw_seq = SELECT_DEV_TYPE
    
    def get_into_progmode(self):
        self.write_avr(CMD_GET_PROGMODE)
        self.fw_seq = GET_INTO_PROGMODE
    
    def read_dev_signature(self):
        self.write_avr(CMD_READ_DEVSIG)
        self.fw_seq = READ_DEV_SIGNATURE
    
    def read_efuse(self):
        self.write_avr(CMD_READ_EFUSE)
        self.fw_seq = READ_EFUSE

    def read_lfuse(self):
        self.write_avr(CMD_READ_LFUSE)
        self.fw_seq = READ_LFUSE

    def read_hfuse(self):
        self.write_avr(CMD_READ_HFUSE)
        self.fw_seq = READ_HFUSE
    
    def exit_boot_loader(self):
        self.write_avr('E')
        self.fw_seq = EXIT_BOOTLOADER
    
    def leave_prog_mode(self):
        self.write_avr('L')
        self.fw_seq = LEAVE_PROGMODE
    
    def set_address(self):
        addstr = (self.flash_addr).to_bytes(2, byteorder='big').hex()
        addbyte = bytes.fromhex(addstr)
        mybyte = []
        mybyte.append(0x41)
        for byte in addbyte:
            mybyte.append(byte)
        self.write_avr_hba(mybyte)

        self.fw_seq = SET_ADDRESS
    
    def load_block_flash(self):
        mybarr = []
        mybarr.append(0x42)
        mybarr.append(0x00)
        mybarr.append(0x80)
        mybarr.append(0x46)
        for i in range(128):
            try:
                mybarr.append(self.mem_flash[self.byte_addr])
            except:
                mybarr.append(0xFF)
            self.byte_addr += 1
        self.write_avr_hba(mybarr)
        self.fw_seq = WRITE_BLOCK
        
    def read_avr_ba(self):
        rxdata = None
        try:
            rxdata = self.avrHand.read(10)
        except serial.SerialException as serr:
            print("\nIssue in Serial port: ", serr)
        return rxdata

    def read_avr_oned(self):
        rxdata = None
        try:
            rxdata = self.avrHand.read(1)
        except serial.SerialException as serr:
            self.log_window.log_message(f"Issue in Serial port: "+str(serr)+"\n")
            # self.top.print_on_log("Issue in Serial port: "+str(serr)+"\n")
        return rxdata

    def read_avr(self):
        rxdata = None
        try:
            rxdata = self.avrHand.readline()
            try:
                rxdata = rxdata.rstrip().decode('utf-8')
            except:
                self.log_window.log_message("\nSerial Parsing Error")
                # print("Serial Parsing Error\n")
        except serial.SerialException as serr:
            self.log_window.log_message("\nIssue in Serial port: ", serr)
            # print("Issue in Serial port: ", serr)
        return rxdata
    
    def write_avr_hba(self,param):
        ba = bytearray(param)
        try:
            self.avrHand.write(ba)
        except serial.SerialException as serr:
            print(serr)

    def write_avr_ba(self,param):
        ba = bytearray(param.encode())
        try:
            self.avrHand.write(ba)
        except serial.SerialException as serr:
            print(serr)

    def write_avr(self,param):
        try:
            self.avrHand.write(param.encode())
        except serial.SerialException as serr:
            print(serr)

    def get_avrdude(self, plist):
        for port in plist:
            if sys.platform == "win32": 
                hwid = port[0]
                strlst = hwid.split('SER')[1].split('LOCATION')[0].rstrip(' ')
                if len(strlst) == 1 and '=' in strlst:
                    return port[1]
            else:
                if port[2].rstrip(' ') == "USB IO board":
                    return port[1]
        return None

    # Dummy Event Handlers (You will define them later)
    def updateBatchLocation(self, pathname):
        self.hexPath = pathname
        
    def LoadBatch(self, event):
        pathname = self.load_file()
        self.updateBatchLocation(pathname)


    def get_selected_com(self):
        """
        Get the selected COM port from the list box.
        Expected format: "COM3 (Description)" so we return the part inside the parentheses.
        If the format is not as expected but the string starts with "COM", return the entire string.
        If nothing is selected, assume boot mode.
        """
        scval = self.fst_lb.GetValue().strip()
        if not scval:
            # No value selected; assume device is in boot mode and start firmware update process.
            self.fw_seq = READ_AVAIL_PORTS
            self.timer_fu.Start(500)
            return ""

        # If the string contains parentheses, extract the part inside.
        if "(" in scval and ")" in scval:
            # self.top.print_on_log("firmware update started here device is in Normal mode!")
            txt = scval.split("(")
            if len(txt) > 1:
                return txt[1].replace(")", "").strip()
        else:
            # self.top.print_on_log("firmware update started here device in boot mode!")
            self.fw_seq = READ_AVAIL_PORTS  # Assuming self.fw_seq is defined in your context.
            self.timer_fu.Start(500)        # And self.timer_fu is available.
            # return scval
            return ""
      
        # Otherwise, log the issue and return an empty string.
        return ""
    
    def update_start(self, event):
        self.bloc = self.tc_bloc.GetValue()
        if os.path.exists(self.bloc):
            if not self.validate_hex_file(self.bloc):
                title = ("3141/3142 Firmware upload")
                msg = ("Please select a valid hex file!")
                dlg = wx.MessageDialog(self, msg, title, wx.OK)
                dlg.ShowModal()
            else:
                self.unpack_hex_file(self.bloc)
                self.mem_addr = list(self.mem_flash.keys())
                self.mem_addr.sort()
                selcom = self.get_selected_com()
                if not selcom:
                    self.fw_seq = READ_AVAIL_PORTS
                    self.timer_fu.Start(500)
                    return
                self.sw = models2450.Models2450(selcom)
                
                if(self.sw.connect()):
                    self.fw_seq = DO_RESET
                    self.timer_fu.Start(1000)

    def update_cancel(self, event):
        """
        Simple cancel function for firmware update.
        Stops the update timer, disconnects the device, and resets the UI.
        """
        self.log_window.log_message("\n Cancelled Firmware update !")

        # Stop the timer if running
        if self.timer_fu.IsRunning():
            self.timer_fu.Stop()
            # print("Timer stopped.")

        # Disconnect the device if connected
        try:
            if self.sw:
                self.sw.disconnect()
                self.log_window.log_message("\n Model2450 Disconnected !")
        except Exception as e:
            print(f"Error while disconnecting: {e}")

        # Reset UI buttons
        self.btn_up_start.Enable(True)
        self.btn_cancel.Enable(True)


    
    # def update_cancel(self, event):
    #     self.fw_seq = READ_AVAIL_PORTS
    #     self.timer_fu.Start(500)
        
    def unpack_hex_file(self, hfloc):
        lines = tuple(open(hfloc, "r"))

        self.mem_flash = {}
        for line in lines:
            self.unpack_line(line)
            
    def unpack_line(self, line):
        if line[0] == ":" and line[-1] == "\n":
            data_len = int(line[1:3], 16)
            addr_hex = int(line[3:7], 16)
            data_type = int(line[7:9], 16)
            data_str = line[9:-3]

            if data_len * 2 == len(data_str) and data_type == 0:
                barr = bytearray.fromhex(data_str)

                for bhex in barr:
                    self.mem_flash[addr_hex] = bhex
                    addr_hex += 1
                       
    def validate_hex_file(self, hfloc):
        lines = tuple(open(hfloc, "r"))
        status = False
        for line in lines:
            if line[0] == ":" and line[-1] == "\n":
                status = True
            else:
                return False
        return status

def EVT_RESULT(win, func):
        win.Connect(-1, -1, EVT_RESULT_ID, func)