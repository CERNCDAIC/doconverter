#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2017, CERN
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
from doconverter.api.Stats import Stats
from flask_sqlalchemy import SQLAlchemy
from doconverter.config import APPCONFIG


app = Flask(__name__)
app.debug = True
# limit the maximum size of files to be upload to 400 MB
app.config['MAX_CONTENT_LENGTH'] = 2000 * 1024 * 1024

api = Api(app)


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = APPCONFIG['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_POOL_SIZE'] = 20
app.config['SQLALCHEMY_POOL_RECYCLE'] = 1
db = SQLAlchemy(app)

@app.route('/')
def index():
    return "Hello, World!"


api.add_resource(UploadFile, '/doconverter/api/v1.0/uploads')
api.add_resource(MonitorWWW, '/doconverter/api/v1.0/monitor')
api.add_resource(ReceivedFile, '/doconverter/api/v1.0/received')
api.add_resource(Stats, '/doconverter/api/v1.0/stats/<int:report>')
if __name__ == '__main__':
 

    app.run(host='0.0.0.0', port=8080)
    # app.run(debug=True)
