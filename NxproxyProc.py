# Copyright 2020 by Roman Khuramshin <mr.linqu@gmail.com>.
# All rights reserved.
# This file is part of the Intsa Term Client - X2Go terminal client for Windows,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.

import os
import subprocess
import threading
import logging
from resource import resource_path

__NAME__ = "nxproxy_proc-pylib"

class NxproxyProc(threading.Thread):
	cookie = None
	port = None
	display = None


	def __init__ (self, nx_root=None, options_file=None, log_file=None, error_log_file=None, exe_file=None):
		super(NxproxyProc, self).__init__()

		self.exe_file = exe_file if exe_file else resource_path(os.path.join('nxproxy','nxproxy.exe'))#os.path.normpath('./nxproxy/nxproxy.exe')
		self.nx_root = nx_root if nx_root else './sessions'
		self.options_file = options_file if options_file else os.path.join(self.nx_root, 'options')
		self.error_log_file = error_log_file if error_log_file else os.path.join(self.nx_root, 'session.err')
		self.log_file = log_file if log_file else os.path.join(self.nx_root, 'session.log')

		#print(self.exe_file)

		self.proc = None


	def mkdir(self, directory):
		try:
			os.makedirs(directory)
		except OSError as e:
			if e.errno == 17:
				# file exists
				pass


	def check_dirs(self):
		self.mkdir(self.nx_root)
		self.mkdir(os.path.dirname(self.options_file))
		self.mkdir(os.path.dirname(self.error_log_file))


	def start(self, cookie, port, display=74):
		self.cookie = cookie
		self.port = port
		self.display = display

		super().start()


	def run(self):
		logging.debug('nxproxy thread id: %s',threading.get_ident())
		self.check_dirs()

		options = [
			"nx/nx" ,
			"retry=5",
			"composite=1",
			"connect=127.0.0.1",
			"clipboard=1",
			"cookie=%s" % self.cookie,
			"port=%s" % self.port,
			"errors=%s" % self.error_log_file,
		]

		f_options = open(self.options_file, 'w')
		f_options.write(u'%s:%s' % (','.join(options), self.display))
		f_options.close()

		cmd = '%s -S nx/nx,options=%s:%s' % (self.exe_file, self.options_file, self.display)
		env = os.environ.copy()
		env.update({"NX_ROOT": self.nx_root, "DISPLAY": "localhost:%s" % self.display})
		_stdin = open('nul', 'r')
		_stdout = open(self.log_file, 'a')
		_stderr = _stdout
		#_stderr = open(self.log_file, 'a')

		logging.debug('Nxproxy cmd: %s' % cmd)#, loglevel=log.loglevel_INFO)

		self.proc = subprocess.Popen(cmd, env=env, stdin=_stdin, stdout=_stdout, stderr=_stderr, creationflags=subprocess.CREATE_NO_WINDOW)

		logging.debug('Nxproxy started')#, loglevel=log.loglevel_INFO)

		self.proc.wait()

		logging.debug('Nxproxy stoped')#, loglevel=log.loglevel_INFO)

		if self.onTerminate:
			self.onTerminate()


	def stop(self):
		if self.proc and not self.proc.returncode:
			self.proc.terminate()
			#self.proc.wait(5)
		

#set NX_ROOT=D:\dev\py-x2go\dev\pyhoca-contrib\mswin\nxproxy-mswin\nxproxy-3.5.0.27_cygwin-2014-10-18\
#set DISPLAY=localhost:40
#echo nx/nx,retry=5,composite=1,connect=127.0.0.1,clipboard=1,cookie=b733124021815192ffe3f892911aa2e2,port=43361,errors=.\nx_session.err:173 > .\nx_options
#%NX_ROOT%nxproxy.exe -S nx/nx,options=.\nx_options:53