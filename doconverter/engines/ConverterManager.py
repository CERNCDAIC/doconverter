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
import hashlib
from doconverter.tools.Task import Task
from doconverter.config import APPCONFIG
from doconverter.DoconverterException import DoconverterException
from doconverter.tools.Utils import Utils
from doconverter.engines.Neevia import Neevia  # noqa
from doconverter.engines.Hpglview_raster import Hpglview_raster  # noqa
from doconverter.engines.Tesseract_ocr import Tesseract_ocr  # noqa


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
        logger.debug('Working on taskid {} from remote_host: {} ext_from: {} ext_to: {}'.format(self.task.taskid,
                                                                                                self.task.remotehost,
                                                                                                self.task.extension,
                                                                                                self.task.converter))

    def __find_converter(self):
        for converter in APPCONFIG['converters']:
            if self.task.converter.split('_')[0] in APPCONFIG['converters'][converter]['output_allowed'] and \
                    self.task.extension.lower() in APPCONFIG['converters'][converter]['extensions_allowed']:
                logger.debug('converter class for reflection: %s' % globals()[converter])
                return globals()[converter]
        logger.debug("{} from {} to {} no converter defined.".format(self.task.taskid, self.task.extension, self.task.converter))
        return None

    def run(self):
        from doconverter.models.Result_Conversion import Result_ConversionMapper
        Utils.set_server_name(self.server)
        logger = Utils.initlogger(self.queue)
        uploadedfilehash = hashlib.md5(self.task.uploadedfile.encode()).hexdigest()
        status = -1
        before = None
        after = None
        try:
            if not self.converter_class:
                raise DoconverterException("{} from {} using converter {} no converter defined."
                                           .format(self.task.taskid, self.task.extension, self.task.converter))
            converter = self.converter_class(taskid=self.task.taskid, queue=self.queue)
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
                                                            uploadedfilehash=uploadedfilehash,
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
                                                            uploadedfilehash=uploadedfilehash,
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
                                                   uploadedfilehash=uploadedfilehash,
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
                                                   uploadedfilehash=uploadedfilehash,
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
