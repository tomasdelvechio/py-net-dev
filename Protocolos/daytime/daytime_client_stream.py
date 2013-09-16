#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys

if(len(sys.argv) < 2):
    sys.exit("Falta el mensaje. Forma de ejecucion: python %s mensaje" % sys.argv[0])

data_send = sys.argv[1]

# Ejemplo de Socket Cliente TCP
buff_size = 4096                # Tamaño del buffer
host, port = 'localhost', 5600  # Host y Puerto a donde se va a conectar
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Declaración del Socket
s.connect((host, port))         # Inicia la conexión TCP contra el servidor
s.send(data_send)                  # Envío algo
data = s.recv(buff_size)               # Recibo algo
print "El servidor respondio: ", data
s.close()                       # Cierro el socket
