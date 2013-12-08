#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from datetime import datetime
import sys
import socket
import struct

# Mide el RTT en base a una conexion TCP
def medir_rtt_stream(ip,time_interval):

    puerto = 80

    medidas = []

    initial_time = datetime.now().second
    while initial_time+time_interval >= datetime.now().second:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        before_connect_time = datetime.now()
        s.connect((ip, puerto))
        after_connect_time = datetime.now()
        s.close()

        delta = after_connect_time - before_connect_time
        medidas.append(delta.microseconds / 1000) # Micro to Milli

    print "Server: %s:%d - rtt min/avg/max = %d/%d/%d ms. Cantidad de pruebas: %d\n" % (ip,puerto,min(medidas),sum(medidas)/len(medidas),max(medidas),len(medidas))
    return 1

# Mide el RTT en base a una conexion UDP
def medir_rtt_dgram(ip,time_interval):

    puerto = 53

    medidas = []

    data_send = struct.pack('>hhhhhh',0x130,0x1000,0x1000,0x1000,0x1000,0x120)

    initial_time = datetime.now().second
    while initial_time+time_interval >= datetime.now().second:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        before_connect_time = datetime.now()
        s.sendto(data_send, (ip, puerto))
        data = s.recvfrom(1024)
        after_connect_time = datetime.now()
        s.close()

        delta = after_connect_time - before_connect_time
        medidas.append(delta.microseconds / 1000) # Micro to Milli

    print "Server: %s:%d - rtt min/avg/max = %d/%d/%d ms. Cantidad de pruebas: %d\n" % (ip,puerto,min(medidas),sum(medidas)/len(medidas),max(medidas),len(medidas))
    return 1

# Tratamiento de parametros del script #
########################################

parser = argparse.ArgumentParser(description="Script para medir RTT de una conexion sobre TCP o UDP. Para UDP, se solicita un listado de IPs de DNS (Port 53). Para IP, un listado de servidores web (Port 80)")
parser.add_argument('-t', '--tipo', help="Tipo de conexion. TCP o UDP. TCP por defecto")
parser.add_argument('-T', '--time-interval', help="Intervalo de tiempo sobre el que se medira el RTT.")
parser.add_argument('-i', '--ip-list', help="Archivo con listados de IP a ser medidos. Una IP por fila.")

args = parser.parse_args()

if args.tipo:
    tipo = args.tipo
    if tipo in ("TCP","UDP"):
        pass
    else:
        sys.exit('Tipo invalido. Debe ser TCP o UDP')
else:
    tipo = "TCP"

# Set time_interval
if args.time_interval:
    time_interval = int(args.time_interval)
else:
    sys.exit('Debe especificar un intervalo de tiempo en segundos. -T <segundos> o --time-interval <segundos>')

# Set method
if args.ip_list:
    ip_file = args.ip_list
    try:
       with open(ip_file):
           pass
    except IOError:
       sys.exit('Debe especificar un archivo con al menos una IP para probar. -i <archivo> o --ip-list <archivo>')
else:
    sys.exit('Debe especificar un archivo con al menos una IP para probar. -i <archivo> o --ip-list <archivo>')

# Levanta el archivo de IPs #
#############################

try:
   with open(ip_file) as f:
       ip_list = f.read().splitlines()
except IOError:
   sys.exit('Ocurrio un error al abrir el archivo: %s' % ip_file)

# Procesar cada IP #
####################

valores = {}

for ip in ip_list:
    if tipo == "TCP":
        valores[ip] = medir_rtt_stream(ip,time_interval)
    else:
        valores[ip] = medir_rtt_dgram(ip,time_interval)
