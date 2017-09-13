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
from doconverter.engines.Baseconverters import Baseconverters
from doconverter.tools.Utils import Utils
from doconverter.DoconverterException import DoconverterException


class Neevia(Baseconverters):

    def __init__(self, taskid, queue=None):
        Baseconverters.__init__(self, taskid=taskid, queue=queue)

    @classmethod
    def get_classname(cls):
        return cls.__name__

    # def __create_dirs_for_task(self):
    #    if not os.path.exists(self.success_dir):
    #        os.makedirs(self.success_dir, exist_ok=True)
    #        logger.debug('%s directory created: %s', self.task.taskid, self.success_dir)
    #    if not os.path.exists(os.path.join(APPCONFIG[self.task.server]['error'], self.task.taskid)):
    #        os.makedirs(self.error_dir, exist_ok=True)
    #        logger.debug('%s directory created: %s', self.task.taskid, self.error_dir)

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
            Baseconverters.logger.debug('{} submitting file issue1 <{}>'.format(self.task.taskid, error))
        return retval

    def convert(self):
        Baseconverters.logger.debug('{} conversion started'.format(self.task.taskid))
        if not os.path.isfile(os.path.join(self.task.fullocalpath, self.task.uploadedfile)):
            raise DoconverterException('{} file is missing {}'.format(self.task.taskid,
                                                                      os.path.join(self.task.fullocalpath,
                                                                                   self.task.uploadedfile)))
        NDocConverter = win32com.client.Dispatch("Neevia.docConverter")
        # TOPNG will provide a zip file
        expected_file = self.task.newfilename
        imgconversion = 'PNG'

        if self.task.converter.upper() == 'PS':
            Baseconverters.logger.debug('{} conversion from: {} towards {}'
                                        .format(self.task.taskid, self.task.extension, 'PS'))
            NDocConverter.setParameter("DocumentOutputFormat", "POSTSCRIPT")
        elif self.task.converter.upper() == 'PDFA':
            Baseconverters.logger.debug('{} conversion from: {} towards {}'
                                        .format(self.task.taskid, self.task.extension, 'PDF/A'))
            NDocConverter.setParameter("DocumentOutputFormat", "PDF/A")
        elif self.task.converter.upper().startswith('THUMB'):
            Baseconverters.logger.debug('{} conversion from: {} towards {}'
                                        .format(self.task.taskid, self.task.extension, 'PNG'))
            NDocConverter.setParameter("DocumentOutputFormat", "PNG")
            (imgresh, imgresv, imgheight, imgwidth) = Utils.getresolutionsettings('thumb', self.task.options)
            NDocConverter.setParameter('ImgHeight', imgheight)
            NDocConverter.setParameter('ImgWidth', imgwidth)
            NDocConverter.setParameter('ImgResH', imgresh)
            NDocConverter.setParameter('ImgResV', imgresv)
        elif self.task.converter.upper().startswith('TOIMG'):
            if 'typeofimg' in self.hash_options.keys():
                imgconversion = self.hash_options['typeofimg'].upper()
            if imgconversion not in ['JPEG', 'BMP', 'TIFF', 'PNG']:
                raise DoconverterException('This image format {} is not allowed'.format('imgconversion'))
                Baseconverters.logger.debug('{} conversion from: {} towards {}'
                                            .format(self.task.taskid, self.task.extension, imgconversion))
            NDocConverter.setParameter("DocumentOutputFormat", imgconversion)
            (imgresh, imgresv, imgheight, imgwidth) = Utils.getresolutionsettings('toimg', self.task.options)
            NDocConverter.setParameter('ImgHeight', imgheight)
            NDocConverter.setParameter('ImgWidth', imgwidth)
            if imgresh != 0 and imgresv != 0:
                NDocConverter.setParameter('ImgResH', imgresh)
                NDocConverter.setParameter('ImgResV', imgresv)
            # At least it should be one png file
            imgconversion_ext = imgconversion.lower()
            if imgconversion == 'JPEG':
                imgconversion_ext = 'jpg'
            if imgconversion != 'TIFF':
                expected_file = '{}1.{}'.format(self.task.uploadedfile.split('.')[0], imgconversion_ext)
        else:
            NDocConverter.setParameter("DocumentOutputFormat", self.task.converter.upper())
            Baseconverters.logger.debug('{} conversion from: {} towards {}'
                                        .format(self.task.taskid, self.task.extension, 'PDF'))
        Baseconverters.logger.debug('{} expected file name is {}'
                                    .format(self.task.taskid, os.path.join(self.task.fullocalpath, expected_file)))
        # set special options
        if 'hidedocumentrevisions' in self.task.options.lower() and self.task.extension in ['doc', 'docx'] \
                and self.task.converter.upper() in ['PDF', 'PDFA']:
            NDocConverter.setParserParameter('WORD', 'HideDocumentRevisions',
                                             self.hash_options['hidedocumentrevisions'])
            Baseconverters.logger.debug('HideDocumentRevisions set to {}'
                                        .format(self.hash_options['hidedocumentrevisions']))

        NDocConverter.setParameter("DocumentOutputFolder", self.success_dir)
        NDocConverter.setParameter("JobOption", "printer")

        # EOS advertising the file but being not ready for working with it
        self.isfileready()

        self.__submit_return_check(NDocConverter.SubmitFile(os.path.join(self.task.fullocalpath,
                                                                         self.task.uploadedfile), ''))

        Baseconverters.logger.debug('{} file submitted: {} '.format(self.task.taskid, self.task.uploadedfile))
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
                    if os.path.isfile(os.path.join(self.task.fullocalpath, expected_file)):
                        if '.zip' in self.task.newfilename:
                            Utils.createzipfile(self.task.fullocalpath, '*.{}', os.path.join(self.task.fullocalpath,
                                                                                             self.task.newfilename))
                        return 0
                    time.sleep(1)
                raise
            except:
                for x in range(0, 30):
                    if os.path.isfile(os.path.join(self.task.fullocalpath, expected_file)):
                        if '.zip' in self.task.newfilename:
                            Utils.createzipfile(self.task.fullocalpath, '*.{}'.format(imgconversion.lower()),
                                                os.path.join(self.task.fullocalpath, self.task.newfilename))
                        return 0
                    time.sleep(1)
                raise
            else:
                for x in range(0, 60):
                    if os.path.isfile(os.path.join(self.task.fullocalpath, expected_file)):
                        if '.zip' in self.task.newfilename:
                            Utils.createzipfile(self.task.fullocalpath, '*.{}'.format(imgconversion.lower()),
                                                os.path.join(self.task.fullocalpath, self.task.newfilename))
                        return 0
                    time.sleep(1)
                raise DoconverterException('{} converted file {} missing. Error code from Neevia: {}'.format(
                    self.task.taskid,
                    os.path.join(
                        self.task.fullocalpath,
                        expected_file), status))
