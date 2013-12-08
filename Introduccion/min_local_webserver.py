#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import BaseHTTPServer
from urlparse import urlparse
import os.path
import argparse

# Parseo y chequeo de parametros #
##################################

parser = argparse.ArgumentParser(description="Script inicia un servidor web y devuelve una pagina. Tambien genera un log")
parser.add_argument('--host', help="IP del host donde escuchara el servidor", default='0.0.0.0')
parser.add_argument('-l', '--log-file', help="Archivo de log", default='server.log')
parser.add_argument('-p', '--port', help="Puerto donde escuchara el servidor", type=int, default=8000)

args = parser.parse_args()

HOST_NAME = args.host
PORT_NUMBER = args.port
LOGFILE = args.log_file

# Clase que maneja las peticiones al servidor #
###############################################

class ModifiedHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    
    def do_GET(s):
        """Implementa el manejo de peticiones GET al server"""
        # Envio de encabezados HTTP
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
        # Devuelve el recurso al cliente
        s.wfile.write("<html><head><title>Taller 2 :: 2013</title></head>")
        s.wfile.write("<body><h1>Taller Libre 2</h1><h2>Trabajo Practico 1 - Ejercicio 4</h2><p>Pagina de prueba</p>")
        s.wfile.write("<p>El log del servidor es accesible en %s</p>" % os.path.realpath(LOGFILE))
        s.wfile.write("</body></html>")
    
    def log_message(self, format, *args):
        """Genera un log por cada peticion al servidor"""
        open(LOGFILE, "a").write("%s - - [%s] %s\n" %
                            (self.address_string(),
                            self.log_date_time_string(),
                            format%args))

if __name__ == '__main__':
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), ModifiedHandler)
    print "Servidor iniciado en %s:%s. Puede consultar el log con el siguiente comando:" % (HOST_NAME,PORT_NUMBER)
    print '     tail -f "%s"' % os.path.realpath(LOGFILE)
    open(LOGFILE, "a").write("%s Server Starts - %s:%s\n" % (time.asctime(), HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    open(LOGFILE, "a").write("%s Server Stops - %s:%s\n" % (time.asctime(), HOST_NAME, PORT_NUMBER))
