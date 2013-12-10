#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
from datetime import datetime

def get_str_time(dt):
	return datetime.strftime(dt, '%H:%M:%S.%f %d-%m-%Y')

format = '%H:%M:%S.%f %d-%m-%Y'

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

host = '127.0.0.1'
port = 8081
buff = 1024

t0 = datetime.now()
s.sendto('ping', (host,port))
data, addr = s.recvfrom(buff)
t1 = datetime.now()

header, t_server = data.split('|')

dt_server = datetime.strptime(t_server,format)

delta = t1 - t0
t_nueva_local = dt_server + (delta // 2)

print 'Incial:', get_str_time(t0)
print 'Final:', get_str_time(t1)
print 'Delta: ', delta
print 'Hora del server:', get_str_time(dt_server)
print 'Nueva hora local:', get_str_time(t_nueva_local)
