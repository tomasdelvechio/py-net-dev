#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys

if(len(sys.argv) < 2):
    sys.exit("Forma de ejecucion: python %s <server_ip> <server_port>" % sys.argv[0])

if(len(sys.argv) < 3):
    sys.exit("Falta <server_port>. Forma de ejecucion: python %s <server_ip> <server_port>" % sys.argv[0])

buff_size = 4096
host, port = sys.argv[1],int(sys.argv[2])

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))
s.send("0")
data = s.recv(buff_size)

dateinfo,tz,formato,version = data.splitlines()
print "Fecha y Hora: ", dateinfo
print "Zona horaria: ",tz
print "Formato: ", formato
print "Protocol Version: ", version

s.close()
