# -*- coding: utf-8 -*-
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

import picamera
import io
import mimetypes

import wiringpi


timezone = 3600
#        <meta http-equiv="refresh" content="5">
#            body {font-family: "Arial", Verdana, Sans-serif;}
#            h1 {font-weight: bold; }


#            h3 {border-style: solid;}

INDEX_PAGE_VLC = \
"""
<!DOCTYPE html>
<html>
    <head>
        <meta charset=utf-8>
        <style>
        </style>
    </head>
    <body>
        <p align="center"><img src="pic/sambo_title_01.jpg" alt="smiley" height="300" width="919"></p>
        <h1 align="center"><b> INTERNATIONAL COMBAT SAMBO COMPETITION. Haifa-2015 </b></h1>
        <h1 align="center"><b> Международное Соревнование по Боевому Самбо. Хайфа-2015 </b></h1>
        <h3>WINDOWS NOTE(Mozilla FireFox, Intenet Explorer):</b> To be able to see the stream you need VLC being installed at your PC: 'http://www.videolan.org/vlc/index.html'.
        If your browser doesn't show the stream immediately probably approval is needed for VLC plug-in to be activated (try a right click at the plug-in area).<h3>
        <h3><b>ANDROID NOTE:</b> You can actually see the stream at port 8080 at your Android devices if you install 'VLC for Android
        beta' and use 'Open Network Stream' icom (antenna) at the top-right corner of the application. Give it: http://pagealh.asuscomm.com:8080. Try few times if it hungs.</h3>
        
        <p align="center"><embed type="application/x-vlc-plugin" pluginspage="http://www.videolan.org" autoplay="yes" src="http://pagealh.asuscomm.com:8080" loop="no" width="640" height="480" target="http://pagealh.asuscomm.com:8080/" ></embed></p>
        <h5>
        </h5>
        <p align="center"><img src="pic/sambo_title_02.jpg" alt="smiley" height="235" width="919"></p>
    </body>
</html>
"""

class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    _preview = False
    _camera = None
    stop_streaming = False

    def requestline(self):
        return 1

    def request_version(self):
        return 'HTTP/5.0'

    def do_GET(self):        
        if self.path == "/":
            page = INDEX_PAGE_VLC
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(page)))
            self.request.send(page)
            self.end_headers()
            return
        if self.path == "/pic/sambo_title_01.jpg":
            self.send_response(200)
            self.send_header("Content-type", "image/jpg")
            self.end_headers() 
            f = open('pic/sambo_title_01.jpg', 'rb')
            self.wfile.write(f.read())
            f.close()
            return

        if self.path == "/pic/sambo_title_02.jpg":
            self.send_response(200)
            self.send_header("Content-type", "image/jpg")
            self.end_headers() 
            f = open('pic/sambo_title_02.jpg', 'rb')
            self.wfile.write(f.read())
            f.close()
            return
        
        
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
        self._http_srv.allow_reuse_address = True
        self._http_srv.rbufsize = -1
        self._http_srv.wbufsize = 100000000
        print("http server started at " + IP + ":8081")
        while (self._stop_server == False):
            try:
                self._http_srv.handle_request()
            except Exception as e:
                pass
        print("http server finished")
        self._http_srv.socket.close()

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
        if not globals().has_key("the_stream_exists"):
            globals()["the_stream_exists"] = True
            os.system("raspivid -o - -t 0 -n -w 640 -h 480 -fps 20 -vf -hf  |cvlc -vvv stream:///dev/stdin --sout '#standard{access=http,mux=ts,dst=:8080}' :demux=h264 &")
            print("!!! streaming started")

        #self.SwitchIRLeds()
        self._main_thread = threading.Thread(target=self._HTTPThread)
        self._main_thread.start()

    def Stop(self):
        self._stop_server=True
        

srv = StrmServerHTTP()
srv.Run()
