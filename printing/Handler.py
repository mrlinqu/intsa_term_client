# Copyright 2020 by Roman Khuramshin <mr.linqu@gmail.com>.
# All rights reserved.
# This file is part of the Intsa Term Client - X2Go terminal client for Windows,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.


import logging
import threading
import os
from resource import resource_path

import subprocess


class Handler(threading.Thread):
    def __init__(self, job_file, pdf_file, job_title, onHandled, printer):
        super(Handler, self).__init__()

        self.job_file = job_file
        self.pdf_file = pdf_file
        self.job_title = job_title
        self.onHandled = onHandled

        self.printer = '%s%s' % ('%printer%', printer)

        self.exe_file = resource_path(os.path.join('gsview','gswin64c.exe'))

        pass


    def run(self):
        logging.info('printing incoming PDF file %s' % self.pdf_file)
        
        logging.debug('printer name is ,,%s\'\'' % self.printer)

        try:
            cmd = '%s -sDEVICE=mswinpr2 -dBATCH -dNOPAUSE -dNoCancel -sOutputFile="%s" %s' % (self.exe_file, self.printer, self.pdf_file)
            opts = {
                'stdin': open('nul', 'r'),
                'stdout':  open('nul', 'r'), #open(self.log_file, 'a'),
                'stderr': open('nul', 'r'), #open(self.log_file, 'a'),
            }

            logging.debug('printing cmd: %s' %  cmd)

            self.proc = subprocess.Popen(cmd, **opts)
            self.proc.wait()

            self.onHandled(self.job_file)

            logging.debug('printing finish %s' % self.pdf_file)

        except Exception as e:
            logging.error('printing error: %s' %  str(e))
            pass

        pass


    def stop(self):
        pass


    pass
