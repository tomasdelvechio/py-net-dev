#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import datetime
import sys

if(len(sys.argv) < 2):
    sys.exit("Forma de ejecucion: python %s <server_ip> <server_port>" % sys.argv[0])

if(len(sys.argv) < 3):
    sys.exit("Falta <server_port>. Forma de ejecucion: python %s <server_ip> <server_port>" % sys.argv[0])


#~ now = datetime.datetime.now()
#~ now.strftime('%A, %B %m, %Y %X')

# Ejemplo de Socket Servidor UDP
buff_size = 4096                # Tamaño del buffer
host, port = sys.argv[1],int(sys.argv[2])   # Host y Puerto a donde se va a conectar
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   # Declaración del Socket UDP
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Permite reutilizar host/port "inmediatamente" si se nos cae el servidor
s.bind((host, port))            # Le indico en qué host y puerto va a atender las peticiones
while True:                    # Bucle principal del servidor
    data, address = s.recvfrom(buff_size) # espera conexiones
    # Si quisiera enviar una respuesta 
    s.sendto(data, address)
