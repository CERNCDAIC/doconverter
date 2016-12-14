#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2016, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.

from flask import Flask
from flask_restful import Api
from doconverter.api.UploadFile import UploadFile
from doconverter.api.ReceivedFile import ReceivedFile
from doconverter.api.MonitorWWW import MonitorWWW
from flask_sqlalchemy import SQLAlchemy
#from doconverter.models import Result
#from doconverter.models import Task

app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://doconverter:toto@conv-test02.cern.ch:5432/doconverter'
# limit the maximum size of files to be upload to 16 MB
app.config['MAX_CONTENT_LENGTH'] = 400 * 1024 * 1024

db = SQLAlchemy(app)
api = Api(app)

#db.drop_all()
#db.create_all()

@app.route('/')
def index():
    return "Hello, World!"


@app.route('/doconverter/api/v1.0/toto2', methods=['GET'])
def get_task(task_id):
    return {'task': 333}


api.add_resource(UploadFile, '/doconverter/api/v1.0/uploads')
api.add_resource(MonitorWWW, '/doconverter/api/v1.0/monitor')
api.add_resource(ReceivedFile, '/doconverter/api/v1.0/received')
if __name__ == '__main__':
    app.run()
