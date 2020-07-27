# Copyright 2020 by Roman Khuramshin <mr.linqu@gmail.com>.
# All rights reserved.
# This file is part of the Intsa Term Client - X2Go terminal client for Windows,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.


import logging
import threading
import os
import time
import win32print
from .Handler import Handler

class Spooler(threading.Thread):
    isAlive = False
    spool_dir = None


    def __init__(self, spool_dir, printer=None):
        super(Spooler, self).__init__()

        self.spool_dir = spool_dir
        self.printer = printer if printer else win32print.GetDefaultPrinter()

        self.jobs = dict()

        pass


    @staticmethod
    def readJobfile(jobfile):
        _job_file_handle = open(jobfile, 'r')
        content = _job_file_handle.read()
        try:
            (pdf_file, job_title) = content.split('\n')[0:2]
        except ValueError:
            pdf_file = content
            job_title = 'X2Go Print Job'
        _job_file_handle.close()

        return (pdf_file, job_title)
        pass


    def run(self):
        logging.debug('starting print queue thread: %s on dir: %s' % (repr(self), self.spool_dir))
        self.isAlive = True

        while self.isAlive:
            l = os.listdir(self.spool_dir)
            job_files = [ jf for jf in l if jf.endswith('.ready') ]
            #jobs = []
            for jobfile in job_files:
                if jobfile in self.jobs:
                    continue

                _jobfile = os.path.join(self.spool_dir, jobfile)
                (pdf_file, job_title) = Spooler.readJobfile(_jobfile)

                handler = Handler(job_file=jobfile, pdf_file=os.path.join(self.spool_dir, pdf_file),job_title=job_title, onHandled=self.onHandled, printer=self.printer)
                handler.start()
                self.jobs[jobfile] = handler

            time.sleep(3)
        logging.debug('print queue thread stoped')
        pass


    def onHandled(self, jobfile):
        _jobfile = os.path.join(self.spool_dir, jobfile)
        (pdf_file, job_title) = Spooler.readJobfile(_jobfile)
        _pdf_file = os.path.join(self.spool_dir, pdf_file)
        os.remove(_pdf_file)
        os.remove(_jobfile)
        del self.jobs[jobfile]
        pass


    def stop(self):
        self.isAlive = False
        pass

    pass