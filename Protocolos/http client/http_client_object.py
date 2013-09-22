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
        
    def __get_host(self):
        if self.parsed_url is None:
            return 'localhost'
        else:
            if self.parsed_url.hostname is None:
                return 'localhost'
            else:
                return self.parsed_url.hostname
            
    
    def __get_port(self):
        if self.parsed_url is None:
            return 80
        else:
            if self.parsed_url.port is None:
                return 80
            else:
                return self.parsed_url.port
    
    def __get_path(self):
        if self.parsed_url is None:
            return '/'
        else:
            if self.parsed_url.path is None:
                return '/'
            else:
                return self.parsed_url.path
    
    def retrieve(self,url=None,method="GET"):
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
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
          self.s.connect((self.__get_host() , self.__get_port()))
        except socket.error, msg:
          sys.stderr.write("[ERROR] %s\n" % msg[1])
          sys.exit(2)
    
    def __build_request(self):
        self.request =  "%(method)s %(path)s %(http_version)s\r\n"
        self.request += "Host: %(host)s\r\n"
        self.request += "User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:23.0) Gecko/20100101 Firefox/23.0\r\n"
        self.request += "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
        self.request += "Accept-Language: es-ar,es;q=0.8,en-us;q=0.5,en;q=0.3\r\n"
        #~ self.request += "Accept-Encoding: gzip, deflate\r\n"
        self.request += "Connection: keep-alive\r\n\r\n"
        self.request = self.request % { 'method':self.method, \
                                        'path':self.__get_path(), \
                                        'http_version':self.http_version, \
                                        'host':self.__get_host()}
    
    def __send_request(self):
        self.s.sendall(self.request)
        response = self.s.recv(self.buffer)
        self.data = ""
        while len(response):
            self.data += response
            # Solo debe hacerlo una vez, controlar!!!!!! esto asi como esta falla si en el content aparece nuevos doble enters
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
        f = open(self.LOGFILE,'a')
        f.write("== HEADER: Response from %s\n" % self.__url)
        f.write("%s\n" % self.str_headers)
        f.close()
    
    def __save_file(self):
        
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
        
        if self.headers.has_key('Content-Type'):
            return '.' + self.headers['Content-Type'].split('; ')[0].split('/')[1]
        else:
            return '' # Que habria que devolver por default? vacio?
    
    def __filename(self):
        
        extension = self.__file_type()
        #~ print "PATH: ", self.__get_path()
        if self.__get_path() in ('/', ''):
            return self.__get_host() + extension
        else:
            return self.__get_path().split('/')[-1]
    
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
    client.retrieve('http://nesys.com.ar/images/nesys.jpg')
    client.retrieve('http://nesys.com.ar/')
    client.retrieve('http://nesys.com.ar')
    


