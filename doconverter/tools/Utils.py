#!c:\Python34\python.exe
# -*- coding: utf-8 -*-

# Copyright (C) 2017, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.

import os
import platform
import random
import logging
import psutil
import smtplib
import platform
from email.mime.text import MIMEText
from logging.handlers import QueueHandler
from doconverter.config import APPCONFIG
from datetime import datetime


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
    def generate_taskid(server=None):
        """Generate a taskid that should be unique among possible current running tasks"""
        Utils.__getlogging()
        Utils.logger.info('checking possible taskid')
        randome = os.urandom(24)
        random.seed(randome)
        taskid = random.randint(0, 999999999)
        while True:
            Utils.logger.info('checking possible taskid %s', taskid)
            if not server:
                server = Utils.getserver()
            if not os.path.isfile(os.path.join(APPCONFIG[server]['tasks'], str(taskid))) \
                    and not os.path.isfile(os.path.join(APPCONFIG[server]['error'], str(taskid))) \
                    and not os.path.isfile(os.path.join(APPCONFIG[server]['success'], str(taskid))) \
                    and not os.path.exists(os.path.join(APPCONFIG[server]['uploadsresults'], str(taskid))):
                        break
            taskid = random.randint(0, 999999999)
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
        if extension in list_extensions:
            return True
        return False

    @staticmethod
    def sortfilesbytime(dirpath):
        """Gives back an array of files (tasks) to be processed ordered by creation time

        :param dirpath:
        :return: an array of files ordered by ctime
        """
        listoffiles = [s for s in os.listdir(dirpath) if os.path.isfile(os.path.join(dirpath, s))]
        listoffiles.sort(key=lambda s: os.path.getctime(os.path.join(dirpath, s)))
        return listoffiles

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
        Utils.logger.debug('{} found: {} times'.format(pythonfile, counter))
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


