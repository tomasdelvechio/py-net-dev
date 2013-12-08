#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import socket
import os
import select
import re
import json
import argparse
from http_client import HttpClient
from threading import Thread
from urlparse import urlparse

debug = False

class BalancerThread(Thread):
    """Implementa un mini cliente, para realizar descargas en paralelo de las peticiones"""
    def __init__(self,client_socket,server_data):
        Thread.__init__(self)
        self.client_socket = client_socket
        self.buffer = 4096
        self.separador = '\r\n\r\n' # Separador de header y content de la respuesta HTTP
        self.h_separador = '\r\n'

        # Client vars
        self.headers = {}
        self.requests = {}
        self.server_data = server_data
        self.sock_timeout = 10

    def receive_request(self, socket):
        data = socket.recv(self.buffer)
        while len(data) == self.buffer:
            data += socket.recv(self.buffer)
        return data

    def run(self):
        # Recibe la peticion desde el cliente
        request = self.receive_request(self.client_socket)
        # Abre una conexion contra el servidor seleccionado
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.settimeout(self.sock_timeout)
        try:
            server_socket.connect(self.server_data)
        except socket.error, msg:
            sys.stderr.write("[ERROR] %s\n" % msg[1])
            sys.exit(2)
        # Descarga el contenido, y en la medida que lo recibe, lo reenvia al cliente
        #  Parseamos el request
        dic_headers = request.split(self.h_separador)
        method, request, version = dic_headers[0].split()
        path = urlparse(request).path
        #  Con el path del request, armamos la peticion para el servidor
        new_request = "GET %s HTTP/1.0%s" % (path,self.separador)
        server_socket.sendall(new_request)
        #  Recibimos del server y devolvemos al cliente
        response = server_socket.recv(self.buffer)
        self.client_socket.sendall(response)
        while len(response):
            response = server_socket.recv(self.buffer)
            self.client_socket.sendall(response)
        # Cierra la conexion
        self.client_socket.close()
        server_socket.close()
            

class BalancerServer(object):
    
    def __init__(self, host='', port=8080, logfile='headers.log', configfile='server.conf'):
        # Server vars
        self.LOGFILE = logfile
        self.http_version = "HTTP/1.0"
        self.separador = '\r\n\r\n' # Separador de header y content de la respuesta HTTP
        self.h_separador = '\r\n'
        self._header_detected = False

        # socket vars
        self.buffer = 4096
        self.backlog = 5
        self.host = host
        self.port = port

        self.config = self.load_config(configfile)

        # round robin
        self.last_server = None

    def load_config(self, configfile):
        try:
            with open(configfile) as f:
               config = f.read()
               return json.loads(config)
        except IOError:
            sys.exit('Archivo de configuracion no existe o el proceso no posee los permisos necesarios para leerlo. Path: %s' % os.path.abspath(configfile))
        except ValueError:
            sys.exit('Formato del archivo de configuracion incorrecto. Path: %s' % os.path.abspath(configfile))

    def open_socket(self):
        sock_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_server.bind((self.host,self.port))
        sock_server.listen(self.backlog)
        sock_input = [sock_server, sys.stdin]
        return sock_server, sock_input

    def next_server(self):
        if self.last_server is None:
            self.last_server = 0
        else:
            self.last_server = (self.last_server + 1) % len(self.config)

        server = self.config[self.config.keys()[self.last_server]]

        return server["host"], int(server["port"]) 

    def run(self):
        # Arma socket de servidor
        self.sock_server, self.sock_input = self.open_socket()
        
        print "[S]: Servidor iniciado en %s:%s" % (self.host is not '' if self.host else '0.0.0.0',self.port)

        hilos = []
        try:
            while True:
                lst_input,lst_output,lst_error = select.select(self.sock_input,[],[])

                for s in lst_input:

                    if s == self.sock_server:
                        client, address = self.sock_server.accept()
                        if debug:
                            print " [S]: Se ha conectado %s:%s" % address
                        self.sock_input.append(client)

                    elif s == sys.stdin:
                        keyWord = sys.stdin.readline()
                        #break
                        pass

                    else:
                        # Procesa la request
                        print "  [S]: Peticion de: %s:%s" % s.getpeername()
                        server_data = self.next_server()
                        print "  [S]: Siguiente server", server_data
                        h = BalancerThread(s,server_data).start()
                        hilos.append(h)
                        self.sock_input.remove(s)

        except KeyboardInterrupt:
            print "\n [S]: Cerrando el servidor"
            self.sock_server.close()
            print " [S]: Sincronizando cache"
            self.save_cache()
        
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script que inicia un web server, segun los parametros proporcionados.")
    parser.add_argument('-i', '--host', help="Host donde escuchara el web server. 0.0.0.0 por defecto.")
    parser.add_argument('-p', '--port', help="Numero de puerto donde escuchara el web server. 8080 por defecto.")
    parser.add_argument('-c', '--configfile', help="Archivo de configuracion del servidor.")
    parser.add_argument('-l', '--logfile', help="Archivo de log de headers devueltos por el servidor")

    args = parser.parse_args()

    if args.host:
        host = args.host
    else:
        host = ''

    if args.port:
        port = int(args.port)
    else:
        port = 8080

    if args.configfile:
        configfile = args.configfile
    else:
        configfile = 'server.conf'

    if args.logfile:
        logfile = args.logfile
    else:
        logfile = 'headers.log'

    server = BalancerServer(host=host,port=port,configfile=configfile,logfile=logfile)
    server.run()
