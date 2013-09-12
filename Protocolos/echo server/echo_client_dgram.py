#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys

data_send = sys.argv[1]

# Ejemplo de Socket Cliente UDP
buff_size = 4096
host, port = 'localhost', 5600
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto(data_send, (host, port))

data = s.recvfrom(buff_size) # La respuesta
print "Respondio:",data[0]
s.close()
