# -*- coding: utf-8 -*-

# Copyright (C) 2017, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.

import logging
import os
import base64
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
        ReceivedFile.logger.debug('status is {}'.format(args['status']))
        if args['status'] == 1:
            try:
                if not (args.directory or os.path.exists(args['directory'])):
                    return {'post': 'not valid directory provided!'}, 400
                filename = secure_filename(args.filename)
                ReceivedFile.logger.debug('filename secured: {}'.format(filename))
                if request.form['content']:
                    data = base64.b64decode(request.form['content'])
                    with open(os.path.join(args.directory, filename), 'wb') as fd:
                        fd.write(data)
                elif 'content' in request.files:
                    file = request.files['content']
                    ReceivedFile.logger.debug("post begin3")
                    if file.filename == '':
                        return {'post': 'file is empty!'}, 400
                    file.save(os.path.join(args.directory, filename))
                else:
                    ReceivedFile.logger.debug('No file {} contents!'.format(filename))
                    return {'post': 'file was missing'}, 400
                ReceivedFile.logger.debug('file has been saved: {}'.format(os.path.join(args.directory, filename)))
                return {'post': 'file was uploaded'}, 200
            except:
                import traceback
                ReceivedFile.logger.debug('Exception got while receiving file {}'.format(traceback.print_exc()))
                return {'post': 'Internal Error'}, 500
        else:
            ReceivedFile.logger.debug('{} was not succesfully converted.'.format(args['filename']))
            return {'post': 'info received'}, 200
