#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import urllib
import sys

# Definicion de parametros #
############################

parser = argparse.ArgumentParser(description="Script que realiza queries a Google y Yahoo.")
parser.add_argument('-q', '--query', help="Consulta a realizar. String entre comillas (simples o dobles). Si se consulta un termino simple (sin espacios), las comillas no son necesarias.")
parser.add_argument('-b', '--buscador', default='google', help="Motor de busqueda donde ejecutar la consulta. Disponibles: google, yahoo. Default: google.")
parser.add_argument('-p', '--proxy', help="Configurar Proxy. Formato: http://proxy_url:port")
parser.add_argument('-o', '--output', help="Archivo de salida. Default: STDOUT. Si el archivo existe, lo sobreescribe.")

# Chequeo de parametros #
#########################

args = parser.parse_args()

if args.query:
    query = args.query
else:
    sys.exit('ERROR: Falta parametro -q. Vea -h para mas ayuda!')

buscador = args.buscador

if args.output:
    output_file = args.output
else:
    output_file = None

if args.proxy:
    proxy = {'http': args.proxy}
else:
    proxy = None

# Definicion del UA #
#####################

# ToDo: ua podria ser un parametro

ua = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12'
#~ ua = 'app/1.0'
urllib.FancyURLopener.version = ua

# definimos search engines diponibles #
#######################################

buscadores = {'google': {'url': 'http://www.google.com.ar/search?', 'search_param': 'q'}, 'yahoo': {'url': 'http://search.yahoo.com/search?', 'search_param': 'q'} }

# construccion de url y ejecucion de la consulta #
##################################################

params = urllib.urlencode({buscadores[buscador]['search_param'] : args.query})
url = buscadores[buscador]['url'] + params

if buscador in buscadores.keys():
    if proxy is not None:
        query_res = urllib.urlopen(url,proxies=proxy)
    else:
        query_res = urllib.urlopen(url)

if output_file:
    open(output_file, 'w').write(query_res.read())
else:
    print query_res.read()
