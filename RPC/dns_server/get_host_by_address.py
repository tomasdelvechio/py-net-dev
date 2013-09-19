#!/usr/bin/env python
from xmlrpclib import *
import sys

if(len(sys.argv) < 3):
    sys.exit("Forma de ejecucion: python %s <server_ip> <server_port> <ip_address>" % sys.argv[0])

server = ServerProxy("http://"+sys.argv[1]+":"+str(sys.argv[2]))

ip_addr = server.gethostbyaddr(sys.argv[3])
if ip_addr:
    print ip_addr
else:
    print "No se pudo resolver"




