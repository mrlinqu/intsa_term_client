# Copyright 2020 by Roman Khuramshin <mr.linqu@gmail.com>.
# All rights reserved.
# This file is part of the Intsa Term Client - X2Go terminal client for Windows,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.


import logging, paramiko

class SSHServer(paramiko.ServerInterface):
    username = None
    auth_key = None

    ####################################################################################################

    def __init__(self, username, auth_key, *args, **kwargs):
        self.username = username
        self.auth_key = auth_key

        paramiko.ServerInterface.__init__(self, *args, **kwargs)
        logging.debug('initializing internal SSH server for handling incoming sFTP requests, allowing connections for user ,,%s\'\' only' % self.username)

    ####################################################################################################

    def check_channel_request(self, kind, chanid):
        logging.debug('detected a channel request for sFTP')
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    ####################################################################################################

    def check_auth_publickey(self, username, key):
        logging.debug('sFTP server %s: username is %s' % (self, self.username))
        #print('%s %s' % (username, type(key)))
        #print('%s' % (key, ))
        #print('%s' % (self.auth_key, ))
        if username == self.username:
            # some sheet... this is maybe not correct 
            if type(key) == paramiko.RSAKey and key == self.auth_key:
                logging.info('sFTP server %s: publickey auth (type: %s) has been successful' % (self, key.get_name()))
                return paramiko.AUTH_SUCCESSFUL
        logging.warn('sFTP server %s: publickey (type: %s) auth failed' % (self, key.get_name()))
        return paramiko.AUTH_FAILED

    ####################################################################################################

    def check_auth_password(self, username, password):
        logging.info('trying authentication login: "%s" password: "%s"' % (username, password))

        if username == 'root' and password == 'TestPass123':
            return paramiko.AUTH_SUCCESSFUL
        
        return paramiko.AUTH_FAILED

    ####################################################################################################

    def get_allowed_auths(self, username):
        logging.debug('sFTP client asked for support auth methods')
        return 'password,publickey'
        #return 'publickey'