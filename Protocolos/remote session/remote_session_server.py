#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys
import json
from os.path import expanduser
from subprocess import call
import random

#~ def generarPrompt(login = None):
    
    #~ home = expanduser("~")
    
class RSessionServer:
    
    def __init__(self,host='localhost',port=8022,buffsize=4096,backlog=5,usersFile='users'):
        self.sessions = {} # Sesiones de usuarios
        self.buffsize = buffsize
        
        # Definicion del socket
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((host, port))
        self.s.listen(backlog)
        
        # Carga los usuarios validos para loguearse
        try:
            # Si quedo una descarga trunca, la limpiamos
            f = open(usersFile)
            self.validUsers = json.loads(f.read())
        except IOError:
            raise IOError('No se encuentra el archivo de usuarios. Consulte README.rsession.')
    
    def validUser(self,user=None):
        if self.validUsers.has_key(user):
            return True
        else:
            return False
    
    def createSession(self,user=None,client_name=('localhost',None)):
        
        if self.validUser(user):
            # Genero la credencial de acceso al server
            session = {}
            session['session'] = self._get_session_cred()
            session['name'] = client_name # Guardamos informacion de (host,port)
            session['home'] = self._get_default_directory(user)
            session['directory'] = self._get_default_directory(user) # Cuando inicia sesion, se posiciona en su home
            session['login'] = True
            session['user'] = user
            
            # Al hacer de clave de sesion al id, hacemos al server multisession
            #   El unico problema es que la session va a tener que viajar en cada request
            self.sessions[session['session']] = session
            
            return session['session']
            
        else:
            
            return False
    
    def getPrompt(self,session=None):
        
        if self.sessions.has_key(session):
            
            return "%(user)s@%(hostname)s:%(directory)s$ " % {  'user' : self.sessions[session]['user'], \
                                                                'hostname' : socket.gethostname(), \
                                                                'directory' : self.sessions[session]['directory'] }
        else:
            return False
    
    def _get_session_cred(self):
        return random.getrandbits(128) # Identificador de session
    
    def _get_default_directory(self,user=None):
        
        if self.validUser(user):
            return self.validUsers[user]['home']
        else:
            return '/'
            
    def load_server(self):
        
        print "Servidor iniciado en: ", self.s.getsockname()
        
        while True:
            
            client_sock, client_addr = self.s.accept()
            print "Conexion desde:", client_sock.getpeername()
            data = client_sock.recv(self.buffsize)
            
            request = json.loads(data)
            
            # Recibido el request, hay que controlar 2 cosas:
            #   Si viene con opt (opciones) y si viene un cmd (comando)
            #   Si viene un comando, hay que controlar que la sesion exista
            
            response = {}
            
            # Manejo de opciones
            if(request.has_key('opt')):
                
                if(request['opt'].has_key('login')):
                    
                    session_id = self.createSession(request['opt']['login'])
                    
                    if session_id:
                        response['opt'] = { 'session' : session_id, \
                                            'prompt' : self.getPrompt(session_id)}
            
            # Manejo de comandos
            if(request.has_key('cmd')):
                
                # Si es una operacion de login, ignoro cualquier cmd que me envie
                if( not request['opt'].has_key('login') ):
                    with open('outfile','w') as fout:
                        call(request['cmd'],stdout=fout,shell=True) # Ejecuta el comando
                    response['out'] = open('outfile').read()
            
            client_sock.sendall(json.dumps(response))
            
            #~ client_sock.sendall(data)
            #~ data = client_sock.recv(self.buffsize) # Sigo leyendo el buffer hasta que este vacío y salga del while
            
            print "Conexion cerrada por:", client_sock.getpeername()
            client_sock.close()

if __name__ == "__main__":
    
    if(len(sys.argv) < 2):
        sys.exit("Forma de ejecucion: python %s <server_ip> <server_port>" % sys.argv[0])

    if(len(sys.argv) < 3):
        sys.exit("Falta <server_port>. Forma de ejecucion: python %s <server_ip> <server_port>" % sys.argv[0])
    
    host, port = sys.argv[1],int(sys.argv[2])
    
    rsession = RSessionServer(host=host,port=port)
    rsession.load_server()
    

