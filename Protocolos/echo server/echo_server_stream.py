#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
from time import sleep
# Ejemplo de Socket Servidor TCP
buffsize = 4096                # Tamaño del buffer
host, port = 'localhost', 5600  # Host y Puerto a donde se va a conectar
backlog = 5                     # Cantidad de conexiones que vamos a atender/encolar
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Declaración del Socket TCP
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Permite reutilizar host/port "inmediatamente" si se nos cae el servidor
s.bind((host, port))            # Le indico en qué host y puerto va a atender las peticiones
s.listen(backlog)               
while True:                    # Bucle principal del servidor
    client_sock, client_addr = s.accept() # Acepta conexiones y retorna el sock para llegar al cliente y su dirección
    print "Conexion desde:", client_sock.getpeername()
    data = client_sock.recv(buffsize)  # Leo los datos entrantes
    while len(data):                  # Mientras haya datos sigo leyendo
        #~ sleep(10) # Prueba que es multi cliente. 2 clientes que se conectan en menos de este tiempo, son encolados
        client_sock.sendall(data)
        data = client_sock.recv(buffsize) # Sigo leyendo el buffer hasta que este vacío y salga del while
    print "Conexion cerrada por:", client_sock.getpeername()
    client_sock.close()
