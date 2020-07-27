# Copyright 2020 by Roman Khuramshin <mr.linqu@gmail.com>.
# All rights reserved.
# This file is part of the Intsa Term Client - X2Go terminal client for Windows,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.


import os
import shutil
import paramiko
import errno
import logging


########################################################################################################
########################################################################################################


class SFTPHandle(paramiko.SFTPHandle):
    def stat(self):
        try:
            return paramiko.SFTPAttributes.from_stat(os.fstat(self.readfile.fileno()))
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

    def chattr(self, attr):
        # python doesn't have equivalents to fchown or fchmod, so we have to
        # use the stored filename
        try:
            paramiko.SFTPServer.set_file_attr(self.filename, attr)
            return paramiko.SFTP_OK
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)


########################################################################################################
########################################################################################################


class SFTPInterface(paramiko.SFTPServerInterface):

    def __init__(self, server, *largs, **kwargs):
        super(SFTPInterface, self).__init__(server, *largs, **kwargs)
    
        #self.client = paramiko.SFTPClient.from_transport(server.client.get_transport())
        self.root_path = server.root_path if ('root_path' in server.__dict__) else ''

    ####################################################################################################

    def _realpath(self, path):
        if path.startswith('/windrive'):
            _path_components = path.split('/')
            _drive = _path_components[2]
            _tail_components = (len(_path_components) > 3) and _path_components[3:] or ''
            _tail = os.path.normpath('/'.join(_tail_components))
            path = os.path.join('%s:' % _drive, '/', _tail)
        else:
            path = self.root_path + self.canonicalize(path)
            path = path.replace('//', '/')
        
        return path

    ####################################################################################################

    def list_folder(self, path):
        logging.debug('sFTP server: listing files in folder: %s' % path)

        try:
            folder = self._realpath(path)
            out = []
            flist = os.listdir(folder)
            for fname in flist:
                try:
                    attr = paramiko.SFTPAttributes.from_stat(os.lstat(os.path.join(folder, fname)))
                    attr.filename = fname
                    logging.debug('sFTP server %s: file attributes ok: %s' % (self, fname))
                    out.append(attr)
                except OSError as e:
                    logging.debug('sFTP server %s: encountered error processing attributes of file %s: %s' % (self, fname, str(e)))

            logging.debug('sFTP server: folder list is : %s' % str([ a.filename for a in out ]))
            return out
        except OSError as e:
            logging.debug('sFTP server %s: encountered error: %s' % (self, str(e)))
            return paramiko.SFTPServer.convert_errno(e.errno)

    ####################################################################################################

    def stat(self, path):
        logging.debug('sFTP server %s: calling stat on path: %s' % (self, path))
        try:
            return paramiko.SFTPAttributes.from_stat(os.stat(self._realpath(path)))
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

    ####################################################################################################

    def lstat(self, path):
        logging.debug('sFTP server: calling lstat on path: %s' % path)
        try:
            return paramiko.SFTPAttributes.from_stat(os.lstat(self._realpath(path)))
        except OSError as e:
            logging.debug('sFTP server %s: encountered error: %s' % (self, str(e)))
            return paramiko.SFTPServer.convert_errno(e.errno)

    ####################################################################################################

    def open(self, path, flags, attr):
        logging.debug('sFTP server %s: opening file: %s' % (self, path))
        
        path = self._realpath(path)

        try:
            binary_flag = getattr(os, 'O_BINARY',  0)
            flags |= binary_flag
            mode = getattr(attr, 'st_mode', None)
            if mode is not None:
                fd = os.open(path, flags, mode)
            else:
                # os.open() defaults to 0777 which is
                # an odd default mode for files
                fd = os.open(path, flags, 0o666)
        except OSError as e:
            logging.debug('sFTP server %s: encountered error: %s' % (self, str(e)))
            return paramiko.SFTPServer.convert_errno(e.errno)

        if (flags & os.O_CREAT) and (attr is not None):
            attr._flags &= ~attr.FLAG_PERMISSIONS
            paramiko.SFTPServer.set_file_attr(path, attr)
        
        if flags & os.O_WRONLY:
            if flags & os.O_APPEND:
                fstr = 'ab'
            else:
                fstr = 'wb'
        elif flags & os.O_RDWR:
            if flags & os.O_APPEND:
                fstr = 'a+b'
            else:
                fstr = 'r+b'
        else:
            # O_RDONLY (== 0)
            fstr = 'rb'
        
        try:
            f = os.fdopen(fd, fstr)
        except OSError as e:
            logging.debug('sFTP server %s: encountered error: %s' % (self, str(e)))
            return paramiko.SFTPServer.convert_errno(e.errno)

        fobj = SFTPHandle(flags)
        fobj.filename = path
        fobj.readfile = f
        fobj.writefile = f
        return fobj

    ####################################################################################################

    def remove(self, path):
        logging.debug('sFTP server %s: removing file: %s' % (self, path))

        path = self._realpath(path)

        try:
            os.remove(path)
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

        return paramiko.SFTP_OK

    ####################################################################################################

    def rename(self, oldpath, newpath):
        logging.debug('sFTP server %s: renaming path from %s to %s' % (self, oldpath, newpath))
        
        oldpath = self._realpath(oldpath)
        newpath = self._realpath(newpath)

        try:
            shutil.move(oldpath, newpath)
        except OSError as e:
            logging.debug('sFTP server %s: encountered error: %s' % (self, str(e)))
            return paramiko.SFTPServer.convert_errno(e.errno)
        
        return paramiko.SFTP_OK
        
    ####################################################################################################

    def mkdir(self, path, attr):
        logging.debug('sFTP server: creating new dir (perms: %s): %s' % (attr.st_mode, path))
        
        path = self._realpath(path)

        try:
            os.mkdir(path, attr.st_mode)
        except OSError as e:
            logging.debug('sFTP server %s: encountered error: %s' % (self, str(e)))
            return paramiko.SFTPServer.convert_errno(e.errno)

        return paramiko.SFTP_OK

    ####################################################################################################

    def rmdir(self, path):
        logging.debug('sFTP server %s: removing dir: %s' % (self, path))
        
        path = self._realpath(path)
        
        try:
            shutil.rmtree(path)
        except OSError as e:
            logging.debug('sFTP server %s: encountered error: %s' % (self, str(e)))
            return paramiko.SFTPServer.convert_errno(e.errno)
        
        return paramiko.SFTP_OK

    ####################################################################################################

    def chattr(self, path, attr):
        logging.debug('sFTP server %s: modifying attributes of path: %s' % (self, path))
        
        path = self._realpath(path)

        try:
            if attr.st_mode is not None:
                os.chmod(path, attr.st_mode)
            #if attr.st_uid is not None:
            #    os.chown(path, attr.st_uid, attr.st_gid)
        except OSError as e:
            logging.debug('sFTP server %s: encountered error: %s' % (self, str(e)))
            return paramiko.SFTPServer.convert_errno(e.errno)
        
        return paramiko.SFTP_OK

    ####################################################################################################

    def symlink(self, target_path, path):
        logging.debug('sFTP server %s: creating symlink from: %s to target: %s' % (self, path, target_path))
        
        path = self._realpath(path)
        
        if target_path.startswith('/'):
            target_path = self._realpath(target_path)
        
        try:
            os.symlink(target_path, path)
        except OSError as e:
            logging.debug('sFTP server %s: encountered error: %s' % (self, str(e)))
            return paramiko.SFTPServer.convert_errno(e.errno)
        
        return paramiko.SFTP_OK

    ####################################################################################################

    def readlink(self, path):
        logging.debug('sFTP server %s: reading symlink from: %s' % (self, path))

        path = self._realpath(path)
        
        try:
            return os.readlink(path)
        except OSError as e:
            logging.debug('sFTP server %s: encountered error: %s' % (self, str(e)))
            return paramiko.SFTPServer.convert_errno(e.errno)
    
    ####################################################################################################

    def session_ended(self):
        #if self.server_event is not None:
        #    logging.debug('sFTP server %s: session has ended' % self)
        #    self.server_event.set()
        pass
        
