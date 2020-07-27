# Copyright 2020 by Roman Khuramshin <mr.linqu@gmail.com>.
# All rights reserved.
# This file is part of the Intsa Term Client - X2Go terminal client for Windows,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.


import threading
import socketserver
import logging
import paramiko
import time

from sftp.SSHServer import SSHServer
from sftp.SFTPInterface import SFTPInterface


####################################################################################################


class SFTPServerHandler(socketserver.BaseRequestHandler):
    RSAKeyHost = None
    Username = None
    RSAKeyAuth = None
    
    def handle(self):
        logging.debug('handle SFTP server connection')
        transport = paramiko.Transport(self.request)
        transport.add_server_key(self.RSAKeyHost)
        transport.set_subsystem_handler('sftp', paramiko.SFTPServer, SFTPInterface)

        server = SSHServer(username = self.Username, auth_key = self.RSAKeyAuth)

        transport.start_server(server = server)

        #while transport.is_active() and pysshrp.common.running:
        while transport.is_active():
            time.sleep(1)

        transport.stop_thread()

        pass
    
    pass


####################################################################################################


class SFTPServer:
    RSAKEY_STRENGTH = 1024
    RSAKeyHost = paramiko.RSAKey.generate(RSAKEY_STRENGTH)
    Username = time.strftime('u%Y%m%d%H%M%S')
    RSAKeyAuth = paramiko.RSAKey.generate(RSAKEY_STRENGTH)
    root_path = None

    def __init__(self, port=22):
        class SubHander(SFTPServerHandler):
            RSAKeyHost = self.RSAKeyHost
            Username = self.Username
            RSAKeyAuth = self.RSAKeyAuth

        self.server = socketserver.ThreadingTCPServer(("", port), SubHander)
        self.server.allow_reuse_address = True
        self.server.daemon_threads = True

        self.server_thread = threading.Thread(target = self.server.serve_forever)
        self.server_thread.start()

        pass
    
    def stop(self):
        self.server.shutdown()
        self.server_thread.join(5)
        self.server.server_close()

        pass

    pass

