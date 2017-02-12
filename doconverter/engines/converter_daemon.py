#!c:\Python34\python.exe
# -*- coding: utf-8 -*-

# Copyright (C) 2017, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.

import logging
import time
import sys
import os
import multiprocessing
from logging.handlers import QueueListener
import argparse
from doconverter.config import APPCONFIG
from doconverter.tools.Utils import Utils
from doconverter.tools.Task import Task
from doconverter.engines.ConverterManager import ConverterManager
from doconverter.tools.MonitorConverter import MonitorConverter


logger = None

def logger_init():
    q = multiprocessing.Queue()
    # this is the handler for all log records
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s %(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"))

    queue_listener = QueueListener(q, handler)
    queue_listener.start()
    global logger
    logger = logging.getLogger('doconverter-api')

    logger.addHandler(handler)
    return queue_listener, q


if __name__ == '__main__':
    q_listener, q = logger_init()

    parser = argparse.ArgumentParser(description='Processing of tasks')
    parser.add_argument('--n', action='store', type=int, dest='nprocesses', required=False, default=2,
                        help='number of documents to treat in parallel')
    parser.add_argument('--t', action='store', type=int, dest='timetosleep', required=False, default=2,
                        help='time to wait for new tasks in secs')
    parser.add_argument('--send', action='store', type=str, dest='sendtaskid', required=False, default=0,
                        help='Get the task information and try to send it, it is supposed it was properly converted')
    parser.add_argument('--s', action='store_true', dest='stopper', required=False,
                        help='creates a flag in the local file system for clean stop')
    parser.add_argument('--r', action='store_true', dest='remove_stopper', required=False,
                        help='deletes flag for clean shutdown in the local file system, if present')
    parser.add_argument('--m', action='store_true', dest='basic_monitoring', required=False,
                        help='Performs basic monitoring checks')
    parser.add_argument('--a', action='store', type=int, dest='archive', required=False, default=0,
                        help='items older than this number of days will be moved to archive')
    parser.add_argument('--c', action='store', type=str, dest='computer', required=False,
                        help='queue to work tasks from. Usually same as the server were the program runs.')

    results = parser.parse_args()
    print(parser.parse_args())
    if results.stopper and APPCONFIG['stopper']:
        logger.debug('Creates stopper file and exists!')
        open(APPCONFIG['stopper'], "w+").close()
        sys.exit(0)
    elif results.stopper and not APPCONFIG['stopper']:
        logger.debug('stopper location not defined on doconverter.ini')
        sys.exit(-1)

    if results.remove_stopper:
        if os.path.exists(APPCONFIG['stopper']):
            logger.debug('remove stopper from file system and exists!')
            os.remove(APPCONFIG['stopper'])
        else:
            logger.debug('stopper flag not present, exiting!')
        sys.exit(0)

    if results.basic_monitoring:
        mon = MonitorConverter(os.path.basename(sys.argv[0]))
        mon.runchecks()
        sys.exit(0)

    if results.archive:
        mon = MonitorConverter(os.path.basename(sys.argv[0]))
        mon.archive_olderthan(results.archive)
        sys.exit(0)

    if results.sendtaskid:
        logger.debug('retrieving task: {}'.format(results.sendtaskid))
        task = Task.getaskbyid(results.sendtaskid, dir=APPCONFIG['success'])
        if task and task.convertedfile_exists():
            logger.debug('sending task: {}'.format(results.sendtaskid))
            task.sendbyweb(task.convertedfile_exists(), 0)
        sys.exit(0)


    if not results.computer:
        server = Utils.get_server_name()
    else:
        Utils.set_server_name(results.computer)
        server = Utils.get_server_name()

    # check if we are alone
    if Utils.isprocess_running(os.path.basename(sys.argv[0]), os.path.basename(sys.executable).split('.')[0]) > 1:
        logger.debug('A converter is already running!')
        print(os.path.basename(sys.argv[0]))
        sys.exit(0)

    nprocesses = results.nprocesses
    timetosleep = results.timetosleep

    counter = 0
    processes = []
    mgr = multiprocessing.Manager()
    list_processes = mgr.list([-666 for _ in range(nprocesses)])

    logger.debug('number of processes %s', len(list_processes))
    while not os.path.exists(APPCONFIG['stopper']):
        tasks = Utils.sortfilesbytime(APPCONFIG[server]['tasks'])
        logger.debug('list of tasks %s', tasks)
        logger.debug('number of jobs %s', len(processes))

        if not tasks:
            time.sleep(timetosleep)
            continue

        for task in tasks:
            if -666 in list_processes:
                for item in list_processes:
                    if str(item) == task:
                        time.sleep(timetosleep)
                        break
                else:
                    if len(processes) <= len(list_processes):
                        logger.debug('processing task: %s', task)
                        list_processes.remove(-666)
                        list_processes.append(int(task))
            else:
                break
        logger.debug('list of processes %s', list_processes)
        for task in list_processes:
            if task == -666:
                continue
            logger.debug('task being added %s', list_processes)
            job = ConverterManager(str(task), list_processes, q)
            job.name = str(task)
            job.daemon = False
            processes.append(job)

        for job in processes:
            logger.debug('JOB START %s' % job.name)
            job.start()
        for job in processes:
            logger.debug('JOB JOIN %s' % job.name)
            job.join()
        processes.clear()
        time.sleep(timetosleep)
    else:
        logger.debug('stopper flag in place!')
        q_listener.stop()
