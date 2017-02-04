#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2017, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.

from doconverter.api.handlers import app
from flask_sqlalchemy import SQLAlchemy
from doconverter.config import APPCONFIG

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = APPCONFIG['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_POOL_SIZE'] = 10
db = SQLAlchemy(app)
