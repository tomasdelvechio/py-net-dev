#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
from time import sleep
import sys

if(len(sys.argv) < 2):
    sys.exit("Forma de ejecucion: python %s <server_ip> <server_port>" % sys.argv[0])

if(len(sys.argv) < 3):
    sys.exit("Falta <server_port>. Forma de ejecucion: python %s <server_ip> <server_port>" % sys.argv[0])

# Ejemplo de Socket Servidor TCP
buffsize = 4096
host, port = sys.argv[1],int(sys.argv[2])
backlog = 5
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((host, port))
s.listen(backlog)

print "Server iniciado en", host, port
while True:
    client_sock, client_addr = s.accept()
    print "Conexion desde:", client_sock.getpeername()
    data = client_sock.recv(buffsize)
    while len(data):
        client_sock.sendall(data)
        print "  Mensaje: ", data
        data = client_sock.recv(buffsize)
    print "Conexion cerrada por:", client_sock.getpeername()
    client_sock.close()
