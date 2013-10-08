#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys

if(len(sys.argv) < 2):
    sys.exit("Forma de ejecucion: python %s <server_ip> <server_port>" % sys.argv[0])

if(len(sys.argv) < 3):
    sys.exit("Falta <server_port>. Forma de ejecucion: python %s <server_ip> <server_port>" % sys.argv[0])

# Ejemplo de Socket Servidor UDP
buffsize = 4096
host, port = sys.argv[1],int(sys.argv[2])
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((host, port))

print "Server iniciado en", host, port
while True:                    # Bucle principal del servidor
    data, address = s.recvfrom(buffsize) # espera conexiones
    print "Mensaje desde: ", address
    print "  Mensaje: ", data
    # Si quisiera enviar una respuesta 
    s.sendto(data, address)
