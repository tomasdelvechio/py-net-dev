#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import BaseHTTPServer
from urlparse import urlparse
import os.path
import argparse
import urlparse
import urllib
import json

CONFIG_FILE = 'nodos.json' # ToDo, podria ser un parametro opcional :/

    
# Parseo y chequeo de parametros #
##################################

parser = argparse.ArgumentParser(description="Script inicia un servidor web y devuelve una pagina. Tambien genera un log")
parser.add_argument('--host', help="IP del host donde escuchara el servidor", default='0.0.0.0')
parser.add_argument('-l', '--log-file', help="Archivo de log", default='server.log')
parser.add_argument('-p', '--port', help="Puerto donde escuchara el servidor", type=int, default=8000)
parser.add_argument('--proxy', help="Proxy")

args = parser.parse_args()

HOST_NAME = args.host
PORT_NUMBER = args.port
LOGFILE = args.log_file

if args.proxy:
    proxy = {'http': args.proxy}
else:
    proxy = None

# Handler del load balancer #
#############################

class ProxyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    
    queue_index = 0 # Variable de clase para saber cual fue el ultimo server al cual se hizo una peticion
    
    def do_GET(self):
        """Implementa el manejo de peticiones GET al server."""
        if self.path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(self._get_root_page())
        else:
            peticion = urlparse.parse_qs(self.path[2:]) # Descarta /?
            if peticion.has_key('consultar'):
                # Si la peticion es correcta, solicita el server a ser usado, realiza la peticion y la devuelve al cliente
                server = self.next_server()
                url = 'http://'+server['host']+':'+server['port']+'/'
                open(LOGFILE, "a").write("Accediendo a %s" % url)
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(self._get_node_response(url))
            else:
                self.send_response(404)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(self._get_error_page())
            
    def log_message(self, format, *args):
        """Genera un log por cada peticion al servidor"""
        open(LOGFILE, "a").write("%s - - [%s] %s\n" %
                                    ( self.address_string(),
                                      self.log_date_time_string(),
                                      format%args))
    
    def next_server(self):
        """Devuelve al balancer cual es el siguiente server a ser consultado."""
        nodes = json.loads(open(CONFIG_FILE).read()) # Levantar json file
        ProxyHandler.queue_index = (self.queue_index + 1) % len(nodes) # Implementacion sencilla de Round Robin, cuando llegue al ultimo indice, devuelve 0.
        node_names = nodes.keys()
        return nodes[node_names[ProxyHandler.queue_index]]
    
    def _get_root_page(self):
        """Genera la pagina cuando se solicita la raiz del server"""
        html = "<html><head><title>Taller 2 :: 2013</title></head>"
        html += "<body><h1>Taller Libre 2</h1><h2>Trabajo Practico 1 - Ejercicio 6 :: Balanceo de carga</h2>"
        html += "<p>Realice una consulta</p>"
        html += "<form> <input type='submit' value='Consultar' name='consultar'></form>"
        html += "</body></html>"
        
        return html
        
    def _get_node_response(self,url):
        """Recupera el recurso del nodo y lo devuelve al servidor."""
        opener = urllib.FancyURLopener(proxies=proxy)
        temp,cabecera = opener.retrieve(url)
        try:
            respuesta = opener.open(url)
        except IOError,e:
            if debug:
                open(LOGFILE, "a").write("[ERROR]: Error inseperado: %s" % e)
                open(LOGFILE, "a").write("  No se recupero %s" % url)
            respuesta = None
        if respuesta:
            response = respuesta.read()
        return response
    
    def _get_error_page(self):
        """Genera la pagina de error 404"""
        html = "<html><head><title>ERROR 404 :: Taller 2 :: 2013</title></head>"
        html += "<body><h1>ERROR 404 :: Taller Libre 2</h1><h2>Trabajo Practico 1 - Ejercicio 6 :: Proxy Reverso</h2>"
        html += "<p>La pagina solicitada no existe. Consulte %s para mas informacion.</p>" % os.path.realpath(LOGFILE)
        html += "</body></html>"
        
        return html
        
if __name__ == '__main__':
    
    server_class = BaseHTTPServer.HTTPServer
    proxyd = server_class((HOST_NAME, PORT_NUMBER), ProxyHandler)
    
    print "Proxy iniciado en %s:%s." % (HOST_NAME,PORT_NUMBER)
    print "Puede consultar el log con el siguiente comando:"
    print '     tail -f "%s"' % os.path.realpath(LOGFILE)
    
    open(LOGFILE, "a").write("%s Proxy Starts - %s:%s\n" % (time.asctime(), HOST_NAME, PORT_NUMBER))
    
    try:
        proxyd.serve_forever()
    except KeyboardInterrupt:
        pass
    proxyd.server_close()
    
    open(LOGFILE, "a").write("%s Proxy Stops - %s:%s\n" % (time.asctime(), HOST_NAME, PORT_NUMBER))
