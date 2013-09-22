#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys

#~ if(len(sys.argv) < 2):
    #~ sys.exit("Falta el mensaje. Forma de ejecucion: python %s mensaje" % sys.argv[0])
#~ 
#~ data_send = sys.argv[1]

cmd = raw_input('user@serverhost:$ ') # ToDo: Esto debe venir del server

while cmd != "exit":
    buff_size = 4096
    host, port = 'localhost', 8022
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.send(cmd)
    response = s.recv(buff_size)
    while 1:
        data = s.recv(buff_size)
        response += data
        if not data: break

    print response
    s.close()
    cmd = raw_input('user@serverhost:$ ')
