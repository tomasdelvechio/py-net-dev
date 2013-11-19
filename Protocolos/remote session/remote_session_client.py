#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys
import json
from getpass import getpass
import rsa

debug = True

class RSessionError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class RSessionClient:

    def __init__(self, user, password, host, port):
        
        # Setea las variables ingresadas por parametro
        self.user = user
        self.password = password
        self.host = host
        self.port = port

        # Define ctes y otras variables generales
        self.buff_size = 4096
        self.srv_pubkey = None
        self.char_limit = '\n'
        self.login = False
        self.prompt = None
        
        # Genera las claves publicas y privadas del cliente
        self.pubkey, self.privkey = self._generate_rsa_keys()

        # Genera el socket de la conexion
        self.s = self.open_conn()

    def _generate_rsa_keys(self):
        return rsa.newkeys(512)

    def open_conn(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        
        return s

    def close_conn(self):

        self.s.close()

        return True

    def split_request(self, request, lenght=53):

        chunks = len(request)
        chunk_size = lenght

        return [ request[i:i+chunk_size] for i in range(0, chunks, chunk_size) ]


    def encrypt_message(self, message):

        return rsa.encrypt(message,self.srv_pubkey)

    def decrypt_message(self,encrypted_message):

        return rsa.decrypt(encrypted_message,self.privkey)

    def send_request(self,request):

        encode_request = json.dumps(request) + self.char_limit

        if self.srv_pubkey is None:
            if debug:
                print "No tengo clave publica, envio mensaje plano", encode_request
            self.s.sendall(encode_request)
            encode_response = self.s.recv(self.buff_size)
            while True:
                data = self.s.recv(self.buff_size)
                encode_response += data
                if not data: break
            #encode_response = ''
            #while True:
            #    encode_response += self.s.recv(self.buff_size)
            #    if debug:
            #        print 'encode_response: ', encode_response
                # Si el ultimo caracter de la respuesta es el caracter de fin de mensaje, salimos del bucle
            #    if len(encode_response) > 0:
            #        if encode_response[-1] == self.char_limit:
            #            break
            print encode_response
            response = json.loads(encode_response)
            if debug:
                print "Llego mensaje...."
        else:
            if len(encode_request) > 53:
                splited_request = split_request(encode_request)
            else:
                splited_request = [encode_request]
            
            for request in splited_request:
                encrypted_request = encrypt_message(request)
                self.s.send(encrypted_request)

            encode_response = ''
            while True:
                encrypted_response = self.s.recv(self.buff_size)
                decrypted_response = self.decrypt_message(encrypted_response)
                encode_response += decrypted_response
                # Si el ultimo caracter de la respuesta es el caracter de fin de mensaje, salimos del bucle
                if decrypted_response[-1] == self.char_limit:
                    break

            response = json.loads(encode_response)

        return response

    # Intercambio de Claves publicas
    def changes_publickey(self):

        # Armar un request de tipo login, con el nombre de usuario y enviarlo al server
        request = { 't' : 2, 'pubkey_n' : self.pubkey.n, 'pubkey_e' : self.pubkey.e }
        response = self.send_request(request)
        if debug:
            print "    3 - Llego la respuesta", response
        if response['t'] == -1:
            raise RSessionError("Error devuelto por el servidor: %s" % response['error'])

        if response['t'] == 3:
            # reconstruye la pk del servidor
            self.srv_pubkey = rsa.PublicKey(response['pubkey_n'],response['pubkey_e'])

    # Proceso de login
    def get_login(self):

        # Armar un mensaje con user y pass, encriptarlo con la pubkey del server y enviarlo
        login_request = { 't' : 4, 'user' : user, 'pass' : password }
        response = self.send_request(host,port,request)

        if response['t'] == '-1':
            raise RSessionError("Error devuelto por el servidor: %s" % response['error'])

        if response['t'] == '5':
            # reconstruye la pk del servidor
            self.login = True
            if response.has_key("prompt"):
                self.prompt = response["prompt"]
            else:
                self.prompt = '%s@%s:$ ' % (self.user, self.host)

    def run(self):

        # Intercambio de claves
        self.changes_publickey()
        if debug:
            print "     Intercambio clave publica correctamente"
        # Login
        if not self.login:
            self.get_login()
        print "Nueva sesion en %s:%d\n" % (self.host,self.port)

        # Si login ok, muestro prompt y espero comandos
        while True:

            cmd = raw_input(self.prompt)
            
            # Salimos con el comando exit
            if cmd == "exit":
                request = { 't' : 6 }
            else:
                request = { 't' : 0, 'cmd' : cmd }
            
            response = self.send_request(request)

            if response['t'] == '-1':
                raise RSessionError("Error devuelto por el servidor: %s" % response['error'])

            if response['t'] == '7':
                # Cerro sesion correctamente
                break

            if response['t'] == '1':
                # reconstruye la pk del servidor
                self.login = True
                if response.has_key("prompt"):
                    self.prompt = response["prompt"]

                print response['out']

        self.close_conn()

        print "Sesion cerrada desde %s:%d\n" % (self.host,self.port)

#######################
###     MAIN        ###
#######################
if __name__ == "__main__":

    # Gestion de parametros y datos de usuario #
    ############################################

    if(len(sys.argv) < 2):
        sys.exit("Falta la cadena de conexion. Forma de ejecucion: python %s <user>@<ip_or_name>:[<port>]" % sys.argv[0])

    user,conn_name = sys.argv[1].split('@')
    host, port = conn_name.split(':')

    if '' in (user,host):
        sys.exit("Faltan datos en la cadena de conexion. Forma de ejecucion: python %s <user>@<ip_or_name>:[<port>]" % sys.argv[0])

    if port == '':
        port = 8022
    else:
        port = int(port)

    # Solicita el password para el login
    password = getpass('Password: ')

    # Instancia el objeto #
    #######################

    client = RSessionClient(user,password,host,port)
    client.run()
    #try:
    #    client.run()
    #except RSessionError as rse:
    #    print "Error de aplicacion: ", rse
    #except Exception as e:
    #    print "Error general: ", e

    # OLD CODE
    #response = s.recv(buff_size)
    #while 1:
        #data = s.recv(buff_size)
        #response += data
        #if not data: break
    #~ cmd = raw_input('user@serverhost:$ ')
