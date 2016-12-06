# -*- coding: utf-8 -*-

# Copyright (C) 2016, CERN
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


class ReceivedFile(Resource):
    logger = None

    def __init__(self):
        ''' Method definition '''
        ReceivedFile.logger = logging.getLogger('doconverter-web')
        self.reqparse_post = reqparse.RequestParser(bundle_errors=True)
        self.reqparse_post.add_argument('content', type=FileStorage, location='files', required=False)
        self.reqparse_post.add_argument('error_message', type=str, location='form', required=False)
        self.reqparse_post.add_argument('status', type=int, location='form', required=True)
        self.reqparse_post.add_argument('directory', type=str, location='form', required=True)
        self.reqparse_post.add_argument('filename', type=str, location='form', required=True)

    def post(self):
        ReceivedFile.logger.debug("post begin")
        args = self.reqparse_post.parse_args()
        if args['status'] == 0:
            if 'content' not in request.files:
                return {'post': 'no file sent!'}, 400
            ReceivedFile.logger.debug("post begin2")
            file = request.files['content']
            ReceivedFile.logger.debug("post begin3")
            if file.filename == '':
                return {'post': 'file is empty!'}, 400
            ReceivedFile.logger.debug('filename is %s', file.filename)
            filename = secure_filename(file.filename)
            ReceivedFile.logger.debug("post begin4")
            if args.directory and os.path.exists(args['directory']):
                ReceivedFile.logger.debug("post begin5")
                file.save(os.path.join(args.directory, filename))
                ReceivedFile.logger.debug("post begin6")
            else:
                return {'post': 'no directory provided!'}, 400
            return {'post': 'file was uploaded'}, 200
        else:
            ReceivedFile.logger.debug('{} was not succesfully converted.'.format(args['filename']))
            return {'post': 'info received'}, 200
