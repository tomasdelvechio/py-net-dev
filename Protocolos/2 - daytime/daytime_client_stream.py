#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys

if(len(sys.argv) < 2):
    sys.exit("Forma de ejecucion: python %s <server_ip> <server_port>" % sys.argv[0])

if(len(sys.argv) < 3):
    sys.exit("Falta <server_port>. Forma de ejecucion: python %s <server_ip> <server_port>" % sys.argv[0])

print """Cliente daytime
    
    Mensaje de peticion: 1 byte.
    
    Mensaje de respuesta: 4 Campos separados por '|'. El formato es el siguiente:
        
        <fecha_y_hora:42 bytes>|<timezone:32 bytes>|<formato_fecha_y_hora:25 bytes>|<version:5 bytes>
        Total: 107 bytes.
    """

buff_size = 107 # Tamaño de la PDU de respuesta
host, port = sys.argv[1],int(sys.argv[2])

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))
s.send("0")
data = s.recv(buff_size)

dateinfo,tz,formato,version = [x.strip() for x in data.split('|')] # Parse por separador | y elimino espachos innecesarios
print "Fecha y Hora: ", dateinfo
print "Zona horaria: ",tz
print "Formato: ", formato
print "Protocol Version: ", version

s.close()
