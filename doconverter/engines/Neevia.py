#!c:\Python34\python.exe
# -*- coding: utf-8 -*-

# Copyright (C) 2017, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.


import win32com.client
import os
import time
import random
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
        self.error_dir = os.path.join(APPCONFIG[self.task.server]['error'], self.task.taskid)
        self.success_dir = os.path.join(APPCONFIG[self.task.server]['uploadsresults'], self.task.taskid)

    @classmethod
    def get_classname(cls):
        return cls.__name__

    def __create_dirs_for_task(self):
        if not os.path.exists(self.success_dir):
            os.makedirs(self.success_dir, exist_ok=True)
            logger.debug('%s directory created: %s', self.task.taskid, self.success_dir)
        if not os.path.exists(os.path.join(APPCONFIG[self.task.server]['error'], self.task.taskid)):
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
        if error is not None:
            logger.debug('{} submitting file issue1 <{}>'.format(self.task.taskid, error))
        return retval

    def convert(self):
        logger.debug('{} convertion started'.format(self.task.taskid))
        if not os.path.isfile(os.path.join(self.task.fullocalpath, self.task.uploadedfile)):
            raise DoconverterException('{} file is missing {}'.format(self.task.taskid,
                                                                      os.path.join(self.task.fullocalpath,
                                                                                   self.task.uploadedfile)))
        NDocConverter = win32com.client.Dispatch("Neevia.docConverter")
        if self.task.converter.upper() == 'PS':
            logger.debug('{} conversion from: {} towards {}'.format(self.task.taskid, self.task.extension,
                                                                    'PS'))
            NDocConverter.setParameter("DocumentOutputFormat", "POSTSCRIPT")
        elif self.task.converter.upper() == 'PDFA':
            logger.debug('{} conversion from: {} towards {}'.format(self.task.taskid, self.task.extension,
                                                                    'PDF/A'))
            NDocConverter.setParameter("DocumentOutputFormat", "PDF/A")
        elif self.task.converter.upper().startswith('THUMB'):
            logger.debug('{} conversion from: {} towards {}'.format(self.task.taskid, self.task.extension,
                                                                    'PNG'))
            NDocConverter.setParameter("DocumentOutputFormat", "PNG")
            (imgresh, imgresv, imgheight, imgwidth)= Utils.getthumbnailsettings(self.task.converter)
            NDocConverter.setParameter('ImgHeight', imgheight)
            NDocConverter.setParameter('ImgWidth', imgwidth)
            NDocConverter.setParameter('ImgResH', imgresh)
            NDocConverter.setParameter('ImgResV',imgresv)
        else:
            NDocConverter.setParameter("DocumentOutputFormat", self.task.converter.upper())
            logger.debug('{} conversion from: {} towards {}'.format(self.task.taskid, self.task.extension,
                                                                    'PDF'))
        NDocConverter.setParameter("DocumentOutputFolder", self.success_dir)
        NDocConverter.setParameter("JobOption", "printer")

        # sleep randomly to reduce likelihood of -3 Invalid input folder error
        size_file = os.stat(os.path.join(self.task.fullocalpath, self.task.uploadedfile)).st_size
        while True:
            time.sleep(1)
            if os.stat(os.path.join(self.task.fullocalpath, self.task.uploadedfile)).st_size > size_file:
                size_file = os.stat(os.path.join(self.task.fullocalpath, self.task.uploadedfile)).st_size
                time.sleep(random.randint(0, 15))
                logger.debug('file: {} still being copied size is {} bytes'.format(
                    os.path.join(self.task.fullocalpath, self.task.uploadedfile),
                    size_file))
            elif os.stat(os.path.join(self.task.fullocalpath, self.task.uploadedfile)).st_size == size_file:
                logger.debug('file: {} got stationary size: {} bytes'.format(
                    os.path.join(self.task.fullocalpath, self.task.uploadedfile),
                    size_file))
                break
            else:
                logger.debug('file: {} must have been fully copied, leaving loop'.format(
                    os.path.join(self.task.fullocalpath, self.task.uploadedfile)))

        self.__submit_return_check(NDocConverter.SubmitFile(os.path.join(self.task.fullocalpath,
                                                                         self.task.uploadedfile), ''))

        logger.debug('{} file submitted: {} '.format(self.task.taskid, self.task.uploadedfile))
        status = None
        while True:
            try:
                status = self.__checkstatusretval(NDocConverter.CheckStatus(os.path.join(
                                                                                        self.task.fullocalpath,
                                                                                        self.task.uploadedfile), ''))
                if status == 2:
                    NDocConverter.doSleep(1000)
                    continue
            except DoconverterException:
                for x in range(0, 30):
                    if os.path.isfile(os.path.join(self.task.fullocalpath, self.task.newfilename)):
                        return 0
                    time.sleep(1)
                raise
            except:
                for x in range(0, 30):
                    if os.path.isfile(os.path.join(self.task.fullocalpath, self.task.newfilename)):
                        return 0
                    time.sleep(1)
                raise
            else:
                for x in range(0, 60):
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
