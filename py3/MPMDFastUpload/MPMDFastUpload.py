import wx
import os
import glob
# import _thread
from threading import Thread
from M34_sendBinGcode import M34_sendBinGcode
from binGcode.binGcode import *
from binGcode.encodeBinGcode import encodeGcodeFile
# from binGcode.encodeBinGcode import encodeGcodeFile
# from binGcode.binGcode import *
import wx.lib.agw.supertooltip as STT
if os.name == "nt":
    try:
        import winreg
    except:
        pass
BAUDRATE=460800
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # base_path = sys._MEIPASS
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        # base_path = os.path.abspath(".")
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

class WorkerThread(Thread):
    def __init__(self, notify_window,progHandle,filepath,comport) :
        Thread.__init__(self)
        self._notify_window = notify_window
        self_want_abort = 0
        self.progHandle = progHandle
        self.filepath = filepath
        self.comport = comport
    def run(self) :
        # M35_sendBinGcode(None,BAUDRATE,self.filename,self.comList.GetValue(),progHandle=self.onProg)
        M34_sendBinGcode(None,BAUDRATE,self.filepath,comport=self.comport,progHandle=self.progHandle,linetimeout=0,linetimeoutmod=50)
    def abort(self) :
        self._want_abort = 1
class MyFrame(wx.Frame) :
    def __init__(self,parent,title) :
        self.dirname = ''
        self.filename = ''
        self.comports = ['COM1','COM2','COM3','COM4']
        wx.Frame.__init__(self,parent,style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX),title=title,size=(400,450))
        self.comList = wx.ComboBox(self,value=self.comports[0],choices=self.comports,size=(200,48))
        # self.refButton = wx.BitmapButton(self,bitmap=wx.ArtProvider.GetBitmap(wx.ART_REFRESH,size=(48,48)))
        # refButton = wx.Button(self,id=wx.ID_REFRESH,style=wx.BU_NOTEXT)
        refButton = wx.BitmapButton(self,style=wx.BU_NOTEXT,bitmap=wx.ArtProvider.GetBitmap(wx.ART_PLUS ),size=(24,24))
        # refButton.SetBitmapPosition(wx.LEFT)
        openButton = wx.Button(self,label='Open')
        uploadButton = wx.Button(self,label='Upload')
        titleLabel = wx.StaticText(self,label='MPMD Fast Uploader',style=wx.ALIGN_CENTRE_HORIZONTAL,size=(-1,90))
        # titleLabel.SetLabelMarkup("<b>&ampBed</b> <span foreground='red'>breakfast</span>")
        titleLabel.SetFont(wx.Font(30,wx.FONTFAMILY_DEFAULT,wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD))
        # titleImage = wx.Image(40,80,False)
        # titleImage.LoadFile('mpmd.png',wx.BITMAP_TYPE_PNG)
        titleBMP = wx.Bitmap(40,80)
        titleBMP.LoadFile(resource_path('mpmd.png'),wx.BITMAP_TYPE_PNG)
        titleImage = wx.StaticBitmap(self,bitmap=titleBMP)
        # titleImage = wx.StaticBitmap(40,80,depth=wx.BITMAP_SCREEN_DEPTH)
        # titleImage.LoadFile('mpmd.png',wx.BITMAP_TYPE_PNG)
        self.progBar = wx.Gauge(self,range=100,size=(350,24))
        self.fileLabel = wx.StaticText(self,label='',style=wx.ALIGN_CENTRE_HORIZONTAL | wx.ST_NO_AUTORESIZE | wx.ST_ELLIPSIZE_START)  
        self.checkBox = wx.CheckBox(self,label='binaryEncode?')
        #make tooltip for binary encode checkbox
        tip = STT.SuperToolTip("Encodes gcode files in a binary format \nwhich can reduce file sizes by 2-3x")
        tip.ApplyStyle('Beige')
        tip.SetMiddleGradientColor(tip.GetTopGradientColor())
        tip.SetBottomGradientColor(tip.GetTopGradientColor())
        # tip.SetHeader("Hello World")
        tip.SetTarget(self.checkBox)
        #bind buttons to events
        self.Bind(wx.EVT_BUTTON, self.OnRefresh, refButton)
        self.Bind(wx.EVT_BUTTON, self.OnOpen, openButton)
        self.Bind(wx.EVT_BUTTON, self.OnUpload,uploadButton)
        self.Bind(wx.EVT_CHECKBOX,self.onCheck,self.checkBox)
        #set up sizers
        topSizer = wx.BoxSizer(wx.VERTICAL)
        row1Sizer = wx.BoxSizer(wx.HORIZONTAL)
        row2Sizer = wx.BoxSizer(wx.HORIZONTAL)
        #row1, COMPORT + refresh
        row1Sizer.AddStretchSpacer()
        row1Sizer.Add(self.comList,flag=wx.ALL | wx.CENTER | wx.FIXED_MINSIZE,border=4)
        row1Sizer.Add(refButton,flag=wx.ALL | wx.CENTER | wx.FIXED_MINSIZE,border=4)
        row1Sizer.AddStretchSpacer()
        #row2, Open + upload buttons
        row2Sizer.Add(openButton,flag=wx.ALL | wx.CENTER | wx.FIXED_MINSIZE,border=4)
        row2Sizer.Add(uploadButton,flag=wx.ALL | wx.CENTER | wx.FIXED_MINSIZE,border=4)
        row2Sizer.Add(self.checkBox,flag=wx.ALL | wx.CENTER | wx.FIXED_MINSIZE,border=4)
        #row3, progbar
        topSizer.Add(titleLabel,0,flag = wx.ALL | wx.CENTER,border=4)
        topSizer.Add(titleImage,0,flag = wx.ALL | wx.CENTER,border=4)
        topSizer.Add(row1Sizer,0,flag=wx.ALL | wx.CENTER | wx.FIXED_MINSIZE,border=4)
        topSizer.Add(row2Sizer,0,flag=wx.ALL | wx.CENTER | wx.FIXED_MINSIZE,border=4)
        topSizer.Add(self.fileLabel,0,flag=wx.EXPAND)
        # topSizer.Add(self.fileLabel,0,flag=wx.ALL | wx.CENTER | wx.FIXED_MINSIZE,border=4)
        topSizer.Add(self.progBar,0,flag=wx.ALL | wx.EXPAND,border=4)
        topSizer.AddStretchSpacer()
        #assign topsizer
        self.SetSizer(topSizer)
        # topSizer.Fit(self)
        self.OnRefresh(None)
        self.Show(True)
    def OnRefresh(self,event) :
        self.comports = self.scanserial()
        self.comports.sort()
        print(self.comports)
        try:
            self.comList.Set(self.comports)
            self.comList.SetValue(self.comports[0])
        except:
            self.comList.Set([])
            self.comList.SetValue('')            
            pass
    def OnUpload(self,event) :
        # try :
        # print([self.comList.GetValue(),BAUDRATE,self.filename])
        # _thread.start_new_thread(M35_sendBinGcode(None,BAUDRATE,self.filename,self.comList.GetValue(),progHandle=self.onProg))
        self.worker = WorkerThread(self,self.onProg,self.filename,self.comList.GetValue())
        wx.CallAfter(self.worker.start)
        # except:
            # pass
        # self.progBar.SetValue(self.progBar.GetValue()+5)
        # print(self.progBar.GetValue())
    def OnOpen(self,event) :
        self.filename = wx.FileSelector('Choose file',self.dirname,'',wildcard='*.gcode;*.g;*.gco;*.bgc',flags=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
        self.fileLabel.SetLabelText(self.filename)
        if(self.checkBox.IsChecked()) :
            fileext = self.filename.rsplit('.',1)[1]
            if(fileext in ['gcode','g','gco']) :
            # try :
                path_out = self.filename.rsplit('.',1)[0]+'.bgc'
                print(path_out)
                encodeGcodeFile(self.filename,path_out)
                self.filename = path_out
                self.fileLabel.SetLabelText(self.filename)
                print(self.filename)
            # except :
                # pass
        # dlg = wx.FileDialog(self, "Choose file", self.dirname, "", "*.txt", wx.FD_OPEN)
        # if dlg.ShowModal() == wx.ID_OK :
            # self.filename = dlg.GetFilename()
            # self.dirname = dlg.GetDirectory()
            # f = open(os.path.join(self.dirname,self.filename),'r')
            # self.control.SetValue(f.read())
            # f.close()
        # dlg.Destroy()        
        pass
    def OnDnD(self,event) :
        pass
    def onProg(self,value) :
        print(value)
        wx.CallAfter(self.progBar.SetValue,value*100)
        # self.progBar.SetValue(value)
        self.Refresh()
        self.Update()
        app.Yield()
        pass
    def onCheck(self,value) :
        if(value) :
            fileext = self.filename.rsplit('.',1)[1]
            if(fileext in ['gcode','g','gco']) :
                path_out = self.filename.rsplit('.',1)[0]+'.bgc'
                print(path_out)
                encodeGcodeFile(self.filename,path_out)
                self.filename = path_out
                self.fileLabel.SetLabelText(self.filename)
                print(self.filename)                
    def scanserial(self):
        """scan for available ports. return a list of device names."""
        baselist = []
        if os.name == "nt":
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "HARDWARE\\DEVICEMAP\\SERIALCOMM")
                i = 0
                while(1):
                    baselist += [winreg.EnumValue(key, i)[1]]
                    i += 1
            except:
                pass

        for g in ['/dev/ttyUSB*', '/dev/ttyACM*', "/dev/tty.*", "/dev/cu.*", "/dev/rfcomm*"]:
            baselist += glob.glob(g)
        return [p for p in baselist if self._bluetoothSerialFilter(p)]

    def _bluetoothSerialFilter(self, serial):
        return not ("Bluetooth" in serial or "FireFly" in serial)        

app = wx.App(False)
frame = MyFrame(None,'MPMD Fast Uploader')
app.MainLoop()

