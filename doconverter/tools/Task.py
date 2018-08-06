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
import random
from doconverter.config import APPCONFIG
from doconverter.tools.Utils import Utils


class Task(object):
    logger = None

    def __init__(self, uploadedfile, converter, urlresponse, diresponse, remotehost=None, server=None,
                 taskid=None, options=None, queue=None):
        global logger
        logger = Utils.initlogger(queue)
        self.queue = queue
        self.uploadedfile = uploadedfile
        self.converter = converter.lower()
        self.urlresponse = urlresponse
        self.diresponse = diresponse
        if remotehost:
            self.remotehost = remotehost
        else:
            self.remotehost = '0.0.0.0'
        self.extension = self.uploadedfile.split('.')[-1].lower()
        if not server:
            self.server = self.decidequeue(self.extension, self.converter)
        else:
            self.server = server
        if not taskid:
            self.taskid = Utils.generate_taskid(self.server)
        else:
            self.taskid = taskid
        self.fullocalpath = os.path.join(APPCONFIG[self.server]['uploadsresults'], str(self.taskid))
        if options:
            self.options = options
        else:
            self.options = ''
        if converter == 'pdfa':
            self.newfilename = self.uploadedfile.replace(self.uploadedfile.split('.')[-1], 'pdf')
        elif converter.startswith('thumb'):
            # Neevia converter adds a number to each page of the document converted to PNG
            self.newfilename = '{}1.png'.format(os.path.splitext(self.uploadedfile)[0])
        elif converter.startswith('toimg'):
            # Neevia converter adds a number to each page of the document converted to PNG, result will be compressed
            if 'tiff' not in self.options.lower():
                self.newfilename = '{}.zip'.format(self.uploadedfile.split('.')[0])
            else:
                self.newfilename = self.uploadedfile.replace(self.uploadedfile.split('.')[-1], 'tif')
        elif converter.startswith('hpgl') or converter.startswith('tesocr'):
            self.newfilename = self.uploadedfile.replace(self.uploadedfile.split('.')[-1], 'pdf')
        elif converter.startswith('modiocr'):
            self.newfilename = self.uploadedfile.replace(self.uploadedfile.split('.')[-1], 'pdf')
        else:
            self.newfilename = self.uploadedfile.replace(self.uploadedfile.split('.')[-1], self.converter)
        logger.info('%s newfilename is %s' % (self.taskid, self.newfilename))
        self.__createTask()

    def __createTask(self):
        """Internal method to create the physical location (directory + file) for the task"""
        if not os.path.exists(os.path.join(APPCONFIG[self.server]['uploadsresults'], str(self.taskid))):
            os.makedirs(os.path.join(APPCONFIG[self.server]['uploadsresults'], str(self.taskid)))
            logger.debug('we created dir: %s', os.path.join(APPCONFIG[self.server]['uploadsresults'], str(self.taskid)))
        # create initial file task
        self.__createFileTask(os.path.join(APPCONFIG[self.server]["tasks"], str(self.taskid)))

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
            'newfilename': self.newfilename,
            'server': self.server,
            'remotehost': self.remotehost,
            'options': self.options
        }
        with open(path, 'w') as outfile:
            json.dump(data, outfile)

        logger.info('new taskid {} from remote_host: {} ext_from: {} ext_to: {}'.format(self.taskid, self.remotehost,
                                                                                        self.extension, self.converter))

    @staticmethod
    def getaskbyid(taskid, queue=None, dir=None):
        """Get Task by id

        :param taskid:
        :param queue: in case of multiprocess logging
        :param dir: in case of different worker node, processing tasks of node A from node B
        :return:
        """
        if not dir:
            server = Utils.get_server_name()
            dir = APPCONFIG[server]['tasks']
        if os.path.exists(os.path.join(dir, taskid)):
            # Iterate as max 5 times
            i = 0
            while not Utils.isfileolderthan(os.path.join(dir, taskid), 5) & i < 5:
                # sleep a sec to give time to EOS...
                i += 1
                time.sleep(1)
            Utils.logmessage('{} reading json file.'.format(taskid))
            with open(os.path.join(dir, taskid)) as data_file:
                data = json.load(data_file)

            if 'options' in data.keys():
                return Task(uploadedfile=data['uploadedfile'], converter=data['converter'],
                            urlresponse=data['urlresponse'], diresponse=data['diresponse'], server=data['server'],
                            remotehost=data['remotehost'], options=data['options'], taskid=taskid, queue=queue)
            else:
                return Task(uploadedfile=data['uploadedfile'], converter=data['converter'],
                            urlresponse=data['urlresponse'], diresponse=data['diresponse'], server=data['server'],
                            remotehost=data['remotehost'], options=None, taskid=taskid, queue=queue)
        return None

    def decidequeue(self, fromext, converter):
        """Decide which queue should be used in order to work with a particular extension

        :return: queue (a server name, without extension)
        """
        possibles = []
        for server in APPCONFIG['servers']:
            if fromext in APPCONFIG[server]['extensions_allowed'] and \
                    converter.split('_')[0] in APPCONFIG[server]['extensions_allowed']:
                    possibles.append(server)
        return random.choice(possibles)

    def movetosuccess(self):
        """Move a task file to the right directory. It acts as a kind of state machine.

        :return: True if the taskfile could be moved and False in case there was an issue
        """
        if os.path.isfile(os.path.join(APPCONFIG[self.server]['tasks'], self.taskid)):
            shutil.move(os.path.join(APPCONFIG[self.server]['tasks'], self.taskid),
                        os.path.join(APPCONFIG[self.server]['success'], self.taskid))
            Utils.logmessage('{} moving {} to {}'.format(self.taskid,
                                                         os.path.join(APPCONFIG[self.server]['tasks'], self.taskid),
                                                         os.path.join(APPCONFIG[self.server]['success'], self.taskid)),
                             self.queue)
        else:
            Utils.logmessage('task file %s doesnt exist, strange!'
                             .format(os.path.join(APPCONFIG[self.server]['tasks'], self.taskid)),
                             self.queue)
            return False
        return True

    def movetoerror(self):
        """Move a task file to the right directory. It acts as a kind of state machine.

        :return: True if the taskfile could be moved and False in case there was an issue
        """
        if os.path.isfile(os.path.join(APPCONFIG[self.server]['tasks'], self.taskid)):
            shutil.move(os.path.join(APPCONFIG[self.server]['tasks'], self.taskid),
                        os.path.join(APPCONFIG[self.server]['error'], self.taskid))
            Utils.logmessage('{} moving from {} to {}'.format(self.taskid,
                                                              os.path.join(APPCONFIG[self.server]['tasks'],
                                                                           self.taskid),
                                                              os.path.join(APPCONFIG[self.server]['error'],
                                                                           self.taskid)),
                             self.queue)
        else:
            Utils.logmessage('task file %s doesnt exist, strange!'.format(
                os.path.join(APPCONFIG[self.server]['tasks'], self.taskid)),
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
            status = 1  # success
        payload = {
            'directory': self.diresponse,
            'status': status,
            'filename': self.newfilename,
            'error_message': status
        }
        before = time.clock()
        if pathtofile and os.path.exists(pathtofile):
            try:
                response = requests.post(self.urlresponse,
                                         data=payload,
                                         files={'content': open(pathtofile, 'rb')},
                                         verify=False)

                if response.status_code >= 300:
                    raise requests.RequestException('{} Unexpected response from server: {}'.format(self.taskid,
                                                                                                    response.text))
                    Utils.logmessage('{} result submitted to callback'.format(self.taskid))
            except Exception as ex:
                Utils.logmessage('Exception name is {} and exception: {}'
                                 .format(ex.__module__ + "." + ex.__class__.__qualname__, ex))
        else:
            try:
                response = requests.post(self.urlresponse, data=payload, verify=APPCONFIG['ca_bundle'])
                if response.status_code >= 300:
                    Utils.logmessage('{} error while sending file {} to {}'.format(self.taskid, pathtofile, self.urlresponse))
                else:
                    Utils.logmessage('{} success sending file {} to {}'.format(self.taskid, pathtofile, self.urlresponse))
            except Exception as ex:
                Utils.logmessage('Exception name is {} and exception: {}'.format(ex.__module__ + "." + ex.__class__.__qualname__, ex))
        totalsecs = round(time.clock() - before)
        Utils.logmessage('{} sending file {} to {} took: {} secs'.format(self.taskid, pathtofile, self.urlresponse,
                                                                         totalsecs))
