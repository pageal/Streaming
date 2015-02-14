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


INDEX_PAGE_VLC = \
"""
<!DOCTYPE html>
<html><body>
<h1> The view from our window. </h1>
<OBJECT classid="clsid:9BE31822-FDAD-461B-AD51-BE1D1C159921"
 codebase="http://downloads.videolan.org/pub/videolan/vlc/latest/win32/axvlc.cab"
 width="640" height="480" id="vlc" events="True">
 <param name="Src" value="http://46.117.246.251:8080/" />
 <param name="ShowDisplay" value="True" />
 <param name="AutoLoop" value="False" />
 <param name="AutoPlay" value="True" />
 <embed id="vlcEmb" type="application/x-google-vlc-plugin" version="VideoLAN.VLCPlugin.2" autoplay="yes" loop="no" width="640" height="480"
 target="http://46.117.246.251:8080/" ></embed>
</OBJECT>
</html></body>
"""

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
            os.system("raspivid -o - -t 9999999 -n -w 640 -h 480 -fps 20 -vf  |cvlc -vvv stream:///dev/stdin --sout '#standard{access=http,mux=ts,dst=:8080}' :demux=h264 &")
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
        self._http_srv = BaseHTTPServer.HTTPServer((IP, 8081),HTTPHandler)
        self._http_srv.rbufsize = -1
        self._http_srv.wbufsize = 100000000
        print("http server started at " + IP + ":8081")
        while (self._stop_server == False):
            try:
                self._http_srv.handle_request()
            except Exception as e:
                pass
        print("http server finished")

    def Run(self):
        self._main_thread = threading.Thread(target=self._HTTPThread)
        self._main_thread.start()

    def Stop(self):
        self._stop_server=True
        self._http_srv.RequestHandlerClass.stop_streaming = True
        self._main_thread.join()

srv = StrmServerHTTP()
srv.Run()
