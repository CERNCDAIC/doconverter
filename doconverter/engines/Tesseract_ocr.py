#!c:\Python34\python.exe
# -*- coding: utf-8 -*-

# Copyright (C) 2017, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.


import os
from doconverter.tools.Utils import Utils
from doconverter.config import APPCONFIG
from doconverter.DoconverterException import DoconverterException
from doconverter.engines.Baseconverters import Baseconverters


class Tesseract_ocr(Baseconverters):

    def __init__(self, taskid, queue=None):
        Baseconverters.__init__(self, taskid=taskid, queue=queue)

    @classmethod
    def get_classname(cls):
        return cls.__name__

    def convert(self):
        Baseconverters.logger.debug('{} conversion started'.format(self.task.taskid))
        if not os.path.isfile(os.path.join(self.task.fullocalpath, self.task.uploadedfile)):
            raise DoconverterException('{} file is missing {}'.format(self.task.taskid,
                                                                      os.path.join(self.task.fullocalpath,
                                                                                   self.task.uploadedfile)))

        cmd = []

        # EOS advertising the file but being not ready for working with it
        self.isfileready()

        # exe application
        cmd.append(APPCONFIG['converters']['Tesseract_ocr']['exe'])
        if not os.path.exists(APPCONFIG['converters']['Tesseract_ocr']['exe']):
            raise DoconverterException('{} file is missing {}'
                                       .format(self.task.taskid,
                                               os.path.exists(
                                                   APPCONFIG['converters']['Tesseract_ocr']['exe'])))

        # arguments
        cmd.append(os.path.join(self.task.fullocalpath, self.task.uploadedfile))
        cmd.append(os.path.join(self.task.fullocalpath, self.task.newfilename.replace('.pdf', '')))
        cmd.append('pdf')
   
        result, outlines = Utils.syscom(cmd, shell=True)

        return result
