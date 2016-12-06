#!c:\Python34\python.exe
# -*- coding: utf-8 -*-

# Copyright (C) 2016, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.

import multiprocessing
import sys
import os
import traceback
import time
from doconverter.tools.Task import Task
from doconverter.config import APPCONFIG
from doconverter.DoconverterException import DoconverterException
from doconverter.tools.Utils import Utils


class ConverterManager(multiprocessing.Process):
    logger = None

    def __init__(self, taskid, list_processes, queue):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        global logger
        logger = Utils.initlogger(queue)
        self.task = Task.getaskbyid(taskid, queue)
        self.converter_class = self.__find_converter()
        self.common_list = list_processes
        logger.debug('Working on {}'.format(self.task.taskid))

    def __find_converter(self):
        for converter in APPCONFIG['converters']:
            if self.task.converter in APPCONFIG['converters'][converter]['output_allowed'] and \
                            self.task.extension in APPCONFIG['converters'][converter]['extensions_allowed']:
                logger.debug('converter class for reflection: %s' % globals()[converter])
                return globals()[converter]
        raise DoconverterException(
            "from {} to {} in task {} no converter defined."
            .format(self.task.extension, self.converter_class, self.task.taskid))

    def run(self):
        converter = self.converter_class(self.task.taskid, self.queue)
        logger = Utils.initlogger(self.queue)
        status = -1
        before = None
        after = None
        try:
            before = time.clock()
            status = converter.convert()
            after = time.clock()
            if status == 0:
                self.task.movetosuccess()
                totalsecs = round(after - before)
                logger. \
                    debug('task {} sucessful: file: {} size: {} KB from: {} to: {} size: {} KB in {} secs'.format(
                        self.task.taskid,
                        self.task.uploadedfile,
                        Utils.getfilesizeinkb(os.path.join(self.task.fullocalpath, self.task.uploadedfile)),
                        self.task.extension,
                        self.task.converter,
                        Utils.getfilesizeinkb(os.path.join(self.task.fullocalpath, self.task.newfilename)),
                        totalsecs))

                self.task.sendbyweb(os.path.join(self.task.fullocalpath, self.task.newfilename), status)
            else:
                self.task.movetoerror()
                totalsecs = round(after - before)
                logger.debug('task {} not converted: file: {} from {} to {} in {} secs'.format(self.task.taskid,
                                                                                               self.task.uploadedfile,
                                                                                               self.task.extension,
                                                                                               self.task.converter,
                                                                                               totalsecs))
                self.task.sendbyweb(None, status)
        except:
            exc_type, exc_value, exc_tb = sys.exc_info()
            logger.debug('Exception got {}. '.format(traceback.print_exception(exc_type, exc_value, exc_tb)))
        finally:
            self.common_list.remove(int(self.task.taskid))
            self.common_list.append(-666)
            if os.path.exists(os.path.join(APPCONFIG['tasks'], self.task.taskid)):
                self.task.movetoerror()
                logger.debug('task {} not converted: file: {} from {} to {} '.format(self.task.taskid,
                                                                                     self.task.uploadedfile,
                                                                                     self.task.extension,
                                                                                     self.task.converter))
                self.task.sendbyweb(None, status)
            sys.exit()
