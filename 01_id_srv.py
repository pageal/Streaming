import time
import sys
import thread
import threading
import signal
import curses
import picamera
import commands
import re
import struct
import ctypes
import socket
import SocketServer
import BaseHTTPServer




class IDServer :
    _IPAddr = "127.0.0.1"
    _CtrlPort = 8200
    _stop_requested = False
    _ctrl_thread = None

    _ctrl_server=None
    _ctrl_channel= None
    def __init__(self):
        pass

    def GetLocalIP(self):
        ifconfig_cmd = commands.getoutput("ifconfig")
        patt = re.compile(r'inet\s*\w*\S*:\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
        addr_list = patt.findall(ifconfig_cmd)
        for addr in addr_list:
            if addr == "127.0.0.1":
                continue
##            if(self._nettype == NETTYPE.CELL):
##                if(addr.find("192.168.") == 0):
##                    continue
            if(addr.find('.')>0):
                return addr
        return "127.0.0.1"

    def Start(self):
        self._IPAddr = self.GetLocalIP()
        self._stop_requested = False

        self._ctrl_thread = threading.Thread(target=self._AutoIDThread)
        self._ctrl_thread.start()


    def Stop(self):
        #wait all the service threads finishing
        if(self._ctrl_thread == None):
            return
        self._stop_requested = True
        if(self._ctrl_thread.isAlive()):
            self._ctrl_thread.join();
        self._ctrl_thread = None

    def SendMCStatus(self, msg):
        mc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        #mc_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        mc_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 100)
        mc_socket.bind((self._IPAddr, 8100))
        #mreq = struct.pack('4sl', socket.inet_aton("224.0.150.150"), socket.INADDR_ANY)
        mreq = struct.pack('4sl', socket.inet_aton("224.0.1.200"), socket.INADDR_ANY)
        mc_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        #mc_socket.sendto("init", ("224.0.150.150", 8100))

        mc_socket.sendto(msg, ("224.0.1.200", 8200))
        mc_socket.close()

    def _AutoIDThread(self):
        print("Control Thread started.")

        msg = ""
        received = 0
        while(self._stop_requested == False):
            try:
                self.SendMCStatus("I'm alive")
                time.sleep(5)
            except socket.timeout as e:
                pass


        # Cleanup before therad exit
        try:
            if(mc_socket != None):
                mc_socket.close()
                print("ctrl channel closed")
        except Exception as e:
            pass
        print("Control Thread finished.")


##if __name__ == "__main__":
##    srv = IDServer()
##    srv.Start()

srv = IDServer()
srv.Start()
