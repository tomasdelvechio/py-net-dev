#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket

# Ejemplo de Socket Servidor UDP
buff_size = 4096                # Tamaño del buffer
host, port = 'localhost', 5600  # Host y Puerto a donde se va a conectar
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   # Declaración del Socket UDP
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Permite reutilizar host/port "inmediatamente" si se nos cae el servidor
s.bind((host, port))            # Le indico en qué host y puerto va a atender las peticiones
while True:                    # Bucle principal del servidor
    data, address = s.recvfrom(buff_size) # espera conexiones
    # Si quisiera enviar una respuesta 
    s.sendto(data, address)
