# -*- coding: utf-8 -*-
#

import sys
import logging
from wsgiref.simple_server import make_server, WSGIRequestHandler, WSGIServer
import SocketServer
from OpenSSL import SSL
import socket

from ajenti.config import Config
from ajenti.app import AppDispatcher
import ajenti.app.plugins as plugins


class CustomRequestHandler(WSGIRequestHandler):
    log = None
    multithread = True

    def setup(self):
        if self.server.cert_file:
            self.connection = self.request
            self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
            self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)
        else:
            WSGIRequestHandler.setup(self)

    def log_request(self, code, size):
        # "GET /dl/core/ui/category-sel.png HTTP/1.1" 200 8994
        if self.log:
            self.log.info('"%s %s %s" %s %d'%(self.command,
                                              self.path,
                                              self.request_version,
                                              code, size))


class CustomServer(SocketServer.ThreadingMixIn, WSGIServer):
    cert_file = ''
    request_queue_size = 100

    def __init__(self, server_address, HandlerClass):
        WSGIServer.__init__(self, server_address, HandlerClass)
        if self.cert_file:
            ctx = SSL.Context(SSL.SSLv3_METHOD)
            ctx.use_privatekey_file(self.cert_file)
            ctx.use_certificate_file(self.cert_file)

            self.socket = SSL.Connection(ctx, socket.socket(self.address_family,
                                                            self.socket_type))
            self.server_bind()
            self.server_activate()


def server(log_level=logging.INFO, config_file=''):
    # Initialize logging subsystem
    log = logging.getLogger('ajenti')
    log.setLevel(log_level)
    stderr = logging.StreamHandler()
    stderr.setLevel(log_level)
    if log_level == logging.DEBUG:
        formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(module)s.%(funcName)s(): %(message)s')
    else:
        formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    stderr.setFormatter(formatter)
    log.addHandler(stderr)

    # Read config
    config = Config()
    if config_file:
        log.info('Using config file %s'%config_file)
        config.load(config_file)
    else:
        log.info('Using default settings')

    host = config.get('ajenti','bind_host')
    port = config.getint('ajenti','bind_port')
    log.info('Listening on %s:%d'%(host, port))
    # Add log handler to config, so all plugins could access it
    config.set('log_facility',log)

    # Load external plugins
    plugins.loader(config.get('ajenti', 'plugins'), log)

    CustomRequestHandler.log = log
    # Start server
    if config.getint('ajenti', 'ssl') == 1:
        CustomServer.cert_file = config.get('ajenti','cert_file')

    httpd = make_server(host, port, AppDispatcher(config).dispatcher,
                            CustomServer, CustomRequestHandler)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt, e:
        log.warn('Stopping by <Control-C>')
