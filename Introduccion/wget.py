#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import urllib
import sys
import os.path
import urlparse
from os import makedirs
from BeautifulSoup import BeautifulSoup
import re
import sqlite3
import json

debug = False # Para que se impriman mensajes de DEBUG

# Manejo de la cache #
######################

def cache_load(cache_file='cache.db'):
    try:
       f = open(cache_file)
    except IOError:
       f = open(cache_file,'w')
       f.write('{}')
       f.close()
       f = open(cache_file)

    encode_json_cache = f.read()
    f.close()

    return json.loads(encode_json_cache)

def cache_save(cache_file='cache.db'):

    global cache
    
    f = open(cache_file,'w')
    f.write(json.dumps(cache))
    f.close()
    
    return True

def esta_en_cache(url_recurso):

    global cache

    return cache.has_key(url_recurso)

def recuperar_last_modified(url_recurso):

    global cache

    return cache[url_recurso]

def set_last_modified(url_recurso, last_modified):

    global cache

    cache[url_recurso] = last_modified

# Funciones para manejar codificacion de URL #
##############################################

def urlEncodeNonAscii(b):
    return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)

def iriToUri(iri):
    parts= urlparse.urlparse(iri)
    return urlparse.urlunparse(
        part.encode('idna') if parti==1 else urlEncodeNonAscii(part.encode('utf-8'))
        for parti, part in enumerate(parts)
    )

# Metodos utiles para trabajar con paths y urls #
#################################################

def is_url(url):
    return bool(urlparse.urlparse(url).scheme)

def create_folder(folder_name):
    # Creamos el directorio base para alojar los archivos y manejamos algunos errores
    try:
        makedirs(folder_name)
        if debug:
            print "Carpeta nueva -> %s" % folder_name
    except OSError, e:
        if e.errno == 17:
            if debug:
                print "Carpeta ./%s ya existe." % folder_name
        elif e.errno == 13:
            raise Exception("Usted no tiene permisos para crear %s. Saliendo." % folder_name)
        else:
            raise Exception("Ocurrio un error al crear %s. Saliendo." % folder_name)

# Metodo generico de descarga de recursos #
###########################################

def descargar_recurso(url,proxy=None):
    opener = urllib.FancyURLopener(proxies=proxy)
    temp,cabecera = opener.retrieve(url)
    if(esta_en_cache(url)):
        last_modified = recuperar_last_modified(url)
        opener.addheader('If-Modified-Since',last_modified)
    respuesta = opener.open(url)
    
    return respuesta

# Recupera todos los recursos de un objeto soup #
#################################################

def recuperar_recursos(soup_object,tag_name):

    global url
    global resource_folder
    global resource_folder_path
    global proxy

    for resource in soup_object.findAll(tag_name):
        # ToDo: Hay que fijarse que no contenga http://
        if debug:
            print "[D]: " + str(resource)

        if resource.has_key('type'):
            if resource['type'] == "application/rss+xml":
                continue

        if resource.has_key('href'):
            enlace_local = resource['href']
            if is_url(enlace_local):
                if os.path.isabs(urlparse.urlparse(enlace_local).path):
                    enlace_local = urlparse.urlparse(enlace_local).path[1:]
                else:
                    enlace_local = urlparse.urlparse(enlace_local).path
            # sobreescribe el enlace para mapear el recurso a la carpeta local
            resource['href'] = os.path.join(resource_folder,enlace_local)
        elif resource.has_key('src'):
            enlace_local = resource['src']
            if is_url(enlace_local):
                if os.path.isabs(urlparse.urlparse(enlace_local).path):
                    enlace_local = urlparse.urlparse(enlace_local).path[1:]
                else:
                    enlace_local = urlparse.urlparse(enlace_local).path
            # sobreescribe el enlace para mapear el recurso a la carpeta local
            resource['src'] = os.path.join(resource_folder,enlace_local)
            
        else:
            continue
        
        if not is_url(enlace_local):
            url_recurso = urlparse.urljoin(url,enlace_local)
            #res_name = os.path.basename(enlace_local)
            path_local = os.path.join(resource_folder_path,enlace_local)

        else:
            url_recurso = enlace_local
            res_path = urlparse.urlparse(enlace_local).path
            if os.path.isabs(res_path):
                path_local = os.path.join(resource_folder_path,res_path[1:])
            else:
                path_local = os.path.join(resource_folder_path,res_path)
        
        try:
            if debug:
                print " Recurso %s" % (url_recurso),
            res_content = descargar_recurso(iriToUri(url_recurso),proxy)
            if debug:
                print " ... OK"

        except IOError, e:
            raise Exception("Ocurrio un error al recuperar %s. Error: %s" % (url_recurso,e))

        # Si el objeto no existe en el servidor, lanza excepcion
        if res_content.getcode() == 404:
            #raise Exception("El objeto %s no existe en el servidor. Error 404." % url_recurso)
            print "[E 404]: %s no existe en el servidor. Error 404." % url_recurso
            continue

        if res_content.getcode() == 304:
            print "[D 304]: %s no modificado, no se descarga." % url_recurso
            continue
        
        # Agrega al recurso a la cache
        if not esta_en_cache(url_recurso):
            set_last_modified(url_recurso,res_content.headers.getheader('Date'))
            print "[D 200]: %s agregado a la cache." % url_recurso
        
        create_folder(os.path.dirname(path_local))
        
        if debug:
            print " Enlace local -> %s" % path_local
            print " Carpeta local -> %s" % os.path.dirname(path_local)
    
        # guarda el recurso #
        #####################
        if debug:
            print " Guardando %s" % (url_recurso)
            print "  en %s." % path_local,
        open(path_local,'w').write(res_content.read())
        if debug:
            print " ... OK"
        

#############################
# Comienza script principal #
#############################

# Parseo y chequeo de parametros #
##################################

parser = argparse.ArgumentParser(description="Script que descarga una URL y todo su contenido (Imagenes, applets).")
parser.add_argument('-u', '--url', help="Url a ser descargada")
parser.add_argument('-f', '--folder', help="Carpeta en donde sera guardada la pagina descargada.")
parser.add_argument('-p', '--proxy', help="Configurar Proxy. Formato: http://proxy_url:port")

args = parser.parse_args()

if args.url:
    url = args.url
else:
    sys.exit('ERROR: Falta parametro -u. Vea -h para mas ayuda!')
    
if args.folder:
    folder = args.folder
else:
    sys.exit('ERROR: Falta parametro -f. Vea -h para mas ayuda!')

if args.proxy:
    proxy = {'http': args.proxy}
else:
    proxy = None

# Definicion del UA #
#####################

# ToDo: ua podria ser un parametro

ua = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12'
urllib.FancyURLopener.version = ua

# Levanta cache #
#################

cache = cache_load()

# construccion de url y recuperacion del contenido original #
#############################################################

#~ params = urllib.urlencode({buscadores[buscador]['search_param'] : args.query})
#~ url = buscadores[buscador]['url'] + params
print "URL -> %s" % url,
respuesta = descargar_recurso(url,proxy)
print " ... OK"

html_content = respuesta.read()
html_soup = BeautifulSoup(html_content)

# creacion de la estructura de archivos para alojar el contenido #
##################################################################

page_name = html_soup.title.string + '.html'

resource_folder = page_name + '_archivos'

page_filename = os.path.join(folder,page_name)
resource_folder_path = os.path.join(folder,resource_folder)

create_folder(resource_folder_path)

# Recuperacion de recursos #
############################

recuperar_recursos(html_soup,'link') # Recupero css
recuperar_recursos(html_soup,'img') # Recupero img
recuperar_recursos(html_soup,'script') # Recupero js

open(page_filename,'w').write(html_soup.prettify());

# Guarda cambios en la cache #
##############################

cache_save()
