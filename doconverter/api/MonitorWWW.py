# -*- coding: utf-8 -*-

# Copyright (C) 2016, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.

import logging
from flask_restful import Resource
from doconverter.tools.MonitorConverter import MonitorConverter


class MonitorWWW(Resource):
    logger = None

    def __init__(self):
        ''' Method definition '''
        MonitorWWW.logger = logging.getLogger('doconverter-api')

    def get(self):
        MonitorWWW.logger.debug("get begin")

        mon = MonitorConverter('converter_daemon.py', counter=1)
        msg = mon.runchecks()
        return {'get': msg}, 200
