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

def open_conn(host,port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    
    return s
    
# Solicita login plano
request = { "opt": {"login":"tomas"} }
s = open_conn(host,port)
s.send(json.dumps(request))
response = json.loads(s.recv(buff_size))
s.close()

prompt = response["opt"]["prompt"]
session = response["opt"]["session"]

cmd = ''
print "Nueva sesion en %s:%d\n" % (host,port)
while cmd != "exit":
    s = open_conn(host,port)
    cmd = raw_input(prompt)
    request = { 'cmd' : cmd, 'opt' : { 'session' : session } }
    s.send(json.dumps(request))
    response = s.recv(buff_size)
    while 1:
        data = s.recv(buff_size)
        response += data
        if not data: break
    response = json.loads(response)
    print response['out']
    s.close()
print "Sesion cerrada desde %s:%d\n" % (host,port)
#~ cmd = raw_input('user@serverhost:$ ')
