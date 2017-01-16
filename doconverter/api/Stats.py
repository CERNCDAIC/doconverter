# -*- coding: utf-8 -*-

# Copyright (C) 2017, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.

import logging
from flask_restful import Resource


class Stats(Resource):
    logger = None

    def __init__(self):
        ''' Method definition '''
        Stats.logger = logging.getLogger('doconverter-web')

    def get(self, report=0):
        Stats.logger.debug('Stats get: begin')
        from doconverter.models.Taskdb import TaskMapper
        from doconverter.models.Result_Conversion import Result_ConversionMapper
        days = 2
        if not report:
            tasks = TaskMapper.fetchall_by_serverandextension(datesince=days)
            return {'report 0': 'Documents submitted in the last {} days group by type of conversion'.format(days),
                    'result': tasks}, 200
        elif report == 1:
            tasks = TaskMapper.fetchall_by_server(datesince=days)
            return {'report 1': 'Documents submitted in the last {} days group by queue and converter'.format(days),
                    'result': tasks}, 200
        elif report == 2:
            tasks = Result_ConversionMapper.fetch_top1(datesince=days)
            return {'report 2': 'Some top tasks for the last {} days'.format(days),
                    'result': tasks}, 200
        elif report == 3:
            tasks = Result_ConversionMapper.fetch_balance(datesince=days)
            message_info = 'Total tasks: {}, Error: {} Success: {}'.format(tasks[0][1], tasks[0][0],
                                                                           tasks[0][1] - tasks[0][0])
            return {'report 3': 'Total tasks dealt in the last {} days'.format(days),
                    'result': message_info}, 200
