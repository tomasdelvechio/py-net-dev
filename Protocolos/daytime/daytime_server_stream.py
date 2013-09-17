#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import datetime
import sys
import pytz

if(len(sys.argv) < 2):
    sys.exit("Forma de ejecucion: python %s <server_ip> <server_port> <timezone>. Para informacion sobre las TimeZone disponibles consultar el archivo TIMEZONE." % sys.argv[0])

if(len(sys.argv) < 3):
    sys.exit("Falta <server_port>. Forma de ejecucion: python %s <server_ip> <server_port> <timezone>" % sys.argv[0])

if(len(sys.argv) < 4):
    sys.exit("Falta <timezone>. Forma de ejecucion: python %s <server_ip> <server_port> <timezone>" % sys.argv[0])

buffsize = 1 # Espero un paquete de 1 byte
host, port = sys.argv[1],int(sys.argv[2])
backlog = 5 # Cantidad de conexiones que vamos a atender/encolar
tz = sys.argv[3]
fmt = '%A, %B %d, %Y %H:%M:%S-%Z' # Formato con el que se envia el datetime al cliente
version = '1.0.0'

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((host, port))
s.listen(backlog)

while True:
    client_sock, client_addr = s.accept() # Acepta conexiones y retorna el sock para llegar al cliente y su dirección
    print "Conexion desde:", client_sock.getpeername()
    request = client_sock.recv(buffsize)  # Leo los datos entrantes
    
    # Calcula la hora segun la timezone que se determino al levantar el servidor
    utc_datetime = datetime.datetime.utcnow()
    utc_datetime = utc_datetime.replace(tzinfo=pytz.utc)
    data = datetime.datetime.astimezone(utc_datetime, pytz.timezone(tz))
    
    response =  """%s\n%s\n%s\n%s""" % (str(data.strftime(fmt)),tz,fmt,version) # Arma la estructura de respuesta para el cliente.
    client_sock.sendall(response)
    
    print "    Respuesta:", data
    print "Conexion cerrada por:", client_sock.getpeername()
    
    client_sock.close()
