#!c:\Python34\python.exe
# -*- coding: utf-8 -*-

# Copyright (C) 2017, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.


import os
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
