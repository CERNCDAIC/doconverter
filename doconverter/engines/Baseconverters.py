#!c:\Python34\python.exe
# -*- coding: utf-8 -*-

# Copyright (C) 2017, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.


import os
import time
import random
from doconverter.tools.Task import Task
from doconverter.tools.Utils import Utils
from doconverter.config import APPCONFIG


class Baseconverters(object):
    logger = None

    def __init__(self, taskid, queue=None):
        Baseconverters.logger = Utils.initlogger(queue)
        self.task = Task.getaskbyid(taskid=taskid, queue=queue)
        self.error_dir = os.path.join(APPCONFIG[self.task.server]['error'], self.task.taskid)
        self.success_dir = os.path.join(APPCONFIG[self.task.server]['uploadsresults'], self.task.taskid)
        self.hash_options = {}
        if self.task.options:
            self.hash_options = Utils.convertohash(self.task.options)

    def isfileready(self):
        # sleep randomly to reduce likelihood of -3 Invalid input folder error
        if not os.path.exists(os.path.join(self.task.fullocalpath, self.task.uploadedfile)):
            for x in range(0, 30):
                if os.path.exists(os.path.join(self.task.fullocalpath, self.task.uploadedfile)):
                    Baseconverters.logger.debug('{} file: {} already there!'
                                                .format(self.task.taskid,
                                                        os.path.join(self.task.fullocalpath, self.task.uploadedfile)))
                    break
                Baseconverters.logger.debug('{} file: {} not there. Wait for EOS sync'
                                            .format(self.task.taskid,
                                                    os.path.join(self.task.fullocalpath, self.task.uploadedfile)))
                time.sleep(1)


        size_file = os.stat(os.path.join(self.task.fullocalpath, self.task.uploadedfile)).st_size
        while True:
            time.sleep(1)
            if os.stat(os.path.join(self.task.fullocalpath, self.task.uploadedfile)).st_size > size_file:
                size_file = os.stat(os.path.join(self.task.fullocalpath, self.task.uploadedfile)).st_size
                time.sleep(random.randint(0, 15))
                Baseconverters.logger.debug('file: {} still being copied size is {} bytes'.format(
                    os.path.join(self.task.fullocalpath, self.task.uploadedfile),
                    size_file))
            elif os.stat(os.path.join(self.task.fullocalpath, self.task.uploadedfile)).st_size == size_file:
                Baseconverters.logger.debug('file: {} got stationary size: {} bytes'.format(
                    os.path.join(self.task.fullocalpath, self.task.uploadedfile),
                    size_file))
                break
            else:
                Baseconverters.logger.debug('file: {} must have been fully copied, leaving loop'.format(
                    os.path.join(self.task.fullocalpath, self.task.uploadedfile)))
                return True
