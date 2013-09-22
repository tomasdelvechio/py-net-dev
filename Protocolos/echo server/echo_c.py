#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Cliente "ECHO-SOCK_STREAM"
import socket

def main():
    buff_size = 4096                # Tamaño del buffer
    host, port = '10.4.10.12', 5600  # Host y Puerto a donde se va a conectar
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Declaración del Socket
    s.connect((host, port))         # Inicia la conexión TCP contra el servidor
    lectura = raw_input("Ingrese el texto: \n")
    #~ while lectura != 'q':
    s.send(lectura)                  # Envío algo
    recibido = s.recv(buff_size)     # Recibo algo
    print ("echo: %s")%recibido
    #~ lectura = raw_input("Ingrese el texto: \n")
    s.close()                       # Cierro el socket
    return 0

if __name__ == '__main__':
    main()

