#!c:\Python34\python.exe
# -*- coding: utf-8 -*-

# Copyright (C) 2017, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.

import os
import shutil
import re
from datetime import date
from doconverter.config import APPCONFIG
from doconverter.tools.Utils import Utils


class MonitorConverter:

    logger = None

    def __init__(self, mainscript, counter=2):
        MonitorConverter.logger = Utils.initlogger()
        self.server = Utils.get_server_name()
        self.tasksdir = APPCONFIG[self.server]['tasks']
        self.emailtolist = APPCONFIG['emails']
        self.archival_dir = APPCONFIG[self.server]['archival_dir']
        self.taskalert = APPCONFIG['taskalert']
        self.converters = APPCONFIG['converters']
        self.daemon = mainscript
        self.smtpserver = APPCONFIG['smtpserver']
        self.isupcounter = counter
        MonitorConverter.logger.debug('MonitorConverter initiated')

    def runchecks(self):
        """ It checks:
                -all defined converters and daemon are running
                -tasks bellow a certain threshold

        Sends an email only if a condition is not met.
        :return: None
        """
        # number of pending tasks
        count = 0
        msg = []
        send = False
        msg.append("Monitoring on server: {}".format(Utils.get_server_name()))
        if not os.path.exists(self.tasksdir):
            MonitorConverter.logger.debug('directory {} doesnt exist. Check cant be done.'.format(self.taskalert))
        else:
            files = os.listdir(self.tasksdir)
            for f in files:
                if re.match(r'^\d{1,}$', f, re.M | re.I) and os.path.isfile(os.path.join(self.tasksdir, f)):
                    count = count + 1

        if count > int(self.taskalert):
            msg.append('Tasks pending: {} (please check!)'.format(count))
            send = True
        else:
            msg.append('Tasks pending: {}'.format(count))

        # Check if processes are running
        for p in self.converters:
            if p == 'Neevia':
                if Utils.isprocess_running(self.converters[p]['exe']) >= 1:
                    msg.append('Converter {}:  UP'.format(p))
                else:
                    msg.append('Converter {}:  DOWN (please check!)'.format(p))
                    send = True
        # main
        if Utils.isprocess_running(self.daemon, 'python') >= self.isupcounter:
            msg.append('Daemon:  UP')
        else:
            msg.append('Daemon:  DOWN (please check!)')
            send = True

        if send and self.smtpserver:
            MonitorConverter.logger.debug('Message {} will be sent'.format(msg))
            Utils.sendemail(self.emailtolist, "Some condition needs to be verified", msg, self.smtpserver)
        return msg

    def archive_olderthan(self, days):
        '''

        :param days:
        :return:
        '''
        if not os.path.exists(self.archival_dir):
            MonitorConverter.logger.debug('archival directory {} doesnt exist!'.format(self.archival_dir))
            return
        # Check for the hierarchy structure tasks, success, error, uploadsresults
        now = date.today()
        if not os.path.exists(os.path.join(self.archival_dir, str(now.year))):
            # create directories
            os.makedirs(os.path.join(self.archival_dir, str(now.year), 'tasks'), exist_ok=True)
            os.makedirs(os.path.join(self.archival_dir, str(now.year), 'success'), exist_ok=True)
            os.makedirs(os.path.join(self.archival_dir, str(now.year), 'error'), exist_ok=True)
            os.makedirs(os.path.join(self.archival_dir, str(now.year), 'uploadsresults'), exist_ok=True)

        (parent, child) = os.path.split(self.tasksdir)
        for folder in ['success', 'uploadsresults', 'error']:
            if folder == 'uploadsresults':
                for dir in os.listdir(os.path.join(parent, folder)):
                    for file in os.listdir(os.path.join(parent, folder, dir)):
                        file_date = date.fromtimestamp(os.path.getmtime(os.path.join(parent, folder, dir, file)))
                        print(os.path.join(parent, folder, dir, file))
                        print(file_date)
                        if (now - file_date).days >= days:
                            try:
                                yeartobemovedto = None
                                if file_date.year == now.year:
                                    yeartobemovedto = now.year
                                else:
                                    yeartobemovedto = now.year - 1

                                shutil.copytree(os.path.join(parent, folder, dir),
                                                os.path.join(self.archival_dir,
                                                             str(yeartobemovedto), folder, dir), False)
                                shutil.rmtree(os.path.join(parent, folder, dir))
                            except Exception as ex:
                                MonitorConverter.logger.debug(
                                    'got an exception <{}> while working from {} to {}'.format(
                                        ex,
                                        os.path.join(parent, folder, dir),
                                        os.path.join(self.archival_dir, str(now.year), folder, dir)
                                    ))
                            break
            else:
                for file in os.listdir(os.path.join(parent, folder)):
                    file_date = date.fromtimestamp(os.path.getmtime(os.path.join(parent, folder, file)))
                    print(os.path.join(parent, folder, file))
                    print(file_date)
                    if (now - file_date).days >= days:
                        try:
                            yeartobemovedto = None
                            if file_date.year == now.year:
                                yeartobemovedto = now.year
                            else:
                                yeartobemovedto = now.year - 1
                            shutil.move(os.path.join(parent, folder, file),
                                        os.path.join(self.archival_dir, str(yeartobemovedto), folder, file))
                        except Exception as ex:
                            MonitorConverter.logger.debug('got an exceptionB <{}> while working from {} to {}'.format(
                                ex,
                                os.path.join(parent, folder, file),
                                os.path.join(self.archival_dir, str(now.year), folder, file)
                            ))
