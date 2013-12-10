#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import socket
import os
import select
import re
import json
import argparse

debug = False

class HttpServer(object):
    
    def __init__(self, host='', port=8080, proxy=None, logfile='headers.log', configfile='server.conf', rootdir=None):
        # Server vars
        self.proxy = proxy
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

        if rootdir is not None:
            if os.path.exists(rootdir) and os.path.isdir(rootdir):
                self.config["root"] = rootdir

    def load_config(self, configfile):
        try:
            with open(configfile) as f:
               config = f.read()
               return json.loads(config)
        except IOError:
            sys.exit('Archivo de configuracion no existe o el proceso no posee los permisos necesarios para leerlo. Path: %s' % os.path.abspath(configfile))
        except ValueError:
            sys.exit('Formato del archivo de configuracion incorrecto. Path: %s' % os.path.abspath(configfile))

    def receive_request(self, socket):
        data = socket.recv(self.buffer)
        while len(data) == self.buffer:
            data += socket.recv(self.buffer)
        return data

    def header_valido(self, header):
        #Valida:
        #   Que al menos tenga la Request-Line
        #   Que sea un dict
        if not (type(header) == type(dict())):
            return False
        if not header.has_key('Request-Line'):
            return False
        return True

    def get_header(self, request):
        """Metodo que detecta si en la descarga se encuentra el header.
            En caso afirmativo, lo detecta y parsea."""
        headers = request.split(self.separador)
        request_line = headers[0].split(self.h_separador)[0]
        
        # Si len es mayor a 1, el header ya esta completo
        if len(headers) > 1:
            dic_headers = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", headers[0])) # Arma un dic con los headers
            dic_headers['Request-Line'] = request_line # Agregamos la linea con el recurso solicitado
            return dic_headers
        else:
            return False

    def get_root_path(self):
        return os.path.abspath(self.config['root'])

    def get_full_path_content(self,relative_path):
        root_directory = self.get_root_path()
        if relative_path == '/':
            relative_path = self.config['default_page_name']
        return os.path.normpath('/'.join([root_directory,relative_path]))

    def get_full_path_error_content(self):
        root_directory = self.get_root_path()
        error_content_name = self.config['error_page']
        return os.path.normpath('/'.join([root_directory,error_content_name]))

    def get_full_path_forbidden_content(self):
        root_directory = self.get_root_path()
        forbidden_content_name = self.config['forbidden_page']
        return os.path.normpath('/'.join([root_directory,forbidden_content_name]))

    def content_exists(self, path):
        full_content_path = self.get_full_path_content(path)
        try:
            with open(full_content_path) as f:
               return True
        except IOError:
            return False

    def get_error_content(self):
        full_path_error_content = self.get_full_path_error_content()
        try:
            with open(full_path_error_content) as f:
               return f.read()
        except IOError:
            return self.config['default_error_html']

    def get_error_headers(self):
        print '   %s 404 Not Found' % self.http_version
        return self.h_separador.join([  '%s 404 Not Found' % self.http_version,
                                        'Content-Type: text/html',
                                        self.h_separador    ])

    def get_forbidden_content(self):
        full_path_forbidden_content = self.get_full_path_forbidden_content()
        try:
            with open(full_path_forbidden_content) as f:
               return f.read()
        except IOError:
            return self.config['default_forbidden_html']

    def get_forbidden_headers(self):
        print '   %s 403 Forbidden' % self.http_version
        return self.h_separador.join([  '%s 403 Forbidden' % self.http_version,
                                        'Content-Type: text/html',
                                        self.h_separador    ])

    def get_content(self, path):
        
        if self.content_exists(path):
            full_content_path = self.get_full_path_content(path)
            try:
                with open(full_content_path) as f:
                   return f.read()
            except IOError:
                return False
        else:
            return False

    def get_response_headers(self, path):

        if self.content_exists(path):
            print '   %s 200 OK' % self.http_version
            headers = self.h_separador.join([   '%s 200 OK' % self.http_version,
                                                self.h_separador    ])
        else:
            headers = self.get_error_headers()
        return headers

    def is_dir(self, path):
        abs_path = self.get_full_path_content(path)
        return os.path.isdir(abs_path)

    def get_resource(self, request_headers): 
        if request_headers.has_key('Request-Line'):

            # Parseamos la linea de la peticion
            method, resource, version = request_headers['Request-Line'].split()

            if method == 'GET':
                content = self.get_content(resource)
                is_dir = self.is_dir(resource)

            if content:
                headers = self.get_response_headers(resource)
            elif is_dir:
                headers = self.get_forbidden_headers()
                content = self.get_forbidden_content()
            else:
                headers = self.get_error_headers()
                content = self.get_error_content()
        else:
            # Error
            content = self.get_error_content()
            headers = self.get_error_headers()

        return content, headers

    def dispatcher_request(self, request):
        request_headers = self.get_header(request)
        if request_headers.has_key('Request-Line'):
            print "   %s" % request_headers['Request-Line']
        if self.header_valido(request_headers):
            content, response = self.get_resource(request_headers)
            # Solo entrara en caso que sea GET
            if content:
                response += content
            return response
        else:        
            return False
    
    def run(self):
        # Arma socket de servidor
        self.sock_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock_server.bind((self.host,self.port))
        self.sock_server.listen(self.backlog)
        self.sock_input = [self.sock_server, sys.stdin]

        print "Servidor iniciado en %s:%s" % (self.host is not '' if self.host else '0.0.0.0',self.port)

        while True:
            lst_input,lst_output,lst_error = select.select(self.sock_input,[],[])

            for s in lst_input:

                if s == self.sock_server:
                    client, address = self.sock_server.accept()
                    if debug:
                        print "Se ha conectado %s:%s" % address
                    self.sock_input.append(client)

                elif s == sys.stdin:
                    keyWord = sys.stdin.readline()
                    #break
                    pass

                else:
                    # Procesa la request
                    print "Peticion de: %s:%s" % s.getpeername()
                    request = self.receive_request(s)
                    if request:
                        response = self.dispatcher_request(request)
                        s.sendall(response)
                    s.close()
                    self.sock_input.remove(s)
            
        self.sock_server.close() 
        
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script que inicia un web server, segun los parametros proporcionados.")
    parser.add_argument('-i', '--host', help="Host donde escuchara el web server. 0.0.0.0 por defecto.")
    parser.add_argument('-p', '--port', help="Numero de puerto donde escuchara el web server. 8080 por defecto.")
    parser.add_argument('-c', '--configfile', help="Archivo de configuracion del servidor.")
    parser.add_argument('-l', '--logfile', help="Archivo de log de headers devueltos por el servidor")
    parser.add_argument('-r', '--rootdir', help="Carpeta raiz del web server. Debe existir. Por defecto, la actual.")

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

    if args.rootdir:
        rootdir = args.rootdir
    else:
        rootdir = None

    server = HttpServer(host=host,port=port,configfile=configfile,logfile=logfile,rootdir=rootdir)
    server.run()

    # Ejemplos:
    # python http_server.py -p 8080 -r 'www1'
    # python http_server.py -p 8081 -r 'www2'
    # python http_server.py -p 8082 -r 'www3'