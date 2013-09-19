#!/usr/bin/env python
from xmlrpclib import *
import sys

if(len(sys.argv) < 5):
    sys.exit("Forma de ejecucion: python %s <server_uno_ip> <server_uno_port> <server_dos_ip> <server_dos_port>" % sys.argv[0])

server1 = ServerProxy("http://"+sys.argv[1]+":"+str(sys.argv[2]))
server2 = ServerProxy("http://"+sys.argv[3]+":"+str(sys.argv[4]))

print server1.saludo("Juancito")
print server1.despedida("Juancito")
print server2.insulto("Juancito")


