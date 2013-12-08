#!/usr/bin/env python
from xmlrpclib import *
import sys

if(len(sys.argv) < 2):
    sys.exit("Forma de ejecucion: python %s <server_ip> <server_port>" % sys.argv[0])

server = ServerProxy("http://"+sys.argv[1]+":"+str(sys.argv[2]))

for hostname in ["localhost","www.unlu.edu.ar","www.tomasdelvechio.com.ar"]:
    print "%s es %s" % (hostname,server.gethostbyname(hostname))
for ip_address in ['127.0.0.1','192.168.1.10','10.0.1.12']:
    print "%s es %s" % (ip_address,server.gethostbyaddr(ip_address))



