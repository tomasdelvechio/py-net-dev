#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import socket
import os
import select
import re
import json

debug = True

class HttpServer(object):
    
    def __init__(self, host='', port=8080, proxy=None, logfile='headers.log', configfile='server.conf'):
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

    def load_config(self, configfile):
        try:
            with open(configfile) as f:
               config = f.read()
               return json.loads(config)
        except IOError:
            raise Exception('Archivo de configuracion no existe o el proceso no posee los permisos necesarios para leerlo. Path: %s' % os.path.abspath(configfile))
        except ValueError:
            raise Exception('Formato del archivo de configuracion incorrecto. Path: %s' % os.path.abspath(configfile))

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
        return self.h_separador.join([  '%s 404 Not Found' % self.http_version,
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
            headers = self.h_separador.join([   '%s 200 OK' % self.http_version,
                                                self.h_separador    ])
        else:
            headers = self.get_error_headers()
        return headers

    def get_resource(self, request_headers): 
        if request_headers.has_key('Request-Line'):

            # Parseamos la linea de la peticion
            method, resource, version = request_headers['Request-Line'].split()

            if method == 'GET':
                content = self.get_content(resource)

            if content:
                headers = self.get_response_headers(resource)
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
        if debug:
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
                    response = self.dispatcher_request(request)
                    s.sendall(response)
                    s.close()
                    self.sock_input.remove(s)
            
        self.sock_server.close() 
        
        
if __name__ == "__main__":
    server = HttpServer()
    server.run()