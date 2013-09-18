import socket
import sys
import re
import zlib
from urlparse import urlparse

if(len(sys.argv) < 2):
    sys.exit("Forma de ejecucion: python %s <url> [<port>]." % sys.argv[0])

resource = urlparse(sys.argv[1])
if resource.scheme is '':
    sys.exit("Formato de url incorrecto. Formato esperado: (http|ftp|https)://url[:port][/path_to_resource]")

if(len(sys.argv) < 3):
    if resource.port is None:
        PORT = 80
    else:
        PORT = resource.port
else:
    PORT = int(sys.argv[2])

if resource.hostname is '':
    HOST = 'localhost'
else:
    HOST = resource.hostname

if resource.path is '':
    GET = '/'
else:
    GET = resource.path

LOGFILE='http.log'

# Creacion del socket y conexion con el server #
################################################

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
  s.connect((HOST , PORT))
except socket.error, msg:
  sys.stderr.write("[ERROR] %s\n" % msg[1])
  sys.exit(2)

# Construyo el request HTTP y envio al server, recibiendo la respuesta #
########################################################################

request = """GET %s HTTP/1.1\r
Host: %s\r
User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:23.0) Gecko/20100101 Firefox/23.0\r
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r
Accept-Language: es-ar,es;q=0.8,en-us;q=0.5,en;q=0.3\r
Accept-Encoding: gzip, deflate\r
Connection: keep-alive\r\n\n"""

s.sendall(request % (GET,HOST))
response = s.recv(4096)
data = ""
while len(response):
    data += response
    response = s.recv(4096)

s.close()

# Separo el header y el content #
#################################

header = data.split('\r\n\r\n')[0]
headers = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", header)) # Armo un dic con los headers

split_content = data.split('\r\n\r\n')[1:]
content = ''.join(split_content)
decompress_content = zlib.decompress(content,  16+zlib.MAX_WBITS)

# Salida #
##########

# Headers a un log
f = open(LOGFILE,'a')
f.write("HEADER: Response from %s\n" % HOST)
f.write("%s\n" % header)
f.close()

# Content por salida estandar
print decompress_content

sys.exit(0)

