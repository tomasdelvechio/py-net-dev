#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import socket
import os
import select

class HttpServer:
    
    def __init__(self, host='', port=8080, proxy=None, logfile='headers.log'):
        # Server vars
        self.proxy = proxy
        self.LOGFILE = logfile
        self.http_version = "HTTP/1.0"
        self.separador = '\r\n\r\n' # Separador de header y content de la respuesta HTTP
        self.h_separador = '\r\n'
        self._header_detected = False

        # socket vars
        self.buffer = 4096
        self.backlog = 5
        self.host = host
        self.port = port

    def receive_request(self, socket):
        data = socket.recv(self.buffer)
        while len(data) == self.buffer:
            data += socket.recv(self.buffer)
        return data

    def dispatcher_request(self, request):
        # En esta version, no me importa nada del request, devuelvo un header y una pagina con formato correcto

        headers = [ "%s 200 OK" % self.http_version,
                    "Content-Type: text/html",
                    self.h_separador ]

        page = "<html><body><h1>It Works!</h1></body></html>"
        response = self.h_separador.join(headers) + page
        return response

    def run(self):

        # Arma socket de servidor
        self.sock_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock_server.bind((self.host,self.port))
        self.sock_server.listen(self.backlog)
        self.sock_input = [self.sock_server, sys.stdin]

        print "Servidor iniciado en %s:%s" % (self.host is not '' if self.host else '0.0.0.0',self.port)

        while True:
            lst_input,lst_output,lst_error = select.select(self.sock_input,[],[])

            for s in lst_input:

                if s == self.sock_server:
                    client, address = self.sock_server.accept()
                    print "Se ha conectado %s:%s" % address
                    self.sock_input.append(client)

                elif s == sys.stdin:
                    print "Presionaron una tecla..."
                    keyWord = sys.stdin.readline()
                    break

                else:
                    # Procesa la request
                    print "Recibo datos de: %s:%s" % s.getpeername()
                    request = self.receive_request(s)
                    response = self.dispatcher_request(request)
                    s.sendall(response)
                    s.close()
                    self.sock_input.remove(s)
            
        self.sock_server.close() 
        
        
if __name__ == "__main__":
    server = HttpServer()
    server.run()