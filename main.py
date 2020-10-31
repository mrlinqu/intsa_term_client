# Copyright 2020 by Roman Khuramshin <mr.linqu@gmail.com>.
# All rights reserved.
# This file is part of the Intsa Term Client - X2Go terminal client for Windows,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.


from MainWindow import MainWindow
from X2goClient import X2goClient
import os
import queue
import time
import threading
import logging
import config
import functools
import paramiko
from tkinter import messagebox

# add filemode="w" to overwrite
#logging.basicConfig(filename="sample.log", level=logging.INFO)


class Main:
    wMain = None
    client = None
    waitClientTerminate_thread = None

    def __init__(self):
        config.init('./config.cfg')

        logfile = config.get('logfile', None)

        loglevel = config.get('loglevel', None)
        if loglevel == 'crit':
            loglevel = logging.CRITICAL
            pass
        elif loglevel == 'error':
            loglevel = logging.ERROR
            pass
        elif loglevel == 'warn':
            loglevel = logging.WARNING
            pass
        elif loglevel == 'info':
            loglevel = logging.INFO
            pass
        elif loglevel == 'debug':
            loglevel = logging.DEBUG
            pass
        else:
            loglevel = None


        logging.basicConfig(filename=logfile, level=loglevel, format='%(asctime)-15s %(message)s')

        logging.debug('main thread id: %s', threading.get_ident())

        self.wMain = MainWindow()
        self.wMain.onOk = self.onWndOk
        self.wMain.onCancel = self.onWndCancel
        self.wMain.start()
        pass

    def wait(self):
        pass

    #def wndLock(self):
    #    if self.wMain:
    #        self.wMain.lock()
    #    pass

    def wndUnlock(self):
        if self.wMain:
            self.wMain.unlock()
        pass

    def wndSetStatus(self, text):
        if self.wMain:
            self.wMain.setStatus(text)
        pass

    def onWndOk(self, username, passwd, printer, shares, keyauth,key=None):
        self.wMain.lock()

        clientParams = {'user':username, 'printer':printer, 'shares':shares}

        if (keyauth and not key):
            keyfilename = '%s.key' % username
            if not os.path.isfile(keyfilename):
                self.wMain.onNewpassOk = functools.partial(self.onNewpassOk, username=username, passwd=passwd, printer=printer, shares=shares)
                self.wMain.showNewpassModal()
                return
            #f = open('.pem','r')
            #s = f.read()
            #keydata = StringIO.StringIO(s)
            #key = paramiko.RSAKey.from_private_key(keydata)
            try:
                key = paramiko.RSAKey.from_private_key_file(keyfilename, passwd)
            except paramiko.ssh_exception.PasswordRequiredException as e:
                logging.debug('password required for key')
                messagebox.showerror(message='Требуется ввести пароль упрощенной авторизации!')
                return
            except paramiko.ssh_exception.SSHException as e:
                logging.debug('incorrect password for key')
                messagebox.showerror(message='Неверный пароль упрощенной авторизации!')
                return
            except Exception:
                logging.debug('auth key readinind error')
                messagebox.showerror(message='Ошибка упрощенной авторизации!')
                return

            clientParams['authkey'] = key
        else:
            if (keyauth):
                clientParams['authkey'] = key
            clientParams['password'] = passwd
        
        self.wMain.showStatusModal()

        self.paramsForSave = {'username':username, 'printer':printer, 'shares':shares, 'keyauth':keyauth} #'password':passwd,

        self.client = X2goClient(**clientParams)
        self.client.onChangeStatus = self.onClientChangeStatus
        self.client.onError = self.onClientError
        self.client.onStarted = self.onClientStarted
        self.client.start()
        pass


    def onNewpassOk(self, username, printer, shares, passwd, keypasswd):
        keyfilename = '%s.key' % username
        RSAKEY_STRENGTH = 4096
        key = paramiko.RSAKey.generate(RSAKEY_STRENGTH)
        key.write_private_key_file(keyfilename, keypasswd)
        self.onWndOk(username=username, passwd=passwd, printer=printer, shares=shares, keyauth=1, key=key)
        pass


    def waitClientTerminate(self):
        a = True
        while a:
            self.client.join()
            a = self.client.is_alive()
            logging.debug('client thread is_alive: %s', a)
            time.sleep(3) if a else None

        self.client = None
        self.waitClientTerminate_thread = None
        self.wndUnlock()
        pass


    def onWndCancel(self):
        if(self.client and not self.waitClientTerminate_thread):
            self.wndSetStatus('Отмена соединения...')
            self.client.stop()
            self.waitClientTerminate_thread = threading.Thread(target=self.waitClientTerminate)
            self.waitClientTerminate_thread.start()
        else:
            self.wMain.close()
        pass


    def onClientChangeStatus(self, text):
        self.wndSetStatus(text)
        pass


    def onClientError(self, error):
        self.wndSetStatus(error)
        self.client = None
        self.wndUnlock()
        pass


    def onClientStarted(self):
        self.wMain.close()
        self.wMain = None
        config.sets(self.paramsForSave)
        pass


if __name__ == '__main__':
    Main().wait()

