from http_client_object import HttpClient
import argparse

parser = argparse.ArgumentParser(description="Script descarga un recurso a traves de un servidor HTTP.")
parser.add_argument('-u', '--url', help="Url a descargar")
parser.add_argument('-p', '--proxy', help="Configurar Proxy. Formato: http://proxy_url:port")
parser.add_argument('-m', '--method', help="Metodo HTTP de descarga. Soporta actualmente GET y HEAD")
parser.add_argument('-l', '--logfile', help="Archivo de log de headers devueltos por el servidor")

args = parser.parse_args()

if args.url:
    url = args.url
else:
    sys.exit('ERROR: Falta parametro -u. Vea -h para mas ayuda!')

# Set logfile
if args.logfile:
    logfile = args.logfile
else:
    logfile = None
    
# Set logfile
if args.proxy:
    proxy = args.proxy
else:
    proxy = None

# Set method
if args.method:
    if args.method.upper() in ('GET','HEAD'):
        method = args.method.upper()
    else:
        method = None
else:
    method = None

# Descarga del recurso #
########################

client = HttpClient(proxy=proxy,logfile=logfile)
print "Descargando %s" % url
if method:
    client.retrieve(url,method=method)
else:
    client.retrieve(url)
