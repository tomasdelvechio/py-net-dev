#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import BaseHTTPServer
from urlparse import urlparse
import os.path
import argparse
import urlparse
import urllib
import re

# Valida la estructura de la URL #
##################################

def is_url(url):
    return bool(urlparse.urlparse(url).scheme)
    
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

# Handler del proxy #
#####################

class ProxyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Implementa el manejo de peticiones GET al server.
        Maneja una web raiz, las respuestas a la consulta (Tanto para rss
            validos como invalidos, y para el caso de otro tipo de consulta
            no valida dentro de las pre-establecidas, devuelve un error 404.
        """
        if self.path == '/':
            # Peticion a la raiz del server
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(self._get_root_page())
        else:
            rss = urlparse.parse_qs(self.path[2:]) # Descarta /?
            if rss.has_key('p'):
                if self.es_valido(rss):
                    # Recuperar RSS
                    self.send_response(200)
                    self.send_header("Content-type", "application/xml")
                    self.end_headers()
                    self.wfile.write(self._get_valid_feed_page(rss))
                else:
                    # RSS invalido
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(self._get_invalid_feed_page(rss))
            else:
                # Si la peticion no esta bien formada, devuelve error 404
                self.send_response(404)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(self._get_error_page())
    
    def log_message(self, format, *args):
        """Genera un log por cada peticion al servidor"""
        open(LOGFILE, "a").write("%s - - [%s] %s\n" %
                            (self.address_string(),
                            self.log_date_time_string(),
                            format%args))
    
    def _get_root_page(self):
        """Genera la pagina cuando se solicita la raiz del server"""
        html = "<html><head><title>Taller 2 :: 2013</title></head>"
        html += "<body><h1>Taller Libre 2</h1><h2>Trabajo Practico 1 - Ejercicio 5 :: Proxy RSS</h2>"
        html += "<form><label for='p'>Fuente de RSS (Formato XML)</label>"
        html += "<input name='p' style='margin-left: 10px;'></input>"
        html += "<button>Consultar</button></form>"
        html += "<br /><h3>Algunos RSS de ejemplo</h3>"
        html += "<a href='/?p=http://clarin.feedsportal.com/c/33088/f/577681/index.rss'>Clarin</a><br />"
        html += "<a href='/?p=http://contenidos.lanacion.com.ar/herramientas/rss/origen=2'>La Nacion</a><br />"
        html += "<a href='/?p=http://www.pagina12.com.ar/diario/rss/ultimas_noticias.xml'>Pagina/12</a><br />"
        html += "<a href='/?p=http://www.nytimes.com/services/xml/rss/nyt/HomePage.xml'>New York Times</a><br />"
        html += "<p style='font-size: 10px;'>El log del servidor es accesible en %s</p>" % os.path.realpath(LOGFILE)
        html += "</body></html>"
        
        return html
    
    def _get_invalid_feed_page(self,rss):
        """Genera la pagina cuando se solicita un feed invalido"""
        url = rss['p'][0]
        html = "<html><head><title>Taller 2 :: 2013</title></head>"
        html += "<body><h1>Feed Invalido</h1>"
        html += "<p>El recurso %s no es un Feed valido.</p>" % url
        html += "<br /><a href='/'>Volver</a>"
        html += "<p style='font-size: 10px;'>El log del servidor es accesible en %s</p>" % os.path.realpath(LOGFILE)
        html += "</body></html>"
        
        return html
        
    def _get_valid_feed_page(self,rss):
        """Recupera el feed y lo devuelve al servidor"""
        url = rss['p'][0]
        opener = urllib.FancyURLopener(proxies=proxy)
        temp,cabecera = opener.retrieve(url)
        try:
            respuesta = opener.open(url)
        except IOError,e:
            # Manejo posibles timeouts, errores de conexion, etc...
            if debug:
                open(LOGFILE, "a").write("[ERROR]: Error inseperado: %s" % e)
                open(LOGFILE, "a").write("  No se recupero %s" % url)
            respuesta = None
        if respuesta:
            xml_content = respuesta.read()
        return xml_content
    
    def _get_error_page(self):
        """Genera la pagina de error 404"""
        html = "<html><head><title>ERROR 404 :: Taller 2 :: 2013</title></head>"
        html += "<body><h1>ERROR 404 :: Taller Libre 2</h1><h2>Trabajo Practico 1 - Ejercicio 5 :: Proxy RSS</h2>"
        html += "<p>La pagina solicitada no existe en el servidor. Consulte %s para mas informacion.</p>" % os.path.realpath(LOGFILE)
        html += "</body></html>"
        
        return html
    
    def es_valido(self, rss_param):
        """Valida que el feed sea valido"""
        url_rss = rss_param['p'][0]
        valido = False
        if is_url(url_rss):
            opener = urllib.FancyURLopener(proxies=proxy)
            temp,cabecera = opener.retrieve(url_rss)
            # El Content-type debe tener application/xml
            if len(re.findall('xml',cabecera.get('Content-type'))) > 0:
                valido = True
        return valido
        
if __name__ == '__main__':
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), ProxyHandler)
    print "Servidor iniciado en %s:%s. Puede consultar el log con el siguiente comando:" % (HOST_NAME,PORT_NUMBER)
    print '     tail -f "%s"' % os.path.realpath(LOGFILE)
    open(LOGFILE, "a").write("%s Server Starts - %s:%s\n" % (time.asctime(), HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    open(LOGFILE, "a").write("%s Server Stops - %s:%s\n" % (time.asctime(), HOST_NAME, PORT_NUMBER))
