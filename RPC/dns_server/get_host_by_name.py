#!/usr/bin/env python
from xmlrpclib import *
import sys

if(len(sys.argv) < 3):
    sys.exit("Forma de ejecucion: python %s <server_ip> <server_port> <hostname>" % sys.argv[0])

server = ServerProxy("http://"+sys.argv[1]+":"+str(sys.argv[2]))

host = server.gethostbyname(sys.argv[3])
if host:
    print host
else:
    print "No se pudo resolver"




