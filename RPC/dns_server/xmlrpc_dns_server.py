#!/usr/bin/env python
from SimpleXMLRPCServer import SimpleXMLRPCServer
import sys

def load_hosts(mode='host_by_name',hosts_file='hosts'):
    
    f = open(hosts_file)
    hosts = f.readlines()
    hosts_dic = {}
    for host in hosts:
        host_part = host.split()
        if mode == 'host_by_name':
            hosts_dic[host_part[1]] = host_part[0]
        if mode == 'host_by_addr':
            hosts_dic[host_part[0]] = host_part[1]
    return hosts_dic

def gethostbyname(hostname):
    hosts = load_hosts()
    return hosts[hostname]
    
def gethostbyaddr(ip_addr):
    hosts = load_hosts('host_by_addr')
    return hosts[ip_addr]

if(len(sys.argv) < 2):
    sys.exit("Forma de ejecucion: python %s <server_ip> <server_port>" % sys.argv[0])

server = SimpleXMLRPCServer((sys.argv[1], int(sys.argv[2])))
server.register_function(gethostbyname)
server.register_function(gethostbyaddr)
server.serve_forever()
