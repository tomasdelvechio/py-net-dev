#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys
from subprocess import call

if(len(sys.argv) < 2):
    sys.exit("Forma de ejecucion: python %s <server_ip> <server_port>" % sys.argv[0])

if(len(sys.argv) < 3):
    sys.exit("Falta <server_port>. Forma de ejecucion: python %s <server_ip> <server_port>" % sys.argv[0])

buffsize = 4096
host, port = sys.argv[1],int(sys.argv[2])
backlog = 5

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((host, port))
s.listen(backlog)

while True:
    client_sock, client_addr = s.accept()
    print "Conexion desde:", client_sock.getpeername()
    data = client_sock.recv(buffsize)
    #~ while len(data):
    #~ print "Comando: ",data
    with open('outfile','w') as fout:
        call(data,stdout=fout,shell=True)
    response = open('outfile').read()
    #~ print response
    client_sock.sendall(response)
    
    #~ client_sock.sendall(data)
    #~ data = client_sock.recv(buffsize) # Sigo leyendo el buffer hasta que este vacío y salga del while
    
    # Cuando termino de llegar el comando, lo ejecuta
    
    print "Conexion cerrada por:", client_sock.getpeername()
    client_sock.close()
