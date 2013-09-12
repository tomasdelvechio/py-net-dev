#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import urllib
import sys
import os.path
import urlparse
from os import makedirs,chdir
from BeautifulSoup import BeautifulSoup
import re
import uuid
#~ import sqlite3
import json
import datetime
import SimpleHTTPServer
import SocketServer

# Valida la estructura de la URL #
##################################

def is_url(url):
    return bool(urlparse.urlparse(url).scheme)

# Manejo del sistema de archivos #
##################################

def create_folder(folder_name):
    # Creamos el directorio base para alojar los archivos y manejamos algunos errores
    try:
        makedirs(folder_name)
        if debug:
            print "[DEBUG]: Carpeta nueva -> %s" % folder_name
    except OSError, e:
        if e.errno == 17:
            if debug:
                print "[DEBUG]: Carpeta ./%s ya existe." % folder_name
        elif e.errno == 13:
            raise Exception("Usted no tiene permisos para crear %s. Saliendo." % folder_name)
        else:
            raise Exception("Ocurrio un error al crear %s. Saliendo." % folder_name)

# Metodo generico de descarga de recursos #
###########################################

def descargar_recurso(url,proxy=None,only_content_type=None):
    if len(re.findall('(jpg|png|jpeg|gif|pdf|tiff|iso|doc|xls|odt|ods)',url)) == 0 and is_url(url):
        opener = urllib.FancyURLopener(proxies=proxy)
        temp,cabecera = opener.retrieve(url)
        if debug:
            print "[DEBUG]: Content-type: %s" % cabecera.get('Content-type')
        if only_content_type:
            if len(re.findall(only_content_type,cabecera.get('Content-type'))) > 0:
                respuesta = opener.open(url)
            else:
                respuesta = None
        else:
            respuesta = opener.open(url)
    else:
        respuesta = None
    return respuesta

# Funciones para construccion de estadisticas del crawling #
############################################################

def estadisticas(url,soup_object,informe):
    
    if not informe.has_key('urls'):
        informe['urls'] = {}
    informe['urls'][url] = {}
    informe['urls'][url]['img'] = len(soup_object.findAll('img'))
    informe['urls'][url]['div'] = len(soup_object.findAll('div'))
    informe['urls'][url]['p'] = len(soup_object.findAll('p'))
    informe['urls'][url]['h1'] = len(soup_object.findAll('h1'))
    informe['urls'][url]['h2'] = len(soup_object.findAll('h2'))
    informe['urls'][url]['h3'] = len(soup_object.findAll('h3'))
    informe['urls'][url]['meta'] = len(soup_object.findAll('meta'))
    informe['urls'][url]['link'] = len(soup_object.findAll('link'))
    informe['urls'][url]['script'] = len(soup_object.findAll('script'))
    informe['urls'][url]['a'] = len(soup_object.findAll('a'))
    informe['urls'][url]['ul'] = len(soup_object.findAll('ul'))
    informe['urls'][url]['form'] = len(soup_object.findAll('form'))
    informe['urls'][url]['span'] = len(soup_object.findAll('span'))
    informe['urls'][url]['a'] = len(soup_object.findAll('a'))
    return True

def realizar_informe(informe):
    
    if informe['folder']:
        path_informe = os.path.join(informe['folder'],'informe.html')
    else:
        create_folder('resultados')
        path_informe = 'resultados/informe.html'
    
    f = open(path_informe,'w')
    f.write('<h1>Trabajo Practico 1 :: Taller Libre 2</h1>');
    f.write('<h2>Ejercicio 3</h2>');
    f.write('<p>Estudiante: Tomas Delvechio - 95346</p>');
    f.write('<h3>Resumen General del Crawling</3>');
    f.write(""" <table border="1">
                    <tr>
                        <td>
                            Fecha
                        </td>
                        <td>
                            %s
                        </td>
                    </tr>
                    <tr>
                        <td>
                            Profundidad
                        </td>
                        <td>
                            %s
                        </td>
                    </tr>
                    <tr>
                        <td>
                            Semilla
                        </td>
                        <td>
                            %s
                        </td>
                    </tr>
                    <tr>
                        <td>
                            URLs crawleadas
                        </td>
                        <td>
                            %s
                        </td>
                    </tr>
                    <tr>
                        <td>
                            Fallos
                        </td>
                        <td>
                            %s
                        </td>
                    </tr>
                    <tr>
                        <td>
                            Cantidad de URLs en la siguiente iteracion
                        </td>
                        <td>
                            %s
                        </td>
                    </tr>
                </table>""" % (str(informe['fecha']),str(informe['depth']),str(informe['seed']),str(informe['cantidad_total']),str(informe['fallos']),str(informe['urls_next_iter'])))
    f.write('<h3>Resumen detallado por URL</3>');
    f.write('<table border="1">');
    f.write(""" <tr>
                    <td>URL</td>
                    <td>Enlaces</td>
                    <td>Imagenes</td>
                    <td>Scripts</td>
                    <td>Link</td>
                    <td>div</td>
                    <td>span</td>
                    <td>h1</td>
                    <td>h2</td>
                    <td>h3</td>
                    <td>meta</td>
                    <td>Listas</td>
                    <td>Formularios</td>
                    <td>Parrafos</td>
                </tr>""")
    for url in informe['urls'].keys():
        f.write('<tr><td>%s</td>' % url)
        f.write('<td>%s</td>' % informe['urls'][url]['a'])
        f.write('<td>%s</td>' % informe['urls'][url]['img'])
        f.write('<td>%s</td>' % informe['urls'][url]['script'])
        f.write('<td>%s</td>' % informe['urls'][url]['link'])
        f.write('<td>%s</td>' % informe['urls'][url]['div'])
        f.write('<td>%s</td>' % informe['urls'][url]['span'])
        f.write('<td>%s</td>' % informe['urls'][url]['h1'])
        f.write('<td>%s</td>' % informe['urls'][url]['h2'])
        f.write('<td>%s</td>' % informe['urls'][url]['h3'])
        f.write('<td>%s</td>' % informe['urls'][url]['meta'])
        f.write('<td>%s</td>' % informe['urls'][url]['ul'])
        f.write('<td>%s</td>' % informe['urls'][url]['form'])
        f.write('<td>%s</td>' % informe['urls'][url]['p'])
        #~ for elemento in informe['urls'][url]:
            #~ f.write('<td>%s</td>' % elemento)
        #~ print informe['urls'][url]
        f.write('</tr>')
    f.close()
    return path_informe

#############################
# Comienza script principal #
#############################

# Parseo y chequeo de parametros #
##################################

parser = argparse.ArgumentParser(description="Script que crawlear una porcion de la web a partir de una URL y profundidad")
parser.add_argument('-u', '--url', help="Url semilla del crawler")
parser.add_argument('-d', '--depth', help="Profundidad del crawling", type=int)
parser.add_argument('-f', '--folder', help="Carpeta de descarga de html. Si no se pasa como parametro, se simula el crwaling (Se recorren las urls pero no se guardan a disco).")
parser.add_argument('-p', '--proxy', help="Configurar Proxy. Formato: http://proxy_url:port")
parser.add_argument('--debug', help="Modo debug")

args = parser.parse_args()

# Activa/Desactiva el modo debug
if args.debug:
    debug = True
else:
    debug = False

if args.url:
    url = args.url
else:
    sys.exit('ERROR: Falta parametro -u. Vea -h para mas ayuda!')

# Reviso la profundidad pasada por parametro
if hasattr(args, 'depth'):
    if args.depth < 0:
        depth = 0
    else:
        depth = args.depth
else:
    sys.exit('ERROR: Falta parametro -d. Vea -h para mas ayuda!')
    
if args.folder:
    folder = args.folder
    create_folder(folder) # Carpeta de descarga de archivos recuperados
else:
    folder = None # Modo simulado (No se guardan las paginas recuperadas)

if args.proxy:
    proxy = {'http': args.proxy}
else:
    proxy = None

# Definicion del UA #
#####################

# ToDo: ua podria ser un parametro
ua = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12'
urllib.FancyURLopener.version = ua

# Proceso de crawling #
#######################

profundidad_actual = 0 # Indica la profundidad actual del crawling
urls = {} # Dic de urls a recorrer y ya recorridas.
# Inicializo la lista de urls con la frontera
urls[url] = {'level':0,'visited':False}
# Creamos un indice para mapear nombres con urls
indice = {} # Para tener un mapeo entre nombre de archivo y url
# Variables para informes
informe = {}
informe['cantidad_total'] = 0
informe['fallos'] = 0

# Mientras no alcanzemos la profundidad tope, crawlear
while (profundidad_actual <= depth):
    # Genera un nuevo dic con las urls a ser recorridas en el nivel actual
    #   claramente es ineficiente, pero habia un motivo para esto
    # No se podia recorrer el dic urls directamente debido a que este 
    #   es modificado dentro del ciclo, y eso daria un error en python.
    urls_nivel_actual = {url: urls[url] for url in urls.keys() if urls[url]['level'] == profundidad_actual }
    
    if(len(urls_nivel_actual.keys()) > 0):
        print "Crawling depth: %s" % profundidad_actual
    
    for url_actual,info_url_actual in urls_nivel_actual.iteritems():
        # Si el nivel actual no supera al maximo y la url aun no fue visitada, recuperarla
        if (info_url_actual['level'] <= depth) and not (info_url_actual['visited']):
            print "  Recuperando %s" % url_actual
            try:
                respuesta = descargar_recurso(url_actual,proxy,only_content_type='text/html')
            except IOError,e:
                # Casos en donde falla: URL caida o no accesible, timeouts, etc...
                if debug:
                    print "[ERROR]: Error inseperado: %s" % e
                informe['fallos'] += 1
                print "  No se recupero %s" % url_actual
                respuesta = None
            
            # Si se pudo recuperar la pagina, la procesa
            if respuesta:
                html_content = respuesta.read()
                html_soup = BeautifulSoup(html_content.decode('ascii', 'ignore'))
                informe['cantidad_total'] += 1
                # Cada enlace en la pagina debe ser analizado como posible url a ser crawleada
                for nueva_url in html_soup.findAll('a'):
                    # Si la url tiene algun enlace
                    if nueva_url.has_key('href'):
                        # Manejo los casos en que tengo urls relativas
                        if not is_url(nueva_url['href']):
                            nueva_url['href'] = urlparse.urljoin(url_actual,nueva_url['href'])
                            if debug:
                                "   URL reparada: %s" % nueva_url['href']
                        # Si la url no fue ya agregada al crawler y ademas es valida sintacticamente, la encolo
                        if not urls.has_key(nueva_url['href']) and is_url(nueva_url['href']):
                            urls[nueva_url['href']] = {'level': profundidad_actual+1, 'visited':False}
                # Si folder no es None, no es modo simulacion y debemos guardar el html recuperado
                if folder:
                    # Genero nombres de archivos univocos
                    page_name = str(uuid.uuid4()) + '.html'
                    page_filename = os.path.join(folder,page_name)
                    open(page_filename,'w').write(html_soup.prettify())
                    indice[page_name] = url_actual
                estadisticas(url_actual,html_soup,informe)
            info_url_actual['visited'] = True # Si todo salio bien, doy la url por visitada
    profundidad_actual += 1 # Paso al siguiente nivel

# Guardo el indice #
####################

f = open('indice.txt','w')
f.write(json.dumps(indice))
f.close()

# Generacion del informe #
##########################

informe['urls_next_iter'] = len({url: urls[url] for url in urls.keys() if urls[url]['level'] == profundidad_actual })
informe['fecha'] = datetime.date.today().ctime()
informe['depth'] = depth
informe['seed'] = url
informe['folder'] = folder

path_informe = realizar_informe(informe)

os.chdir(os.path.dirname(path_informe))

# Publicacion del informe en un servidor web ad-hoc #
#####################################################

PORT = 8000
Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
httpd = SocketServer.TCPServer(("", PORT), Handler)

print "Crawling finalizado. Podra ver un informe con los resultados en http://localhost:%i/%s  Para terminar con el programa presione CTRL+C." % (PORT,os.path.basename(path_informe))
httpd.serve_forever()
