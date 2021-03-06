#!c:\Python34\python.exe
# -*- coding: utf-8 -*-

# Copyright (C) 2017, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.

import logging
import os
from flask import request
from flask_restful import Resource, reqparse
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from doconverter.config import APPCONFIG
from doconverter.tools.Utils import Utils
from doconverter.tools.Task import Task


class UploadFile(Resource):
    logger = None

    def __init__(self):
        ''' Method definition '''
        UploadFile.logger = logging.getLogger('doconverter-api')
        self.reqparse_post = reqparse.RequestParser(bundle_errors=True)
        self.reqparse_post.add_argument('uploadedfile', type=FileStorage, location='files')
        self.reqparse_post.add_argument('converter', type=str, location='form', required=True)
        self.reqparse_post.add_argument('urlresponse', type=str, location='form', required=True)
        self.reqparse_post.add_argument('dirresponse', type=str, location='form', required=True)
        self.reqparse_post.add_argument('options', type=str, location='form', required=False)

    def post(self):
        UploadFile.logger.debug("post begin")
        args = self.reqparse_post.parse_args()
        UploadFile.logger.debug("post begin2")
        if 'uploadedfile' not in request.files:
            return {'post': 'no file sent!'}, 400
        UploadFile.logger.debug("post begin3")
        file = request.files['uploadedfile']
        UploadFile.logger.debug("post begin4")
        # if user does not select file, browser also
        # submit a empty part without filename
        UploadFile.logger.debug("post begin5")
        if file.filename == '':
            return {'post': 'file is empty!'}, 400
        UploadFile.logger.debug('filename is %s', file.filename)
        extension = file.filename.split('.')[-1]
        if file and Utils.allowed_filextension(extension, APPCONFIG['extensions_all']):
            filename = secure_filename(file.filename)
            task = Task(converter=args["converter"], urlresponse=args["urlresponse"], diresponse=args["dirresponse"],
                        uploadedfile=filename, options=args['options'], remotehost=request.remote_addr)
            pathdir = task.fullocalpath
            file.save(os.path.join(pathdir, filename))

            from doconverter.models.Taskdb import TaskMapper
            if TaskMapper.insert_from_taskfile(task):
                UploadFile.logger.debug('Task {} inserted in db'.format(task.taskid))
        else:
            UploadFile.logger.debug('<{}> is not permitted'.format(extension))
            return {'post': 'Extension is not permitted!'}, 400
        return {'post': 'ok-[{}]'.format(task.taskid)}, 200
