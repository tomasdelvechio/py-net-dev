#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys

if(len(sys.argv) < 2):
    sys.exit("Forma de ejecucion: python %s \"mensaje\" <ip_server> <port_server>" % sys.argv[0])

if(len(sys.argv) < 3):
    sys.exit("Falta ip y puerto del servidor. Forma de ejecucion: python %s mensaje <ip_server> <port_server>" % sys.argv[0])

if(len(sys.argv) < 4):
    sys.exit("Falta el puerto del servidor. Forma de ejecucion: python %s mensaje <ip_server> <port_server>" % sys.argv[0])

data_send = sys.argv[1]
buff_size = 4096
host, port = sys.argv[2],int(sys.argv[3])
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto(data_send, (host, port))

data = s.recvfrom(buff_size) # La respuesta
print "Respondio:",data[0]
s.close()
