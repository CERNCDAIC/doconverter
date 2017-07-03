#!c:\Python34\python.exe
# -*- coding: utf-8 -*-

# Copyright (C) 2017, CERN
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
from doconverter.engines.Neevia import Neevia  # noqa


class ConverterManager(multiprocessing.Process):
    logger = None

    def __init__(self, taskid, server, list_processes, queue):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        global logger
        logger = Utils.initlogger(queue)
        Utils.set_server_name(server)
        self.server = server
        self.task = Task.getaskbyid(taskid=taskid, queue=queue, dir=APPCONFIG[self.server]['tasks'])
        self.converter_class = self.__find_converter()
        self.common_list = list_processes
        logger.debug('Working on {}'.format(self.task.taskid))

    def __find_converter(self):
        for converter in APPCONFIG['converters']:
            if self.task.converter.split('_')[0] in APPCONFIG['converters'][converter]['output_allowed'] and \
                    self.task.extension in APPCONFIG['converters'][converter]['extensions_allowed']:
                logger.debug('converter class for reflection: %s' % globals()[converter])
                return globals()[converter]
        raise DoconverterException(
            "from {} to {} in task {} no converter defined."
            .format(self.task.extension, self.converter_class, self.task.taskid))

    def run(self):
        from doconverter.models.Result_Conversion import Result_ConversionMapper
        Utils.set_server_name(self.server)
        converter = self.converter_class(taskid=self.task.taskid, queue=self.queue)
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
                    debug('task {} in server {}, remote host: {} sucessful: file: {} size: {} '
                          'KB from: {} to: {} size: {} KB in {} secs'
                          .format(self.task.taskid, self.task.server, self.task.remotehost, self.task.uploadedfile,
                                  Utils.getfilesizeinkb(os.path.join(self.task.fullocalpath, self.task.uploadedfile)),
                                  self.task.extension,
                                  self.task.converter,
                                  Utils.getfilesizeinkb(os.path.join(self.task.fullocalpath, self.task.newfilename)),
                                  totalsecs))
                if Result_ConversionMapper.insert_dict(dict(from_ext=self.task.extension, to_ext=self.task.converter,
                                                            taskid=self.task.taskid, remotehost=self.task.remotehost,
                                                            size_from=Utils.getfilesizeinkb(
                                                                os.path.join(self.task.fullocalpath,
                                                                             self.task.uploadedfile)),
                                                            size_to=Utils.getfilesizeinkb(
                                                                os.path.join(self.task.fullocalpath,
                                                                             self.task.newfilename)),
                                                            duration=totalsecs,
                                                            converter=str(self.converter_class))):
                    logger.debug('Results for task {} were logged.'.format(self.task.taskid))
                else:
                    logger.debug('Problem logging task {} into DB'.format(self.task.taskid))

                self.task.sendbyweb(os.path.join(self.task.fullocalpath, self.task.newfilename), status)
            else:
                self.task.movetoerror()
                totalsecs = round(after - before)
                logger\
                    .debug('task {} in server {}, remote host: {} failed: file: {} size: {} '
                           'KB from: {} to: {} size: {} KB in {} secs'
                           .format(self.task.taskid, self.server, self.task.remotehost, self.task.uploadedfile,
                                   Utils.getfilesizeinkb(os.path.join(self.task.fullocalpath, self.task.uploadedfile)),
                                   self.task.extension, self.task.converter, -1, -1))
                if Result_ConversionMapper.insert_dict(dict(from_ext=self.task.extension, to_ext=self.task.converter,
                                                            taskid=self.task.taskid, remotehost=self.task.remotehost,
                                                            size_from=Utils.getfilesizeinkb(
                                                                os.path.join(self.task.fullocalpath,
                                                                             self.task.uploadedfile)),
                                                            size_to=-1,
                                                            duration=totalsecs,
                                                            converter=str(self.converter_class))):
                    logger.debug('Results for task {} were logged.'.format(self.task.taskid))
                else:
                    logger.debug('Problem logging task {} into DB'.format(self.task.taskid))

                self.task.sendbyweb(None, status)
        except DoconverterException as ex:
            logger.debug('DoconverterException {}'.format(ex))
            logger.\
                debug('task {} in server {}, remote host: {} failed: file: {} size: {} '
                      'KB from: {} to: {} size: {} KB in {} secs'
                      .format(self.task.taskid, self.server, self.task.remotehost, self.task.uploadedfile,
                              Utils.getfilesizeinkb(os.path.join(self.task.fullocalpath, self.task.uploadedfile)),
                              self.task.extension, self.task.converter, -1, -1))
            if Result_ConversionMapper.insert_dict(dict(from_ext=self.task.extension, to_ext=self.task.converter,
                                                   taskid=self.task.taskid, remotehost=self.task.remotehost,
                                                   size_from=Utils.getfilesizeinkb(
                                                       os.path.join(self.task.fullocalpath,
                                                                    self.task.uploadedfile)),
                                                   size_to=-1,
                                                   duration=-1,
                                                   converter=str(self.converter_class),
                                                   error=repr(ex))):
                logger.debug('Results for task {} were logged.'.format(self.task.taskid))
            else:
                logger.debug('Problem logging task {} into DB'.format(self.task.taskid))

        except Exception as ex:
            logger.debug('Exception got {}. Stack trace: {} '.format(ex, traceback.print_exc()))
            logger\
                .debug('task {} in server {}, remote host: {} failed: file: {} size: {} '
                       'KB from: {} to: {} size: {} KB in {} secs'
                       .format(self.task.taskid, self.server, self.task.remotehost, self.task.uploadedfile,
                               Utils.getfilesizeinkb(os.path.join(self.task.fullocalpath, self.task.uploadedfile)),
                               self.task.extension, self.task.converter, -1, -1))
            if Result_ConversionMapper.insert_dict(dict(from_ext=self.task.extension, to_ext=self.task.converter,
                                                   taskid=self.task.taskid, remotehost=self.task.remotehost,
                                                   size_from=Utils.getfilesizeinkb(
                                                       os.path.join(self.task.fullocalpath,
                                                                    self.task.uploadedfile)),
                                                   size_to=-1,
                                                   duration=-1,
                                                   converter=str(self.converter_class),
                                                   error=repr(ex))):
                logger.debug('Results for task {} were logged.'.format(self.task.taskid))
            else:
                logger.debug('Problem logging task {} into DB'.format(self.task.taskid))

        finally:
            self.common_list.remove(int(self.task.taskid))
            self.common_list.append(-666)
            if os.path.exists(os.path.join(APPCONFIG[self.task.server]['tasks'], self.task.taskid)):
                self.task.movetoerror()
                logger\
                    .debug('task {} in server {} remote host: {} failed: file: {} size: {} '
                           'KB from: {} to: {} size: {} KB in {} secs'
                           .format(self.task.taskid, self.task.server, self.task.remotehost, self.task.uploadedfile,
                                   Utils.getfilesizeinkb(os.path.join(self.task.fullocalpath, self.task.uploadedfile)),
                                   self.task.extension, self.task.converter, -1, -1))
                self.task.sendbyweb(None, status)
            sys.exit()
