import os
import subprocess
import win32gui
import win32process
import time
import logging
from resource import resource_path

class Xserv:
	proc = None
	session_window = None

	def __init__(self, exe_file=None, log_file=None):
		self.exe_file = exe_file if exe_file else resource_path(os.path.join('vcxsrv','vcxsrv.exe'))
		#self.log_file = log_file if log_file else os.path.join(self.nx_root, 'session.log')
		self.log_file = log_file if log_file else 'nul'


	def start(self, display=74):
		cmd = '%s -multiwindow -notrayicon -clipboard -nopn -silent-dup-error -xinerama -once -background none :%s' % (self.exe_file, display)
		opts = {
			'env': os.environ.copy(),
			#env.update({"NX_ROOT": self.nx_root, "DISPLAY": "localhost:40"}),
			'stdin': open('nul', 'r'),
			'stdout':  open(self.log_file, 'a'),
			'stderr': open(self.log_file, 'a'),
		}

		#self.proc = subprocess.Popen(cmd, env=env, stdin=_stdin, stdout=_stdout, stderr=_stderr)
		logging.debug('Xserv cmd: %s', cmd)
		logging.debug('Xserv opts: %s', opts)
		self.proc = subprocess.Popen(cmd, **opts)
		logging.debug(self.proc)
		pass


	def stop(self):
		if self.proc:
			self.proc.terminate()
			#self.proc.wait(5)


	def find_session_window(self, session_name, hostname):
		windows = []
		window = None
		needle = "X2GO-%s@%s" % (session_name, hostname)
		#logging.debug('search window:', '"',session_name,'"','"', hostname,'"')
		logging.debug('search window: "%s"', needle)
		
		def _callback(hwnd, extra):
			try:
				#print('"',win32gui.GetWindowText(hwnd), '"')
				if win32gui.GetWindowText(hwnd) == needle:
					#print('__FOUND__:', hwnd)
					windows.append(hwnd)
			except:
				pass
		
		i = 20
		while i:
			i -= 1
			logging.debug('search window...')

			#win32gui.EnumWindows(_callback, None)
			#if len(windows):
			#	#print('__FOUND__:', windows[0])
			#	self.session_window = windows[0]
			#	return True

			handle = win32gui.FindWindow(None, needle) #//for example
			if (handle):
				logging.debug('window found: %s', handle)
				self.session_window = handle
				win32gui.SetForegroundWindow(handle)
				#threadId = win32process.GetWindowThreadProcessId(handle);
				#print('window threadId:',threadId)
			#	#win32gui.SetWindowText(handle, session_title)
				return True

			time.sleep(1)
			pass

		return False


	def set_session_window_title(self, title):
		if self.session_window:
			win32gui.SetWindowText(self.session_window, session_title)
		pass

	def raise_session_window(self):
		if self.session_window:
			win32gui.SetForegroundWindow(self.session_window)
		pass
