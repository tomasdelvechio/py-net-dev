#!/usr/bin/env python
from SimpleXMLRPCServer import SimpleXMLRPCServer
import sys

def saludo (nombre):
    return "Hola " + str(nombre)

def despedida (nombre):
    return "Chau " + str(nombre)

if(len(sys.argv) < 3):
    sys.exit("Forma de ejecucion: python %s <server_ip> <server_port>" % sys.argv[0])

server = SimpleXMLRPCServer((sys.argv[1], int(sys.argv[2])))
server.register_function(saludo)
server.register_function(despedida)
server.serve_forever()
