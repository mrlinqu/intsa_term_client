from MainWindow import MainWindow
from X2goClient import X2goClient
import os
import queue
import time
import threading
import logging

# add filemode="w" to overwrite
#logging.basicConfig(filename="sample.log", level=logging.INFO)


class Main:
	wMain = None
	client = None
	config = None
	waitClientTerminate_thread = None

	def __init__(self):
		self.config = self.readConf()

		logfile = self.config.get('logfile', None)

		loglevel = self.config.get('loglevel', None)
		loglv = None
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

		self.wMain = MainWindow(config=self.config)
		self.wMain.onOk = self.onWndOk
		self.wMain.onCancel = self.onWndCancel
		self.wMain.start()
		pass


	def readConf(self):
		options = {}
		fname = './config.cfg'
		if os.path.exists(fname):
			with open(fname, 'r') as f:
				for line in f:
					opt = line.split("=")
					options[opt[0].strip()] = opt[1].strip()

		return options


	def wait(self):
		pass

	def wndLock(self):
		if self.wMain:
			self.wMain.lock()
		pass

	def wndUnlock(self):
		if self.wMain:
			self.wMain.unlock()
		pass

	def wndSetStatus(self, text):
		if self.wMain:
			self.wMain.setStatus(text)
		pass

	def onWndOk(self, login, passwd):
		self.wndLock()
		self.client = X2goClient(user=login, password=passwd, config=self.config,)
		self.client.onChangeStatus = self.onClientChangeStatus
		self.client.onError = self.onClientError
		self.client.onStarted = self.onClientStarted
		self.client.start()
		pass


	def waitClientTerminate(self):
		a = True
		while a:
			self.client.join()
			a = self.client.is_alive()
			logging.debug('client thread is_alive: %s', a)
			time.sleep(3) if a else None

		self.afterClientTerminate()
		pass


	def afterClientTerminate(self):
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
		pass




if __name__ == '__main__':
	Main().wait()
