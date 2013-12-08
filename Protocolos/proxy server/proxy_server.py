#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import socket
import os
import select
import re
import json
from http_client import HttpClient
from threading import Thread
import signal
import collections

debug = False

class ProxyThread(Thread):
    """Implementa un mini cliente, para realizar descargas en paralelo de las peticiones"""
    def __init__(self,s,cache,cache_dir,cache_len):
        Thread.__init__(self)
        self.s = s
        self.buffer = 4096
        self.separador = '\r\n\r\n' # Separador de header y content de la respuesta HTTP
        self.h_separador = '\r\n'

        # Client vars
        self.headers = {}
        self.requests = {}
        self.cache = cache
        self.cache_len = int(cache_len)
        self.cache_dir = cache_dir

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

    def receive_request(self, socket):
        data = socket.recv(self.buffer)
        while len(data) == self.buffer:
            data += socket.recv(self.buffer)
        return data

    def dispatcher_request(self, request, s):

        request_headers = self.get_header(request)

        # Guardamos el request en la variable global headers
        peername = s.getpeername()
        self.headers[peername] = { 'str' : request, 'dic' : request_headers}

        if self.header_valido(request_headers):
            self.get_resource(s)
            return True
        else:        
            return False

    def en_cache(self, resource):
        return self.cache.has_key(resource)

    def get_from_cache(self, resource):
        #print "   [C]: Recurso", resource
        if self.en_cache(resource):
            filename = self.cache[resource]['filename']
            header = self.cache[resource]['header']
            return filename, header

    def set_to_cache(self, resource, filename, header):
        self.cache[resource] = {}
        self.cache[resource]['filename'] = filename
        self.cache[resource]['header'] = header
        # Si la cache supera el limite, eliminar el elemento mas viejo
        if(len(self.cache)>self.cache_len):
            # Elimina el elemento mas viejo
            older_element_key = self.cache.keys()[0]
            self.remove_from_cache(older_element_key)
        return True

    def remove_from_cache(self, resource):
        try:
            os.remove(self.cache[resource]['filename'])
        except:
            pass # Puede pasar que el archivo no exista, etc...
        self.cache.pop(resource)
        return True

    def adaptar_header(self, header):
        # Transformar el header en un dic
        # Modificar los campos necesarios
        # Transformarlo de nuevo en un str y retornarlo
        headers = header.split(self.h_separador)

        # En la response line, cambiamos la version del protocolo
        response_line = headers[0].split()
        response_line[0] = 'HTTP/1.0'
        headers[0] = " ".join(response_line)

        # Quitamos el parametro Conection: keep-alive
        try:
            headers.remove('Connection: keep-alive')
        except Exception:
            try:
                headers.remove('Connection: Keep-Alive')
            except Exception:
                pass

        new_header = self.h_separador.join(headers)
        return new_header

    def get_content(self, s):
        
        # Instancia el cliente para el peer, y hace la peticion.

        request_headers = self.headers[s.getpeername()]['str']
        #url = self.headers[s.getpeername()]['dic']['Host']
        method, resource, version = self.headers[s.getpeername()]['dic']['Request-Line'].split()
        if self.en_cache(resource):
            filename, header = self.get_from_cache(resource)
        else:
            client = HttpClient(download_dir=self.cache_dir)
            filename, header = client.retrieve_con_headers(request_headers, resource, method)
            header = self.adaptar_header(header)
            self.set_to_cache(resource,filename,header)

        self.requests[s.getpeername()] = {}
        self.requests[s.getpeername()]['filename'] = filename
        self.requests[s.getpeername()]['header'] = header

        return True

    def get_resource(self, s): 

        if self.get_content(s):
            return True

    def header_valido(self, header):
        #Valida:
        #   Que al menos tenga la Request-Line
        #   Que sea un dict
        if not (type(header) == type(dict())):
            return False
        if not header.has_key('Request-Line'):
            return False
        if not header.has_key('Host'):
            return False
        return True

    def run(self):

        while True:
            request = self.receive_request(self.s)
            if self.dispatcher_request(request,self.s):
                filename = self.requests[self.s.getpeername()]['filename']
                headers = self.requests[self.s.getpeername()]['header']
                headers += '\r\n\r\n'
                try:
                    if filename is not None:
                        with open(filename) as f:
                            #content += f.read()
                            content = f.read()
                    else:
                        content = ""
                    self.s.sendall(headers.encode('utf-8')+content)
                except IOError as e:
                    # Hubo algun error, el archivo no esta, pero esta en el indice de la cache, asi que lo borramos del indice
                    method, resource, version = self.headers[self.s.getpeername()]['dic']['Request-Line'].split()
                    self.remove_from_cache(resource)
                    # Ahora hay que recuperarlo de nuevo
                    self.dispatcher_request(request,self.s)
                break


class ProxyServer(object):
    
    def __init__(self, host='', port=8080, proxy=None, logfile='headers.log', configfile='server.conf', cachefile='cache.db'):
        # Server vars
        self.proxy = proxy
        self.LOGFILE = logfile
        self.http_version = "HTTP/1.0"
        self.h_separador = '\r\n'
        self._header_detected = False

        # socket vars
        self.backlog = 6
        self.host = host
        self.port = port

        # Config vars
        self.config = self.load_config(configfile)
        self.cachefile = cachefile
        self.cache = collections.OrderedDict(self.load_cache(cachefile))

        if not os.path.exists(self.config['cache_dir']):
            os.makedirs(self.config['cache_dir'])

    def load_config(self, configfile):
        try:
            with open(configfile) as f:
               config = f.read()
               return json.loads(config)
        except IOError:
            sys.exit('Archivo de configuracion no existe o el proceso no posee los permisos necesarios para leerlo. Path: %s' % os.path.abspath(configfile))
        except ValueError:
            sys.exit('Formato del archivo de configuracion incorrecto. Path: %s' % os.path.abspath(configfile))

    def load_cache(self, cachefile):
        try:
            with open(cachefile) as f:
               cache = f.read()
               return json.loads(cache)
        except IOError:
            sys.exit('Archivo de configuracion no existe o el proceso no posee los permisos necesarios para leerlo. Path: %s' % os.path.abspath(cachefile))
        except ValueError:
            sys.exit('Formato del archivo de configuracion incorrecto. Path: %s' % os.path.abspath(cachefile))

    def save_cache(self):
        try:
            with open(self.cachefile, 'w') as f:
                f.write(json.dumps(self.cache))
                return True
        except IOError:
            sys.exit('Archivo de configuracion no existe o el proceso no posee los permisos necesarios para leerlo. Path: %s' % os.path.abspath(cachefile))
        except ValueError:
            sys.exit('Formato del archivo de configuracion incorrecto. Path: %s' % os.path.abspath(cachefile))

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

    def open_socket(self):

        sock_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_server.bind((self.host,self.port))
        sock_server.listen(self.backlog)
        sock_input = [sock_server, sys.stdin]
        return sock_server, sock_input

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
                        h = ProxyThread(s,self.cache,self.config["cache_dir"],self.config["cache_len"]).start()
                        hilos.append(h)
                        self.sock_input.remove(s)
        except KeyboardInterrupt:
            print "\n [S]: Cerrando el servidor"
            self.sock_server.close()
            print " [S]: Cerrando hilos"
            #for h in hilos:
                #h.s.close()
                #h.join()
            print " [S]: Sincronizando cache"
            self.save_cache()
            
        
if __name__ == "__main__":
    server = ProxyServer()
    server.run()