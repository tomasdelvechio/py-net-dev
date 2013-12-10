#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys
import json
from os.path import expanduser
import os
import subprocess
import random
import shlex
import rsa
import select

debug = True
   
class RSessionServer:
    
    def __init__(self,host='localhost',port=8022,buffsize=4096,backlog=5,usersFile='users'):
        self.sessions = {} # Sesiones de usuarios
        self.buffsize = buffsize
        self.pubkey, self.privkey = rsa.newkeys(512)
        self.char_limit = '\n'
        
        # Definicion del socket principal
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((host, port))
        self.s.listen(backlog)
        self.s_input = [self.s, sys.stdin] # Agrega el socket a la lista de sockets a ser controlados por el server
        
        # Carga los usuarios validos para loguearse
        # 	ToDo: No hay validacion de la estructura y contenido del archivo :/
        try:
            f = open(usersFile)
            self.validUsers = json.loads(f.read())
        except IOError:
            raise IOError('No se encuentra el archivo de usuarios. Consulte README.rsession.')
        
    def validUser(self,user=None,password=None):
        if self.validUsers.has_key(user):
            if self.validUsers[user]['pass'] == password:
                return True
            else:
                return False
        else:
            return False
    
    def getUserPassword(self,user=None):
        if self.validUsers.has_key(user):
            return self.validUsers[user]['pass']
        else:
            return False
        
    def createSession(self,user=None,password=None,hostname='localhost',port=None,pubkey=None,session=None):
        # Tengo que diferenciar entre el momento en que me pide conectarse y cuando me manda el login
        if session is None:
            # En este caso, recien me envia su clave publica. Datos necesarios: hostname, port, pubkey
            session = {}
            session['login'] = False
            session['pubkey'] = pubkey
            session['hostname'] = hostname
            session['port'] = port

            return session
        else:
            # Intento de login, con estructura de sesion ya creada. Datos: user, password
            if self.validUser(user,password):
                session['home'] = self._get_default_directory(user)
                session['directory'] = self._get_default_directory(user) # Cuando inicia sesion, se posiciona en su home
                session['login'] = True
                session['user'] = user

                return session
            else:
                return False
    
    def getPrompt(self,session=None):
        if self.sessions.has_key(session):
            return "%(user)s@%(hostname)s:%(directory)s$ " % {  'user' : self.sessions[session]['user'], \
                                                                'hostname' : socket.gethostname(), \
                                                                'directory' : self.sessions[session]['directory'] }
        else:
            return False
    
    def _get_default_directory(self,user=None):
        if self.validUser(user):
            return self.validUsers[user]['home']
        else:
            return '/'
    
    def _get_pubkey_package(self):
        return json.dumps({ 't' : 3, 'pubkey_n' : self.pubkey.n, 'pubkey_e' : self.pubkey.e}) + self.char_limit

    def _get_error_package(self,message):
        return json.dumps({ 't' : -1, 'error' : message })

    def encrypt_message(self, message, cli_pubkey):
        return rsa.encrypt(message,cli_pubkey)

    def decrypt_message(self,encrypted_message):
        return rsa.decrypt(encrypted_message,self.privkey)

    def split_response(self, response, lenght=53):
        chunks = len(response)
        chunk_size = lenght
        return [ response[i:i+chunk_size] for i in range(0, chunks, chunk_size) ]
    
    def send_response(self, response, s):

        encode_response = json.dumps(response) + self.char_limit
        sock_name = s.getsockname()

        # Si no esta en el hash de sesiones, entonces se envia en texto plano la rta
        if not self.sessions.has_key(sock_name):
            s.send(encode_response)
        # Si esta en el hash, se envia encriptada
        else:
            if len(encode_response) > 53:
                splited_response = self.split_response(encode_response)
            else:
                splited_response = [encode_response]
            
            for response in splited_response:
                encrypted_response = encrypt_message(response, self.sessions[sock_name]['pubkey'])
                s.send(encrypted_response)

        return True

    def _receive_data(self,s):
        # Evalua el tipo de mensaje y genera el response en consecuencia. Tipos de Mensaje:
        #       
        #       0: Request  (cli -> srv)
        #       1: Response (srv -> cli)
        #       2: Pubkey intercambio  (cli -> srv)
        #       3: Pubkey respuesta (srv -> cli)
        #       4: Encripted user and pass (cli -> srv)
        #       5: Login response (srv -> cli)
        #       6: CLose sesion (cli->srv)
        #      -1: Error (srv -> cli)
        # Debo fijarme si es un socket de una conexion ya logueada o no

        sock_name = s.getsockname()
        keep_session = True

        # Si esta en la lista de sesiones ya se conecto al menos una vez, sino, es la primera
        if self.sessions.has_key(sock_name):
            # Si esta, hay que distinguir entre solo tener la PubKey y que ya este logueado
            if self.sessions[sock_name]["login"]:
                # Recibo mensaje completo
                encode_request = ''
                while True:
                    encrypted_request = s.recv(self.buffsize)
                    decrypted_request = decrypt_message(encrypted_request)
                    encode_request += decrypted_request
                    # Si el ultimo caracter del request es el caracter de fin de mensaje, salimos del bucle
                    if encode_request[-1] == self.char_limit:
                        break
                request = json.loads(encode_request)
                if request['t'] == 0:
                    # Mensaje correcto, procesamos comando
                    if(request.has_key('cmd')):
                        # si es una operacion de cd, entonces cambio la carpeta de trabajo
                        cmd = shlex.split(request['cmd'])
                        if cmd[0] == 'cd':
                            if not os.path.isabs(cmd[1]):
                                path = os.path.abspath(os.path.join(self.sessions[sock_name]['directory'],cmd[1]))
                            else:
                                path = os.path.abspath(cmd[1])
                            os.chdir(path)
                            self.sessions[sock_name]['directory'] = path
                            response['out'] = ''
                        else:
                            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,)
                            response['out'] = proc.communicate()[0]
                        response['prompt'] = self.getPrompt(sock_name)
                    else:
                        response['out'] = ''
                        response['prompt'] = self.getPrompt(sock_name)
                    response['t'] = 1
                elif request['t'] == 6:
                    # Esta cerrando la sesion
                    self.sessions.pop(sock_name)
                    response = { 't' : 7 , 'mensaje' : 'OK' }
                    keep_session = False
                else:
                    #Error
                    response = self._get_error_package("Mensaje mal armado. Se esperaba un tipo de mensaje 0")
                self.send_response(response, s)
            else:
                # Si no esta logueado, esta enviando el mensaje de usuario y login encriptado
                encode_request = ''
                while True:
                    encrypted_request = s.recv(self.buffsize)
                    decrypted_request = decrypt_message(encrypted_request)
                    encode_request += decrypted_request
                    # Si el ultimo caracter de la respuesta es el caracter de fin de mensaje, salimos del bucle
                    if encode_request[-1] == self.char_limit:
                        break
                request = json.loads(encode_request)
                
                if request['t'] == 4:
                    if validUser(request['user'],request['pass']):
                        # Inicia sesion
                        self.sessions[sock_name]['home'] = self._get_default_directory(user)
                        session['directory'] = self._get_default_directory(user) # Cuando inicia sesion, se posiciona en su home
                        session['user'] = user
                        session['login'] = True
                        
                        response = { 't' : 5 , 'prompt' : self.getPrompt(sock_name) }
                    else:
                        #~ Paquete de tipo=-1
                        response = self._get_error_package("Error al loguearse. Usuario o contraseña incorrectos")
                else:
                    response = self._get_error_package("Mensaje mal armado. Se esperaba un tipo de mensaje 4")
                self.send_response(response,s)
        else:
            # Si es la primera vez, me esta enviado de forma plana la PubKey
            if debug:
                print "    1 - Primer conexion desde ", sock_name
            encode_request = ''
            while True:
                encode_request += s.recv(self.buffsize)
                # Si el ultimo caracter de la respuesta es el caracter de fin de mensaje, salimos del bucle
                if encode_request[-1] == self.char_limit:
                    break
            request = json.loads(encode_request)
            if debug:
                print "        request trae esto: ", request
            if request['t'] == 2:
                if debug:
                    print "    2 - Mensaje completo llego al server"
                self.sessions[sock_name] = { 'pubkey' : rsa.PublicKey(request['pubkey_n'],request['pubkey_e']), 'login' : False }
                print "LALALA"
                print self._get_pubkey_package()
                self.s.sendall(self._get_pubkey_package())
                print "LELELELE"
            else:
                response = self._get_error_package("Mensaje mal armado. Se esperaba un tipo de mensaje 2")

        return keep_session
        
    def load_server(self):
        close_server = False
        print "Servidor iniciado en: ", self.s.getsockname()
        while True:
            
            s_input,s_output,s_error = select.select(self.s_input,[],[])
            
            for s in s_input:
                # Si es el socket del servidor
                if s == self.s:
                    c_sock, c_addr = self.s.accept()
                    print "Conexion inciada desde: %s:%s" % c_sock.getpeername()
                    self.s_input.append(c_sock)
                elif s == sys.stdin:
                    #~ Si el usuario intenta cerrar el servidor
                    close_server = True
                    break
                else:
                    #~ Es un socket activo
                    sesion_activa = self._receive_data(s)
            
            if close_server:
                print "Cerrando sockets activos..."
                for s in s_input:
                    s.close()
                self.s.close()
                print "Saliendo."
                break
            
            # Salvo por un error, envio encriptado el response
            #if response['t'] in (-1,3):
                #client_sock.sendall(response)
            #else:
                #cypher_response = crypto.encrypt(json.dumps(response),)
                #client_sock.sendall(cypher_response)
            
            #print "Conexion cerrada por:", client_sock.getpeername()
            #client_sock.close()

#######################
###     MAIN        ###
#######################
if __name__ == "__main__":
    
    if(len(sys.argv) < 2):
        sys.exit("Forma de ejecucion: python %s <server_ip> <server_port>" % sys.argv[0])

    if(len(sys.argv) < 3):
        sys.exit("Falta <server_port>. Forma de ejecucion: python %s <server_ip> <server_port>" % sys.argv[0])
    
    host, port = sys.argv[1],int(sys.argv[2])
    
    rsession = RSessionServer(host=host,port=port)
    rsession.load_server()
    

