#!c:\Python34\python.exe
# -*- coding: utf-8 -*-

# Copyright (C) 2017, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.

import os
import random
import logging
import psutil
import smtplib
import platform
import fnmatch
import zipfile
import time
import subprocess
from email.mime.text import MIMEText
from logging.handlers import QueueHandler
from doconverter.config import APPCONFIG


class Utils(object):
    logger = None
    server_name = None

    @staticmethod
    def get_server_name():
        if not Utils.server_name:
            Utils.server_name = Utils.getserver()
        return Utils.server_name

    @staticmethod
    def set_server_name(name):
        Utils.server_name = name

    @staticmethod
    def __getlogging():
        if __name__ == '__main__':
            Utils.logger = logging.getLogger('doconverter-console')
        else:
            Utils.logger = logging.getLogger('doconverter-api')

    @staticmethod
    def isfileolderthan(file, secs=5):
        """Return True if file is older than X secs (5 as default), False otherwise

        :param: secs - seconds a file should be older to return True
        :param: file - file to check
        :return:
        """

        file_time = round(os.stat(file).st_mtime)
        if (time.time() - file_time) > secs:
            return True
        return False

    @staticmethod
    def generate_taskid(server=None):
        """Generate a taskid that should be unique among possible current running tasks"""
        Utils.__getlogging()
        Utils.logger.info('checking possible taskid')
        randome = os.urandom(24)
        random.seed(randome)
        taskid = round(time.time()) + random.randint(0, 99999)
        while True:
            Utils.logger.info('checking possible taskid %s', taskid)
            if not server:
                server = Utils.getserver()
            if not os.path.isfile(os.path.join(APPCONFIG[server]['tasks'], str(taskid))) \
                    and not os.path.isfile(os.path.join(APPCONFIG[server]['error'], str(taskid))) \
                    and not os.path.isfile(os.path.join(APPCONFIG[server]['success'], str(taskid))) \
                    and not os.path.exists(os.path.join(APPCONFIG[server]['uploadsresults'], str(taskid))):
                        break
            taskid = round(time.time()) + random.randint(0, 99999)
        Utils.logger.info("new taskid generated %s" % taskid)
        return taskid

    @staticmethod
    def getserver():
        '''Returns actual server where the script is running, with no domain

        :return:
        '''
        server = platform.node()
        return server.split('.')[0]

    @staticmethod
    def allowed_filextension(extension, list_extensions):
        """Check if a given extension is allowed by the possible extensions

        :param: extension - to be check if it's on the list e.g. docx (for Microsoft Word)
        :param: list_extentions - list of possible extensions
        :return: True or False
        """
        if extension.lower() in list_extensions:
            return True
        return False

    @staticmethod
    def sortfilesbytime(dirpath):
        """Gives back an array of files (tasks) to be processed ordered by creation time

        :param dirpath:
        :return: an array of files ordered by ctime
        """
        listoffiles = [s for s in os.listdir(dirpath)
                       if (os.path.isfile(os.path.join(dirpath, s))
                           and not s.startswith('.')
                           and os.path.getsize(os.path.join(dirpath, s)) > 0)]
        listoffiles.sort(key=lambda s: os.path.getctime(os.path.join(dirpath, s)))
        return listoffiles

    @staticmethod
    def totalpendingtasks(basedirpath, servers):
        """Tasks folder to be verified

        :param dirpath:
        :return: an array of files ordered by ctime
        """
        total = 0
        for s in servers:
            dir = os.path.join(*[basedirpath, s, 'var', 'tasks'])
            total += len(os.listdir(dir))
        return total

    @staticmethod
    def initlogger(queue=None):
        """

        :return: it returns a logger object with a handler to treat logging from multiprocess environment
        """
        logger = None
        if __name__ == '__main__':
            logger = logging.getLogger('doconverter-console')
        else:
            logger = logging.getLogger('doconverter-api')
        flag = False
        if queue:
            for handler in logger.handlers:
                if isinstance(handler, logging.handlers.QueueHandler):
                    flag = True
                    break
            if not flag:
                qh = QueueHandler(queue)
                logger.addHandler(qh)
        return logger

    @staticmethod
    def logmessage(str, queue=None):
        """

        :param str: message to log
        :return:
        """
        logger = Utils.initlogger(queue)
        logger.debug(str)

    @staticmethod
    def isprocess_running(pythonfile, exe=None):
        """ A platform independent way to check if a process is running.

        :param str: command line to check for
        :param exe: executable in case of need, avoid false positive like an editor that has open the file
        :return: number of instances found in the process space
        """

        counter = 0
        for process in psutil.process_iter():
            try:
                for item in process.cmdline():
                    if pythonfile in item:
                        if exe:
                            if exe in process.cmdline()[0]:
                                counter += 1
                                break
                        else:
                            counter += 1
                            break
            except psutil.AccessDenied:
                pass
        Utils.__getlogging()
        if exe:
            Utils.logger.debug('py file: {} and exe: {} found: {} times'.format(pythonfile, exe, counter))    
        else:
            Utils.logger.debug('py file: {} found: {} times'.format(pythonfile, counter))    
        return counter

    @staticmethod
    def getfilesizeinkb(path):
        '''Retrieves size of a given file.

        :param path: location of the file
        :return: size in kb
        '''
        if os.path.isfile(path):
            return round(os.path.getsize(path)/1024)
        return 0

    @staticmethod
    def sendemail(tos, subject, msg, server):
        '''

        :param tos:
        :param subject:
        :param msg:
        :param server:
        :return:
        '''

        # Prepare the email
        if len(msg) == 0:
            Utils.logger('no message provided')
            return False
        message = '\n'.join(map(str, msg))
        message = MIMEText(message)
        if not tos:
            Utils.logger('No recipients!')
            return False
        message['To'] = ', '.join(tos)
        if not subject:
            Utils.logger('No subject, bad practise!')
            return False
        message['Subject'] = subject
        message['From'] = 'doconverter.noreply@cern.ch'
        s = None
        try:
            s = smtplib.SMTP(server)
            s.send_message(message)
        except Exception as ex:
            Utils.logger('Problem sending email: %e', ex)
        finally:
            s.quit()
        return True

    @staticmethod
    def convertohash(juststr):
        '''

        :param juststr: an string with format: a=b:c=d:....
        :return: a dictionary
        '''
        list_options = juststr.split(':')
        hash_options = {}
        for item in list_options:
            k, v = item.split('=')
            hash_options[k] = v
        return hash_options

    @staticmethod
    def getresolutionsettings(typeofimg, options):
        '''

        :param converter: it's the desired output of a conversion e.g. thumb, pdf, pdfa
        :return: a tupple with image resolution (dpi) and size (pixels) (imgresh, imgresv, imgheight, imgwidth)
        '''
        Utils.__getlogging()
        imgresh = 300
        imgresv = 300
        imgheight = 0
        imgwidth = 0
        if typeofimg.lower() == 'thumb':
            imgheight = 200
            imgwidth = 200
        if not options:
            # apply defaults
            Utils.logger.debug('Following dpi: imgresh: {} imgresv {} and dimensions: imgheight {} imgwidth {}'
                               .format(imgresh, imgresv, imgheight, imgwidth))
            return (imgresh, imgresv, imgheight, imgwidth)

        Utils.logger.debug('options are {}'.format(options))
        dpi_res = ('72x72', '100x100', '150x150', '200x200', '300x300', '400x400', '600x600', '1200x1200')
        hash_options = Utils.convertohash(options)
        # defaults
        imgresh = hash_options.get('imgresh', 300)
        imgresv = hash_options.get('imgresv', 300)
        if typeofimg.lower() == 'thumb':
            imgheight = hash_options.get('imgheight', 200)
            imgwidth = hash_options.get('imgwidth', 200)
        else:
            imgheight = hash_options.get('imgheight', 0)
            imgwidth = hash_options.get('imgwidth', 0)
        if not '{}x{}'.format(imgresh, imgresv) in dpi_res:
            Utils.logger.debug("Specified dpi: %s is not alloweed" % '{}x{}'.format(imgresh, imgresv))
            return {}
        Utils.logger.debug('Following dpi: imgresh: {} imgresv {} and dimensions: imgheight {} imgwidth {}'
                           .format(imgresh, imgresv, imgheight, imgwidth))
        return (imgresh, imgresv, imgheight, imgwidth)

    @staticmethod
    def createzipfile(fromwhere, pattern, finalzipfile):
        '''

        :param fromwhere: parent directory e.g. Y:\\conv-test02\\var\\uploadsresults\\184627739
        :param pattern: which files to compress
        :param finalzipfile: full path to zip file e.g. Y:\\conv-test02\\var\\uploadsresults\\184627739\\file.zip
        :return:
        '''
        Utils.__getlogging()
        Utils.logger.debug('Creating Zipfile {}'.format(finalzipfile))
        if 'jpeg' in pattern:
            pattern = pattern.replace('jpeg', 'jpg')
        result = fnmatch.filter(os.listdir(fromwhere), pattern)
        with zipfile.ZipFile(finalzipfile, 'w', zipfile.ZIP_DEFLATED) as zip:
            for f in result:
                Utils.logger.debug('Zipping {}'.format(os.path.join(fromwhere, f)))
                zip.write(os.path.join(fromwhere, f), arcname=f)

    @staticmethod
    def syscom(cmd, read_output=True, shell=False):
        """
            Execute a process
        """
        Utils.__getlogging()
        if type(cmd) is list:
            Utils.logger.debug("syscom: %s" % subprocess.list2cmdline(cmd))
        else:
            Utils.logger.debug("syscom: %s" % cmd)

        p = None
        if not read_output:
            p = subprocess.Popen(cmd, shell=shell)
        else:
            p = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, _ = p.communicate()
            out_list = out.splitlines()
            Utils.logger.debug("Output: {}".format(out.decode().replace(r"\r\n", r"\n")))

        return p.returncode, out_list
