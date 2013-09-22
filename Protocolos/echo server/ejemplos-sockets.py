#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket


# Ejemplo de Socket Servidor TCP
buff_size = 4096                # Tamaño del buffer
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
        # Si quisiera enviar una respuesta
        # client_sock.sendall('Algo')
        data = client_sock.recv(buffsize) # Sigo leyendo el buffer hasta que este vacío y salga del while
    
    print "Conexion cerrada por:", client_sock.getpeername()
    client_sock.close()

# Ejemplo de Socket Cliente TCP
buff_size = 4096                # Tamaño del buffer
host, port = 'localhost', 5600  # Host y Puerto a donde se va a conectar
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Declaración del Socket
s.connect((host, port))         # Inicia la conexión TCP contra el servidor
s.send("Algo")                  # Envío algo
s.recv(buff_size)               # Recibo algo
s.close()                       # Cierro el socket

#----------------------------------------------------------------------------------------------------------------------------------------

# Ejemplo de Socket Servidor UDP
buff_size = 4096                # Tamaño del buffer
host, port = 'localhost', 5600  # Host y Puerto a donde se va a conectar
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   # Declaración del Socket UDP
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Permite reutilizar host/port "inmediatamente" si se nos cae el servidor
s.bind((host, port))            # Le indico en qué host y puerto va a atender las peticiones
while True:                    # Bucle principal del servidor
    data, address = s.recvfrom(buffsize) # espera conexiones
    # Si quisiera enviar una respuesta 
    # s.sendto(data, address)
    
# Ejemplo de Socket Cliente UDP
buff_size = 4096
host, port = 'localhost', 5600
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto("ALGO", (host, port))

data = s.recvfrom(buff_size) # La respuesta
print "Respondio:",data
s.close()

    



