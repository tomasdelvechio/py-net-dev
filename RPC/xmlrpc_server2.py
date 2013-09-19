#!/usr/bin/env python
from SimpleXMLRPCServer import SimpleXMLRPCServer
import sys

def insulto (nombre):
    return "#@!@#$#!@%%## " + str(nombre)

if(len(sys.argv) < 3):
    sys.exit("Forma de ejecucion: python %s <server_ip> <server_port>" % sys.argv[0])

server = SimpleXMLRPCServer((sys.argv[1], int(sys.argv[2])))
server.register_function (insulto)
server.serve_forever ()
