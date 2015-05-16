import socket
import time
import sys
import thread
import threading
import signal
import curses
import commands
import re
import SocketServer
import BaseHTTPServer
import os
#sys.path.append('./lib/picamera')

import picamera
import io
import mimetypes

import wiringpi




INDEX_PAGE_VLC = \
"""
<!DOCTYPE html>
<html><body>
<h1> The view from our window. </h1>
<h4>
WINDOWS NOTE: To be able to see the stream you need VLC being installed at your PC: 'http://www.videolan.org/vlc/index.html'.
If your browser doesn't show the stream immediately probably approval is needed for VLC plug-in to be activated (try a right click at the plug-in area).
</h4>
<h4>
ANDROID NOTE: You can actually see the stream at port 8100 at your Android devices if you install 'VLC for Android
beta' and use 'Open Network Stream' icom (antenna) at the top-right corner of the application. Give it: http://pagealh.asuscomm.com:8100. Try few times if it hungs.
</h4>
<embed type="application/x-vlc-plugin" pluginspage="http://www.videolan.org" autoplay="yes" src="http://pagealh.asuscomm.com:8100" loop="no" width="640" height="480" target="http://pagealh.asuscomm.com:8100/" ></embed>
</html></body>
"""


INDEX_PAGE_VLC_OLD = \
"""
<!DOCTYPE html>
<html><body>
<h1> The view from our window. </h1>
<h4>
WINDOWS NOTE: To be able to see the stream you need VLC being installed at your PC: 'http://www.videolan.org/vlc/index.html'.
If your browser doesn't show the stream immediately probably approval is needed for VLC plug-in to be activated (try a right click at the plug-in area).
</h4>
<h4>
80ANDROID NOTE: You can actually see the stream at port 8100 at your Android devices if you install 'VLC for Android
beta' and use 'Open Network Stream' icom (antenna) at the top-right corner of the application. Give it: http://pagealh.asuscomm.com:8100. Try few times if it hungs.
</h4>
<OBJECT classid="clsid:9BE31822-FDAD-461B-AD51-BE1D1C159921"
 codebase="http://downloads.videolan.org/pub/videolan/vlc/latest/win32/axvlc.cab"
 width="640" height="480" id="vlc" events="True">
 <param name="Src" value="http://pagealh.asuscomm.com:8100/" />
 <param name="ShowDisplay" value="True" />
 <param name="AutoLoop" value="False" />
 <param name="AutoPlay" value="True" />
</OBJECT>
</html></body>
"""
# <embed id="vlcEmb" type="application/x-google-vlc-plugin" version="VideoLAN.VLCPlugin.2"
#autoplay="yes" loop="no" width="640" height="480"

class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    _preview = False
    _camera = None
    stop_streaming = False

    def requestline(self):
        return 1

    def request_version(self):
        return 'HTTP/5.0'

    def handle(self):

        if not globals().has_key("the_stream_exists"):
            globals()["the_stream_exists"] = True
            os.system("raspivid -o - -t 0 -n -w 640 -h 480 -fps 20 -vf -hf  |cvlc -vvv stream:///dev/stdin --sout '#standard{access=http,mux=ts,dst=:8100}' :demux=h264 &")
            time.sleep(2)
            print("!!! streaming started")

        print("start streaming on request")

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(INDEX_PAGE_VLC)))
        self.request.send(INDEX_PAGE_VLC)
        self.end_headers()

        
        
class NETTYPE:
    LAN = 1
    WLAN = 2
    CELL = 3

class StrmServerHTTP :
    _stop_server = False
    _main_thread = None
    _nettype = NETTYPE.LAN

    def GetLocalIP(self):
        ifconfig_cmd = commands.getoutput("ifconfig")
        patt = re.compile(r'inet\s*\w*\S*:\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
        addr_list = patt.findall(ifconfig_cmd)
        for addr in addr_list:
            if addr == "127.0.0.1":
                continue
            if(self._nettype == NETTYPE.CELL):
                if(addr.find("192.168.") == 0):
                    continue
            if(addr.find('.')>0):
                return addr
        return "127.0.0.1"


    def _HTTPThread(self):
        IP = self.GetLocalIP()
        self._http_srv = BaseHTTPServer.HTTPServer((IP, 8101),HTTPHandler)
        self._http_srv.rbufsize = -1
        self._http_srv.wbufsize = 100000000
        print("http server started at " + IP + ":8101")
        while (self._stop_server == False):
            try:
                self._http_srv.handle_request()
            except Exception as e:
                pass
        print("http server finished")

    def SwitchIRLeds(self, direction='on'):
        GPIO5=24
        os.system("gpio export %s out"%GPIO5)
        io = wiringpi.GPIO(wiringpi.GPIO.WPI_MODE_SYS)  
        io.pinMode(GPIO5,io.OUTPUT)
        wiringpi.pinMode(GPIO5,io.OUTPUT)
        if(direction=='on'):
            io.digitalWrite(GPIO5,io.HIGH)  # Turn on the IR lights
            print("IR light switched On")
        else:
            io.digitalWrite(GPIO5,io.LOW)  # Turn on the IR lights
            print("IR light switched Off")

    def Run(self):
        #self.SwitchIRLeds()
        self._main_thread = threading.Thread(target=self._HTTPThread)
        self._main_thread.start()

    def Stop(self):
        self._stop_server=True
        self._http_srv.socket.close()
        

srv = StrmServerHTTP()
srv.Run()
