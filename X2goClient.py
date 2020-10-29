# Copyright 2020 by Roman Khuramshin <mr.linqu@gmail.com>.
# All rights reserved.
# This file is part of the Intsa Term Client - X2Go terminal client for Windows,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.

import paramiko
from TunServer import TunServer
from NxproxyProc import NxproxyProc
from Xserv import Xserv
import threading
import sys
import traceback
#import time
import logging
import os, io
from getTcpPort import getTcpPort
from sftp.SFTPServer import SFTPServer
#from rforward import rforward
from RForvard import RForvard
import printing

class X2goClientException(Exception):
    '''raise this for my app'''
    pass

class X2goClient(threading.Thread):
    host = '1isa.ru' #'xffa.net'
    port = 2211 #2218
    user = ''
    password = ''
    printer = None
    shares = None

    ssh = None
    findedSessionInfo = None
    sessionParams = {}
    tunSrv = None
    nxProc = None
    xsrvProc = None
    printSpooler = None
    rtun = None
    hostname = ''

    onError = None
    onChangeStatus = None
    onStarted = None

    def __init__(self, user, password, printer, shares, ):
        super(X2goClient, self).__init__()

        self.user = user
        self.password = password
        self.printer = printer
        self.shares = shares

        self.evt_stop = threading.Event()


    def run(self):
        try:
            logging.debug('x2go client thread id: %s',threading.get_ident())
            if (not self.evt_stop.is_set()):
                self.execStatusCallback('Аутентификация...')
                self.startSsh(host=self.host, port=self.port, user=self.user, password=self.password)
            
            if (not self.evt_stop.is_set()):
                self.execStatusCallback('Поиск запущенных сессий...')
                self.findSession()
            
            if (not self.evt_stop.is_set() and not self.findedSessionInfo):
                self.execStatusCallback('Запуск сессии...')
                #self.startSession()
                self.startAgent()

            if (not self.evt_stop.is_set() and self.findedSessionInfo):
                self.execStatusCallback('Восстановление сессии...')
                self.resumeSession()

            self.sessiondir = '%s/.x2go/C-%s' % (self.homedir, self.sessionParams['session_id'])

            if (not self.evt_stop.is_set()):
                self.execStatusCallback('Инициализация защищенного соединения...')
                self.startTun()
            
            if not self.evt_stop.is_set() and (self.printer or self.shares):
                self.execStatusCallback('Запуск sftp...')
                self.startSftpServer()

            if (not self.evt_stop.is_set()):
                self.execStatusCallback('Инициализация дисплея...')
                self.startXserver()
            
            if (not self.evt_stop.is_set()):
                self.execStatusCallback('Запуск прокси...')
                self.startNxProxy()
            
            if (not self.evt_stop.is_set() and not self.findedSessionInfo):
                self.execStatusCallback('Загрузка рабочего стола...')
                self.startDesktop()

            if not self.evt_stop.is_set() and self.printer:
                self.execStatusCallback('Инициализация печати...')
                self.startPrinting()
            
            if not self.evt_stop.is_set() and self.shares:
                self.execStatusCallback('Инициализация дисков...')
                self.startShares()
            
            if (not self.evt_stop.is_set()):
                self.execStatusCallback('Ожидание инициализции клиентского окна...')
                self.findWindow()

            if self.onStarted:
                self.onStarted()

        except X2goClientException as e:
            self.execErrorCallback(e)
            self.evt_stop.set()
        except Exception as e:
            logging.error(e)
            exc_type, exc_obj, tb = sys.exc_info()
            logging.error(traceback.format_tb(tb))

            #f = tb.tb_frame
            #lineno = tb.tb_lineno
            #filename = f.f_code.co_filename
            #linecache.checkcache(filename)
            #line = linecache.getline(filename, lineno, f.f_globals)
            #print 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)

            self.execErrorCallback('Неизвестная ошибка запуска клиента!')
            self.evt_stop.set()

        logging.debug('started')
        self.evt_stop.wait()

        self.stopNxProxy()
        self.stopXserver()
        self.stopSftpServer()
        self.stopPrinting()
        self.stopTun()
        self.stopSsh()
        logging.debug('ended')


    def stop(self):
        logging.debug('client stop signal')
        if (self.evt_stop):
            self.evt_stop.set()
        pass

    def execStatusCallback(self, text):
        logging.debug('client STATUS: %s',text)
        if self.onChangeStatus:
            self.onChangeStatus(text)
        pass

    def execErrorCallback(self, error):
        logging.error('client error: %s',error)
        if self.onError:
            self.onError(error)
        pass


    def startSsh(self, host, port, user, password):
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(hostname=host, username=user, password=password, port=port)

            stdin, stdout, stderr = self.ssh.exec_command('hostname')
            self.hostname = stdout.read().decode().strip()
            logging.debug('hostname:  %s', self.hostname)

            stdin, stdout, stderr = self.ssh.exec_command('echo $HOME')
            self.homedir = stdout.read().decode().strip()
            logging.debug('homedir:  %s', self.homedir)
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            raise X2goClientException('Ошибка соединения с сервером!')
        except paramiko.ssh_exception.AuthenticationException as e:
            raise X2goClientException('Неправильный логин или пароль!')
        #except Exception:
        #    raise X2goClientException('Неизвестная ошибка соединения!')

    def stopSsh(self):
        if self.ssh:
            logging.debug('ssh stoping')
            self.ssh.close()
            #self.ssh = None
        else:
            logging.debug('ssh stoping none')
        pass


    def sshWriteFile(self, filename, data):
        logging.debug('ssh write file %s' % (filename, ))
        dirname = os.path.dirname(filename)
        stdin, stdout, stderr = self.ssh.exec_command('mkdir -p %s && cat > %s' % (dirname, filename))
        stdin.channel.send(data)
        stdin.channel.shutdown_write()
        
        pass


    def findSession(self):
        cmd = 'x2golistsessions' #{ x2golistsessions; x2golistshadowsessions; }
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        data = stdout.read().decode()
        err = stderr.read().decode()
        logging.debug('findSession data: %s',data)
        logging.debug('findSession err: %s',err)
        
        if err:
            raise X2goClientException('Ошибка при получении списка запущенных сессий!')

        sessions = []
        lines = data.split('\n')
        for line in lines:
            if line != '':
                info = line.split('|')
                sessions.append(info)
            pass

        if (sessions and sessions[0]):
            logging.debug('sessions: %s',sessions)
            self.findedSessionInfo = sessions[0]
        #    self.resumeSession(sessions[0])
        #else:
        #    self.startAgent()

        pass


    def startAgent(self):
        cmd = 'X2GO_XINERAMA=false x2gostartagent 800x600 adsl 16m-jpeg-9 unix-kde-depth_32 null auto 1 D LXDE both'

        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        data = stdout.read().decode()
        err = stderr.read().decode()
        logging.debug('startAgent data: %s',data)
        logging.debug('startAgent err: %s',err)
        if err:
            raise X2goClientException('Ошибка при запуске сессии!')

        splitedData = data.split('\n')

        self.sessionParams = {
            'display': int(splitedData[0]),
            'cookie': splitedData[1],
            'agent_pid': int(splitedData[2]),
            'session_id': splitedData[3],
            'graphics_port': int(splitedData[4]),
            'sound_port': int(splitedData[5]),
            'sshfs_port': int(splitedData[6]),
        }

        pass

    def resumeSession(self):
        cmd = 'X2GO_XINERAMA=false x2goresume-session '+self.findedSessionInfo[1]+' 800x600 adsl 16m-jpeg-9 unix-kde-depth_32 null auto 1 both'

        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        data = stdout.read().decode()
        err = stderr.read().decode()
        logging.debug('resumeSession data: %s',data)
        logging.debug('resumeSession err: %s',err)

        #if err:
        #    raise X2goClientException('Ошибка при возобновлении сессии!')

        lines = data.split('\n')
        logging.debug('lines: %s',lines)
        ports = []
        for line in lines:
            if line != '':
                ports.append(line.split('=')[1])

        self.sessionParams = {
            'display': 0,
            'cookie': self.findedSessionInfo[6],
            'agent_pid': int(self.findedSessionInfo[0]),
            'session_id': self.findedSessionInfo[1],
            'graphics_port': int(ports[0]),
            'sound_port': int(ports[1]),
            'sshfs_port': int(ports[2]),
        }

        pass


    def startTun(self):
        self.tunSrv = TunServer(self.sessionParams['graphics_port'], '127.0.0.1', self.sessionParams['graphics_port'], self.ssh.get_transport())
        self.tunSrv.onConnect = self.onTunConnected
        self.tunSrv.onDisconnect = self.onTunDisconnected
        pass

    def stopTun(self):
        if self.tunSrv:
            logging.debug('tun stoping')
            self.tunSrv.stop()
            self.tunSrv = None
        else:
            logging.debug('tun stoping none')
        pass

    def onTunConnected(self, peer):
        logging.debug("Tunnel open %r" % (peer,))
        pass

    def onTunDisconnected(self, peer):
        logging.debug("Tunnel closed from %r" % (peer,))
        self.stop()
        pass


    def startNxProxy(self):
        self.nxProc = NxproxyProc()
        #self.nxProc.start(cookie=self.sessionParams['cookie'], port=self.sessionParams['graphics_port'], display=self.sessionParams['display'])
        self.nxProc.start(cookie=self.sessionParams['cookie'], port=self.sessionParams['graphics_port'], display=74)
        self.nxProc.onTerminate = self.onNxTerminate
        pass

    def stopNxProxy(self):
        if self.nxProc:
            logging.debug('nxproxy stoping')
            self.nxProc.stop()
            self.nxProc.join()
            logging.debug('nxProc finished')
            self.nxProc = None
        else:
            logging.debug('nxproxy stoping none')
        pass

    def onNxTerminate(self):
        self.stop()
        pass



    def startXserver(self):
        self.xsrvProc = Xserv()
        self.xsrvProc.start()
        pass

    def stopXserver(self):
        if (self.xsrvProc):
            logging.debug('xserver stoping')
            self.xsrvProc.stop()
            self.xsrvProc = None
        else:
            logging.debug('xserver stoping none')
        pass

    def startDesktop(self):
        cmd = 'setsid x2goruncommand %s %s %s %s "startlxde" none D 1>/dev/null 2>/dev/null & exit' % (self.sessionParams['display'], self.sessionParams['agent_pid'], self.sessionParams['session_id'], self.sessionParams['sound_port'], )
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        pass

    def findWindow(self):
        finded = False
        finded = self.xsrvProc.find_session_window(self.sessionParams['session_id'], self.hostname)

        if not finded:
            raise X2goClientException('Неизвестная ошибка соединения!')

        pass


    def startSftpServer(self):
        logging.debug('sftp starting...')
        port = getTcpPort()
        logging.debug('sftp server port: %s' % port)
        self.stpServer = SFTPServer(port=port)
        logging.debug('sftp server started')
        logging.debug('sftp reverce tun startind...')
        #bindedPort = self.ssh.get_transport().request_port_forward(address=('127.0.0.1:%s' % port), port=self.sessionParams['sshfs_port'])
        #self.ssh.get_transport().open_forwarded_tcpip_channel(src_addr, dest_addr)
        #print('request_port_forward: %s -> %s' % (bindedPort, port))
        #rforward(server_port=port, remote_host='127.0.0.1', remote_port=self.sessionParams['sshfs_port'], transport=self.ssh.get_transport())
        
        #rforward(server=('127.0.0.1:%s' % port), port=self.sessionParams['sshfs_port'], transport=self.ssh.get_transport())
        self.rtun = RForvard(transport=self.ssh.get_transport(), remote_addr='127.0.0.1', remote_port=port, server_addr='127.0.0.1', server_port=self.sessionParams['sshfs_port'])
        self.rtun.start()
        logging.debug('sftp reverce tun started')

        #self.sftpKeySend()

        logging.debug('sftp user: %s' % self.stpServer.Username)

        pass


    def stopSftpServer(self):
        if self.rtun:
            self.rtun.stop()
            self.stpServer.stop()
            #_key_fname = '%s/%s/%s/%s' % (self.homedir, self.sessionParams['session_id'], 'ssh', 'key')
            #self.ssh.exec_command('rm %s' % (_key_fname,))
        pass


    def sftpKeySend(self):
        #_tmp_io_object = io.BytesIO()
        _tmp_io_object = io.StringIO()
        self.stpServer.RSAKeyAuth.write_private_key(_tmp_io_object)
        _tmp_io_object.write('----BEGIN RSA IDENTITY----')
        #_tmp_io_object.write(b'%b %b' % (self.stpServer.RSAKeyHost.get_name().encode(), self.stpServer.RSAKeyHost.get_base64().encode(),))
        _tmp_io_object.write('%s %s' % (self.stpServer.RSAKeyHost.get_name(), self.stpServer.RSAKeyHost.get_base64(),))

        _key_fname = '%s/%s/%s' % (self.sessiondir, 'ssh', 'key')
        self.sshWriteFile(_key_fname, _tmp_io_object.getvalue())

        pass


    def shareFolder(self, path, type='disk'):
        logging.info('sharing local folder: %s' % path)

        self.sftpKeySend()

        path = os.path.normpath(path)

        if not os.path.exists(path):
            logging.warn('local folder does not exist: %s' % path)
            return False

        path = path.replace('\\', '/')
        path = path.replace(':', '')
        path = '/windrive/%s' % path

        _key_fname = '%s/%s/%s' % (self.sessiondir, 'ssh', 'key')

        mounttype = ''
        if type == 'spool':
            mounttype = '__PRINT_SPOOL_'
        elif type == 'mimebox':
            mounttype = '__MIMEBOX_SPOOL_'
            pass
        
        export_iconv_settings = 'echo'#export X2GO_ICONV=modules=iconv,from_code=WINDOWS-1252,to_code=UTF-8'

        cmd = '%s && x2gomountdirs dir %s \'%s\' %s %s%s__REVERSESSH_PORT__%s;' % (export_iconv_settings, self.sessionParams['session_id'], self.stpServer.Username, _key_fname, path, mounttype, self.sessionParams['sshfs_port'])
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        logging.debug(stdout.read().decode())
        logging.debug(stderr.read().decode())

        pass


    def startPrinting(self):
        # share spool
        # run spoll handler
        
        #RSAKEY_STRENGTH = 1024
        #RSAHostKey = paramiko.RSAKey.generate(RSAKEY_STRENGTH)
        #self.sftp = paramiko.sftp_server.SFTPServer
        spool_dir = os.path.join(os.getcwd(),'spool')

        try:
            os.makedirs(spool_dir)
        except OSError as e:
            if e.errno == 17:
                # file exists
                pass

        self.shareFolder(path=spool_dir, type='spool')

        self.printSpooler = printing.Spooler(spool_dir=spool_dir, printer=self.printer)
        self.printSpooler.start()

        pass

    def stopPrinting(self):
        if self.printSpooler:
            self.printSpooler.stop()
        pass

    def startShares(self):
        for path in self.shares:
            self.shareFolder(path)
        pass

    #def start(self):
    #    pass

