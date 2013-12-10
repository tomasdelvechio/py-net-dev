#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket, re, select, os, json
from datetime import datetime

class TimeServer:
    def __init__(self, host = '', port = 8081):
        self.host = host
        self.port = port
                
        self.sock_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock_server.bind((self.host, self.port))
        
        print  "Servidor NTP iniciado en %s:%i" %(self.host, self.port)
        
    def run(self):
        while True:
            request, addr = self.sock_server.recvfrom(1024)
            print addr, "-%s-"%(request)
            try:
                if request.lower().startswith('ping'):
                    dt = datetime.now()
                    self.pdu = "pong|%s" % dt.strftime('%H:%M:%S.%f %d-%m-%Y')
                else:
                    self.pdu = "pong|error"
            except Exception, e:
                print e
                
            self.sock_server.sendto(self.pdu, addr)
            
if __name__ == '__main__':
    server = TimeServer()
    server.run()

