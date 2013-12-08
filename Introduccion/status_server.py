#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Basic Status HTTP Server

Simple implementation of Python's BaseHTTPServer
that creates a web server which prints out 
basic system information in plain text, HTML or JSON.

:Author
    Andrés Gattinoni <andresgattinoni@gmail.com>

:Website
    http://www.tail-f.com.ar

:Version
    0.1
"""
import os
import sys
import time
import json
import BaseHTTPServer
from optparse import OptionParser
from urlparse import urlparse

__author__ = "Andrés Gattinoni <andresgattinoni@gmail.com>"
__version__ = "StatusServer/0.1"

class RequestHandler (BaseHTTPServer.BaseHTTPRequestHandler):
    """Request handler

    Handles HTTP GET requests and returns
    basic system information in different formats"""

    server_version = __version__
    
    def do_GET (self):
        """Handles GET requests"""
        args = urlparse(self.path)
        self.send_response(200)
        body = self._get_status(args.path[1:])
        self.end_headers()
        self.wfile.write(body)
        return

    def _get_data (self):
        """Gathers basic system information"""
        return {'platform': sys.platform,
                'os_name': ' '.join(os.uname()),
                'loadavg': "%01.2f, %01.2f, %01.2f" % \
                           os.getloadavg(),
                'date': time.strftime('%a %b %d %H:%M:%S %Z %Y', \
                                      time.localtime()),
                'pyver': 'Python %s' % sys.version}

    def _get_plain (self):
        """Returns the system info in plain text format"""
        self.send_header('Content-Type', \
                         'text/plain; charset=utf-8')
        data = self._get_data()
        return "System Status:\n" \
               "--------------\n" \
               "Platform: %s\n" \
               "OS: %s\n" \
               "System date: %s\n" \
               "Load average: %s\n"  \
               "Python version: %s\n" % \
               (data['platform'], \
                data['os_name'], \
                data['date'], \
                data['loadavg'], \
                data['pyver'])

    def _get_json (self):
        """Returns the system info as a json string"""
        self.send_header('Content-Type', \
                         'application/json; charset=utf-8')
        return json.dumps(self._get_data())

    def _get_html (self):
        """Returns the system info as an HTML document"""
        self.send_header('Content-Type', \
                         'text/html; charset=utf-8')
        data = self._get_data()
        return "<html>" \
               "<head>" \
               "<title>System status</title>" \
               "</head>" \
               "<body>" \
               "<h1>System status</h1>" \
               "<ul>" \
               "    <li><strong>Platform:</strong> %s</li>" \
               "    <li><strong>OS Name:</strong> %s</li>" \
               "    <li><strong>System date:</strong> %s</li>" \
               "    <li><strong>Load average:</strong> %s</li>" \
               "    <li><strong>Python version:</strong> %s</li>" \
               "</ul>" \
               "</body>" \
               "</html>" % \
               (data['platform'], \
                data['os_name'], \
                data['date'], \
                data['loadavg'], \
                data['pyver'])

    def _get_status (self, format):
        """Returns the status string 
           in the appropriate format"""
        if format == 'plain':
            return self._get_plain()
        elif format == 'json':
            return self._get_json()
        else:
            return self._get_html()
            

def main ():
    """Main function of the script
       Runs the HTTP Server
       """
    parser = OptionParser(usage="%prog [options]", \
                          version=__version__,
                          description="Basic HTTP Server which provides " \
                                      "general information of the system status")
    parser.add_option('-a', '--address', dest='host', \
                      help='Host/IP address to bind to', \
                      metavar='ADDRESS', default='localhost')
    parser.add_option('-p', '--port', dest='port', \
                      help='Port to bind to', \
                      metavar='PORT', default=8000, \
                      type='int')
    (option, args) = parser.parse_args()

    if option.port < 0:
        parser.error("Port number must be a positive integer")
        return 1

    if option.port < 1024:
        print "Warning: ports lower than 1024 are reserved to root"

    try:
        httpd = BaseHTTPServer.HTTPServer((option.host, option.port), RequestHandler)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print "Shutting down."
    return 0

if __name__ == "__main__":
    sys.exit(main())