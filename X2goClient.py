import paramiko
from TunServer import TunServer
from NxproxyProc import NxproxyProc
from Xserv import Xserv
import threading
import sys
import traceback
#import time
import logging

class X2goClientException(Exception):
	'''raise this for my app'''
	pass

class X2goClient(threading.Thread):
	host = '1isa.ru' #'xffa.net'
	port = 2211 #2218
	user = ''
	password = ''

	ssh = None
	findedSessionInfo = None
	sessionParams = {}
	tunSrv = None
	nxProc = None
	xsrvProc = None
	hostname = ''

	onError = None
	onChangeStatus = None
	onStarted = None

	def __init__(self, user, password, config):
		super(X2goClient, self).__init__()

		self.user = user
		self.password = password

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
				pass

			if (not self.evt_stop.is_set() and self.findedSessionInfo):
				self.execStatusCallback('Восстановление сессии...')
				self.resumeSession()

			if (not self.evt_stop.is_set()):
				self.execStatusCallback('Инициализация защищенного соединения...')
				self.startTun()
			
			if (not self.evt_stop.is_set()):
				self.execStatusCallback('Инициализация дисплея...')
				self.startXserver()
			
			if (not self.evt_stop.is_set()):
				self.execStatusCallback('Запуск прокси...')
				self.startNxProxy()
			
			if (not self.evt_stop.is_set() and not self.findedSessionInfo):
				self.execStatusCallback('Загрузка рабочего стола...')
				self.startDesktop()
			
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
		except paramiko.ssh_exception.NoValidConnectionsError as e:
			raise X2goClientException('Ошибка соединения с сервером!')
		except paramiko.ssh_exception.AuthenticationException as e:
			raise X2goClientException('Неправильный логин или пароль!')
		except Exception:
			raise X2goClientException('Неизвестная ошибка соединения!')

	def stopSsh(self):
		if self.ssh:
			logging.debug('ssh stoping')
			self.ssh.close()
			#self.ssh = None
		else:
			logging.debug('ssh stoping none')
		pass


	def findSession(self):
		cmd = 'x2golistsessions' #{ x2golistsessions; x2golistshadowsessions; }
		stdin, stdout, stderr = self.ssh.exec_command(cmd)
		data = stdout.read().decode()
		err = stderr.read().decode()
		logging.debug('data: %s',data)
		logging.debug('err: %s',err)
		
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
		#	self.resumeSession(sessions[0])
		#else:
		#	self.startAgent()

		pass


	def startAgent(self):
		cmd = 'X2GO_XINERAMA=false x2gostartagent 800x600 adsl 16m-jpeg-9 unix-kde-depth_32 null auto 1 D LXDE both'

		stdin, stdout, stderr = self.ssh.exec_command(cmd)
		data = stdout.read().decode()
		err = stderr.read().decode()
		logging.debug('data: %s',data)
		logging.debug('err: %s',err)
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
		logging.debug('data: %s',data)
		logging.debug('err: %s',err)

		#if err:
		#	raise X2goClientException('Ошибка при возобновлении сессии!')

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

	#def start(self):
	#	pass

