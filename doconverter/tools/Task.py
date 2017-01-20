#!c:\Python34\python.exe
# -*- coding: utf-8 -*-

# Copyright (C) 2017, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.

import os
import json
import shutil
import requests
import time
from doconverter.config import APPCONFIG
from doconverter.tools.Utils import Utils


class Task(object):
    logger = None

    def __init__(self, uploadedfile, converter, urlresponse, diresponse, taskid=None, queue=None):
        global logger
        logger = Utils.initlogger(queue)
        self.queue = queue
        self.uploadedfile = uploadedfile
        if not taskid:
            self.taskid = Utils.generate_taskid()
        else:
            self.taskid = taskid
        self.converter = converter
        self.urlresponse = urlresponse
        self.diresponse = diresponse
        logger.info('taskid %s' % self.taskid)
        self.fullocalpath = os.path.join(APPCONFIG['uploadsresults'], str(self.taskid))
        self.extension = self.uploadedfile.split('.')[1].lower()
        if converter == 'pdfa':
            self.newfilename = self.uploadedfile.replace(self.uploadedfile.split('.')[1], 'pdf')
        else:
            self.newfilename = self.uploadedfile.replace(self.uploadedfile.split('.')[1], self.converter)
        logger.info('%s newfilename is %s' % (self.taskid, self.newfilename))
        self.__createTask()

    def __createTask(self):
        """Internal method to create the physical location (directory + file) for the task"""
        if not os.path.exists(os.path.join(APPCONFIG['uploadsresults'], str(self.taskid))):
            os.makedirs(os.path.join(APPCONFIG['uploadsresults'], str(self.taskid)))
            logger.debug('we created dir: %s', os.path.join(APPCONFIG['uploadsresults'], str(self.taskid)))
        # create initial file task
        self.__createFileTask(os.path.join(APPCONFIG["tasks"], str(self.taskid)))

    def __createFileTask(self, path):
        """Create a file with the task to be done. The contents are a json type.

        :param path: string --location of the file
        :return:
        """
        if os.path.isfile(path):
            logger.info('file already present %s', path)
            return

        data = {
            'taskid': self.taskid,
            'converter': self.converter,
            'urlresponse': self.urlresponse,
            'diresponse': self.diresponse,
            'uploadedfile': self.uploadedfile,
            'fullocalpath': self.fullocalpath,
            'extension': self.extension,
            'newfilename': self.newfilename
        }
        with open(path, 'w') as outfile:
            json.dump(data, outfile)

    @staticmethod
    def getaskbyid(taskid, queue=None, dir=APPCONFIG['tasks']):
        """It generates a task object from a taskid.

        :param taskid - taskid of the task object
        :return:
        """

        if os.path.exists(os.path.join(dir, taskid)):
            with open(os.path.join(dir, taskid)) as data_file:
                data = json.load(data_file)
            return Task(data['uploadedfile'], data['converter'], data['urlresponse'], data['diresponse'], taskid, queue)
        return None

    def movetosuccess(self):
        """Move a task file to the right directory. It acts as a kind of state machine.

        :return: True if the taskfile could be moved and False in case there was an issue
        """
        if os.path.isfile(os.path.join(APPCONFIG['tasks'], self.taskid)):
            shutil.move(os.path.join(APPCONFIG['tasks'], self.taskid),
                        os.path.join(APPCONFIG['success'], self.taskid))
            Utils.logmessage('{} moving {} to {}'.format(self.taskid,
                                                         os.path.join(APPCONFIG['tasks'], self.taskid),
                                                         os.path.join(APPCONFIG['success'], self.taskid)), self.queue)
        else:
            Utils.logmessage('task file %s doesnt exist, strange!'
                             .format(os.path.join(APPCONFIG['tasks'], self.taskid)),
                             self.queue)
            return False
        return True

    def movetoerror(self):
        """Move a task file to the right directory. It acts as a kind of state machine.

        :return: True if the taskfile could be moved and False in case there was an issue
        """
        if os.path.isfile(os.path.join(APPCONFIG['tasks'], self.taskid)):
            shutil.move(os.path.join(APPCONFIG['tasks'], self.taskid),
                        os.path.join(APPCONFIG['error'], self.taskid))
            Utils.logmessage('{} moving from {} to {}'.format(self.taskid,
                                                              os.path.join(APPCONFIG['tasks'], self.taskid),
                                                              os.path.join(APPCONFIG['error'], self.taskid)),
                             self.queue)
        else:
            Utils.logmessage('task file %s doesnt exist, strange!'.format(
                os.path.join(APPCONFIG['tasks'], self.taskid)),
                             self.taskid)
            return False
        return True

    def convertedfile_exists(self):
        ''' Check if the onverted file is present

        :return: Path to the converted file if exists, and False otherwise
        '''
        if os.path.exists(os.path.join(self.fullocalpath, self.newfilename)):
            return os.path.join(self.fullocalpath, self.newfilename)
        return False

    def sendbyweb(self, pathtofile, status):
        """Send the converted file to the specified location

        :param pathtofile - location of the converted file that needs to be sent back
        :param status - result of conversion. It needs to be 1 if success, otherwise error
        :return:
        """
        if not status:
            status = 1 # sucess
        payload = {
            'directory': self.diresponse,
            'status': status,
            'filename': self.newfilename,
            'error_message': status
        }
        before = time.clock()
        if pathtofile and os.path.exists(pathtofile):
            logger.info('Sending file 1')
            response = requests.post(self.urlresponse,
                                     data=payload,
                                     files={'content': open(pathtofile, 'rb')},
                                     verify=False)
            logger.info('Sending file 2')
            if response.status_code >= 300:
                raise requests.RequestException('{} Unexpected response from server: {}'.format(self.taskid,
                                                                                                response.text))
            logger.info('{} result submitted to callback'.format(self.taskid))
        else:
            response = requests.post(self.urlresponse, data=payload, verify=False)
            if response.status_code >= 300:
                logger.debug('{} error while sending file {} to {}'.format(self.taskid, pathtofile, self.urlresponse))
            else:
                logger.info('{} success sending file {} to {}'.format(self.taskid, pathtofile, self.urlresponse))

        totalsecs = round(time.clock() - before)
        logger.info('Sending file {} to {} took: {} secs'.format(pathtofile, self.urlresponse, totalsecs))
