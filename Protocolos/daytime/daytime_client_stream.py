#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys

if(len(sys.argv) < 2):
    sys.exit("Forma de ejecucion: python %s <server_ip> <server_port> [<timezone>]" % sys.argv[0])

if(len(sys.argv) < 3):
    sys.exit("Falta <server_port>. Forma de ejecucion: python %s <server_ip> <server_port> [<timezone>]" % sys.argv[0])

if(len(sys.argv) < 4):
    tz = "0"
else:
    tz = sys.argv[3]

buff_size = 4096                # Tamaño del buffer
host, port = sys.argv[1],int(sys.argv[2])  # Host y Puerto a donde se va a conectar
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Declaración del Socket
s.connect((host, port))         # Inicia la conexión TCP contra el servidor
s.send(tz)                  # Envío algo
data = s.recv(buff_size)               # Recibo algo
print "Fecha y Hora: ", data
s.close()                       # Cierro el socket
