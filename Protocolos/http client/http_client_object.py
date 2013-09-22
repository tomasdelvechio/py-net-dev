from urlparse import urlparse
import sys
import socket
import os
import re

class HttpClient:
    
    def __init__(self,proxy=None,logfile='headers.log'):
        self.proxy = proxy
        self.LOGFILE = logfile
        self.parsed_url = None # Instance of class urlparse
        self.http_version = "HTTP/1.1"
        self.buffer = 4096
        self.separador = '\r\n\r\n' # Separador de header y content de la respuesta HTTP
        self.download_file = 'download.part'
        self.__header_detected = False
        self.__url = None
        try:
            # Si quedo una descarga trunca, la limpiamos
            with open(self.download_file):
                os.remove(self.download_file)
        except IOError:
            pass
        
    def _get_host(self):
        """Devuelve el hostname de la url de forma inteligente(?)"""
        if self.parsed_url is None:
            return 'localhost'
        else:
            if self.parsed_url.hostname in (None,''):
                return 'localhost'
            else:
                return self.parsed_url.hostname
            
    
    def _get_port(self):
        """Devuelve el puerto de la url de forma inteligente(?)"""
        if self.parsed_url is None:
            return 80
        else:
            if self.parsed_url.port in (None,''):
                return 80
            else:
                return self.parsed_url.port
    
    def _get_path(self):
        """Devuelve el path de la url de forma inteligente(?)"""
        if self.parsed_url is None:
            return '/'
        else:
            if self.parsed_url.path in (None,''):
                return '/'
            else:
                return self.parsed_url.path
    
    def retrieve(self,url=None,method="GET"):
        """Punto de acceso del cliente, crea la peticion, la envia al servidor, y guarda la respuesta"""
        if url:
            self.__url = url
            self.parsed_url = urlparse(url)
            
            if self.parsed_url.scheme is '':
                raise Exception("Formato de url incorrecto. Formato esperado: (http|ftp|https)://url[:port][/path_to_resource]")
            
            self.method = method # GET o HEAD (Solo soporta GET por el momento)
            
            self.__conect() # self.s socket created
            self.__build_request() # self.request string created
            self.__send_request() # Realiza la peticion y gestiona la descarga del recurso
        else:
            raise Exception("Expect parameter url")
    
    def __conect(self):
        """Crea el socket con el servidor"""
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
          self.s.connect((self._get_host() , self._get_port()))
        except socket.error, msg:
          sys.stderr.write("[ERROR] %s\n" % msg[1])
          sys.exit(2)
    
    def __build_request(self):
        """Construye el str de request para el servidor"""
        self.request =  "%(method)s %(path)s %(http_version)s\r\n"
        self.request += "Host: %(host)s\r\n"
        self.request += "User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:23.0) Gecko/20100101 Firefox/23.0\r\n"
        self.request += "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
        self.request += "Accept-Language: es-ar,es;q=0.8,en-us;q=0.5,en;q=0.3\r\n"
        #~ self.request += "Accept-Encoding: gzip, deflate\r\n" # No soporta encoding en esta version
        self.request += "Connection: keep-alive\r\n\r\n"
        self.request = self.request % { 'method':self.method, \
                                        'path':self._get_path(), \
                                        'http_version':self.http_version, \
                                        'host':self._get_host()}
    
    def __send_request(self):
        """Envia el request y recibe la respuesta"""
        self.s.sendall(self.request)
        response = self.s.recv(self.buffer)
        self.data = ""
        while len(response):
            self.data += response
            # Se controla que detecte solo la primera vez las cabeceras
            if not self.__header_detected:
                self.__header_detect()
            self.__sync_data()
            response = self.s.recv(self.buffer)
        self.__sync_data()
        
        self.__log_headers() # Logs a un header
        self.__save_file() # Guardar el archivo
        # Que use proxy
        # Que soporte Head
        
        
    def __sync_data(self):
        """ Este metodo se encarga de descargar la memoria si el archivo 
            que se descarga es demasiado grande"""
        
        if len(self.data) > 100000:
            f = open(self.download_file,'a')
            f.write(self.data)
            self.data = ""
            f.close()
    
    def __header_detect(self):
        """Metodo que detecta si en la descarga se encuentra el header.
            En caso afirmativo, lo carga en la instancia y lo elimina del
            stream de descarga."""
        headers = self.data.split(self.separador)
        
        # Si len es mayor a 1, el header ya esta completo
        if len(headers) > 1:
            self.data = self.separador.join(headers[1:]) # Arma la informacion de descarga sin el header
            
            self.str_headers = headers[0]
            self.headers = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", self.str_headers)) # Arma un dic con los headers
            # Primer linea del header HTTP/1.1
            self.headers["http"] = headers[0].split('\r\n')[0] 
            self.headers["http_version"] = self.headers["http"].split(' ')[0]
            self.headers["status"] = self.headers["http"].split(' ')[1]
            self.headers["status_message"] = ' '.join(self.headers["http"].split(' ')[2:])
            
            self.__header_detected = True
    
    def __log_headers(self):
        """Descarga las cabeceras de response a un archivo de log"""
        f = open(self.LOGFILE,'a')
        f.write("== HEADER: Response from %s\n" % self.__url)
        f.write("%s\n" % self.str_headers)
        f.close()
    
    def __save_file(self):
        """Guarda el archivo a disco, teniendo en cuenta si la descarga ya lo hizo o no"""
        file_in_disk = self.__saved_file()
        filename = self.__filename()
        if file_in_disk:
            os.rename(self.download_file, filename)
        else:
            f = open(filename,'w')
            f.write(self.data)
            f.close()
        
    
    def __content_encoding(self):
        """Soporte para encoding de contenido con gzip. No soportado"""
        if self.headers.has_key('Content-Encoding'):
            return self.headers['Content-Encoding']
        else:
            return None
    
    def __file_type(self):
        """Retorna la extension segun el tipo de archivo"""
        if self.headers.has_key('Content-Type'):
            return '.' + self.headers['Content-Type'].split('; ')[0].split('/')[1]
        else:
            return '' # Que habria que devolver por default? vacio?
    
    def __filename(self):
        """Retorna el mejor nombre de archivo en funcion de la informacion disponible"""
        extension = self.__file_type()
        #~ print "PATH: ", self.__get_path()
        if self._get_path() in ('/', ''):
            return self._get_host() + extension
        else:
            return self._get_path().split('/')[-1]
    
    def __saved_file(self):
        """Controla si durante la descarga el archivo fue bajado temporalmente a disco"""
        try:
            open(self.download_file)
        except:
            return False
        return True
        
if __name__=='__main__':
    # Test...
    #~ from http_client_object import HttpClient
    client = HttpClient()
    #~ client.retrieve('http://nesys.com.ar/images/nesys.jpg')
    #~ client.retrieve('http://nesys.com.ar/')
    #~ client.retrieve('http://nesys.com.ar')
    client.retrieve('http://www.tomasdelvechio.com.ar/')
    


