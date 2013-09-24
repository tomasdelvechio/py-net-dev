#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys
import json

#~ if(len(sys.argv) < 2):
    #~ sys.exit("Falta el mensaje. Forma de ejecucion: python %s mensaje" % sys.argv[0])
#~ 
#~ data_send = sys.argv[1]
buff_size = 4096
host, port = 'localhost', 8022

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))

# Solicita login plano
request = { "opt": {"login":"tomas"} }

s.send(json.dumps(request))

response = json.loads(s.recv(buff_size))
prompt = response["options"]["prompt"]

cmd = ''
while cmd != "exit":
    cmd = raw_input(prompt)
    s.send(cmd)
    response = s.recv(buff_size)
    while 1:
        data = s.recv(buff_size)
        response += data
        if not data: break
    print response

s.close()
#~ cmd = raw_input('user@serverhost:$ ')
