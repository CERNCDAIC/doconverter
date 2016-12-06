#!c:\Python34\python.exe
# -*- coding: utf-8 -*-

# Copyright (C) 2016, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.


import win32com.client
import os
import time
from doconverter.tools.Task import Task
from doconverter.tools.Utils import Utils
from doconverter.config import APPCONFIG
from doconverter.DoconverterException import DoconverterException


class Neevia(object):
    logger = None

    def __init__(self, taskid, queue=None):
        global logger
        logger = Utils.initlogger(queue)
        self.task = Task.getaskbyid(taskid, queue)
        self.error_dir = os.path.join(APPCONFIG['error'], self.task.taskid)
        self.success_dir = os.path.join(APPCONFIG['uploadsresults'], self.task.taskid)

    def __create_dirs_for_task(self):
        if not os.path.exists(self.success_dir):
            os.makedirs(self.success_dir, exist_ok=True)
            logger.debug('%s directory created: %s', self.task.taskid, self.success_dir)
        if not os.path.exists(os.path.join(APPCONFIG['error'], self.task.taskid)):
            os.makedirs(self.error_dir, exist_ok=True)
            logger.debug('%s directory created: %s', self.task.taskid, self.error_dir)

    def __submit_return_check(self, retval):
        retvals = {
            # '0 Successfully submitted'
            0: None,
            # Internal error
            -1: '-1 Error submitting document',
            -2: '-2 Invalid input file',
            -3: '-3 Invalid input folder',
            -4: '-4 A file with the same name already exists in the Input folder',
            -5: '-5 Unable to copy document into the input folder',
            -6: '-6 Unable to copy the job file into the output folder',
            -7: '-7 Invalid parameter',
        }
        error = retvals.get(retval, '%s Undocumented Return Value')
        if error is not None:
            raise DoconverterException('{} submitting file issue {}'.format(self.task.taskid, error))
        return retval

    def __checkstatusretval(self, retval):
        retvals = {
            # '0 Converted successfully'
            0: None,
            1: '1 Was not converted -> error',
            # '2 Still Converting'
            2: None,
            3: 'Unable to determine the conversion status.',
            -1: '-1 Internal error',
            -3: '-3 Invalid input folder',
            -5: '-5 Invalid input file',
            -8: '-8 OutputFolder=InputFolder (output folder cannot be the same as input folder)'
            }
        error = retvals.get(retval, '%s Undocumented Return Value')
        return error

    def convert(self):
        logger.debug('{} convertion started'.format(self.task.taskid))
        if not os.path.isfile(os.path.join(self.task.fullocalpath, self.task.uploadedfile)):
            raise DoconverterException('{} file is missing {}'.format(self.task.taskid,
                                                                      os.path.join(self.task.fullocalpath,
                                                                                   self.task.uploadedfile)))
        NDocConverter = win32com.client.Dispatch("Neevia.docConverter")
        if self.task.converter.upper() == 'PS':
            print('PS CONVERSIONG')
            NDocConverter.setParameter("DocumentOutputFormat", "POSTSCRIPT")
        elif self.task.converter.upper() == 'PDFA':
            print('PDFAAAAA CONVERSION')
            NDocConverter.setParameter("DocumentOutputFormat", "PDF/A")
        else:
            NDocConverter.setParameter("DocumentOutputFormat", self.task.converter.upper())
        NDocConverter.setParameter("DocumentOutputFolder", self.success_dir)
        NDocConverter.setParameter("JobOption", "printer")

        self.__submit_return_check(NDocConverter.SubmitFile(os.path.join(self.task.fullocalpath,
                                                                         self.task.uploadedfile), ''))

        logger.debug('{} file submitted: {} '.format(self.task.taskid, self.task.uploadedfile))
        status = None
        while 1:
            status = self.__checkstatusretval(NDocConverter.CheckStatus(os.path.join(
                                                                                    self.task.fullocalpath,
                                                                                    self.task.uploadedfile), ''))

            if status == 2:
                NDocConverter.doSleep(1000)
            else:
                break

        # legacy code, just wait in case dfs takes a while to show file
        for x in range(0, 10):
            if os.path.isfile(os.path.join(self.task.fullocalpath, self.task.newfilename)):
                return 0
            time.sleep(1)
        if not os.path.isfile(os.path.join(self.task.fullocalpath, self.task.newfilename)):
            raise DoconverterException('{} converted file {} missing. Error code from Neevia: {}'.format(
                                                                            self.task.taskid,
                                                                            os.path.join(
                                                                                  self.task.fullocalpath,
                                                                                  self.task.newfilename), status))

        return status
