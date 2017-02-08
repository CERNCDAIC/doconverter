#!c:\Python34\python.exe
# -*- coding: utf-8 -*-

# Copyright (C) 2017, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.

import logging
import logging.config
import configparser
import sys
import traceback
import json
import os
import platform
from doconverter.DoconverterException import DoconverterException


CONFIG = None
APPCONFIG = {}

FILELOGS = None
if os.name == 'posix':
    FILELOGS = '/etc/doconverter/logging.conf'
    FILEINI = '/etc/doconverter/doconverter.ini'
else:
    FILELOGS = 'c:\doconverter\config\logging.conf'
    FILEINI = 'c:\doconverter\config\doconverter.ini'
with open(FILELOGS) as jdata:
    config_logging = json.load(jdata)

server = platform.uname()[1]
if server.index('.') > 0:
    server = server.split('.')[0]
logging.config.dictConfig(config_logging)
logger = logging.getLogger('doconverter-api')

logger.debug("logger has been initialised")
print(FILEINI)
try:
    # Load configuration from file
    CONFIG = configparser.ConfigParser()
    CONFIG.read(FILEINI)
    # Get usual values
    APPCONFIG['servers'] = [server, ]

    if CONFIG.has_section('default'):
        if CONFIG.has_option('default','servers'):
            APPCONFIG['servers'] = CONFIG.get('default', 'servers').split(',')
        if CONFIG.has_option("default", "prefix_dir"):
            APPCONFIG["prefix_dir"] = CONFIG.get("default", "prefix_dir")
            for computer in APPCONFIG['servers']:
                APPCONFIG[computer] = {}
                if CONFIG.has_option('default', computer):
                    APPCONFIG[computer]["extensions_allowed"] = CONFIG.get('default', computer).split(',')
                    print("extensions_allowed {}".format(APPCONFIG[computer]["extensions_allowed"]))
                else:
                    logger.debug("{} has not allowed_extensions.".format(computer))
                    raise DoconverterException(
                        "{} has not allowed_extensions.".format(computer))
                if not os.path.exists(os.path.join(APPCONFIG["prefix_dir"], computer, 'var')):
                    logger.debug(os.path.join(APPCONFIG["prefix_dir"], computer, 'var') + " doesnt exist")
                    os.mkdir(os.path.join(APPCONFIG["prefix_dir"], computer, 'var'))
                APPCONFIG[computer]['prefix_dir'] = os.path.join(APPCONFIG["prefix_dir"], computer, 'var')
                print("extensions_allowed {}".format(APPCONFIG[computer]["prefix_dir"]))

                if not os.path.exists(os.path.join(APPCONFIG[computer]['prefix_dir'], "tasks")):
                    pathname = os.path.join(APPCONFIG[computer]['prefix_dir'], "tasks")
                    logger.debug(pathname + " doesnt exist")
                    os.mkdir(pathname)
                APPCONFIG[computer]["tasks"] = os.path.join(APPCONFIG[computer]["prefix_dir"], "tasks")
                print("extensions_allowed {}".format(APPCONFIG[computer]["tasks"]))

                if not os.path.exists(os.path.join(APPCONFIG[computer]["prefix_dir"], "uploadsresults")):
                    pathname = os.path.join(os.path.join(APPCONFIG[computer]["prefix_dir"], "uploadsresults"))
                    logger.debug("{} doesnt exist".format(pathname))
                    os.mkdir(pathname)
                APPCONFIG[computer]["uploadsresults"] = os.path.join(APPCONFIG[computer]["prefix_dir"],
                                                                     "uploadsresults")
                print("extensions_allowed {}".format(APPCONFIG[computer]["uploadsresults"]))

                if not os.path.exists(os.path.join(APPCONFIG[computer]["prefix_dir"], "error")):
                    pathname = os.path.join(os.path.join(APPCONFIG[computer]["prefix_dir"], "error"))
                    logger.debug("{} doesnt exist".format(pathname))
                    os.mkdir(pathname)
                APPCONFIG[computer]["error"] = os.path.join(APPCONFIG[computer]["prefix_dir"], "error")
                print("extensions_allowed {}".format(APPCONFIG[computer]["error"]))

                if not os.path.exists(os.path.join(APPCONFIG[computer]["prefix_dir"], "success")):
                    pathname = os.path.join(os.path.join(APPCONFIG[computer]["prefix_dir"], "success"))
                    logger.debug("{} doesnt exist".format(pathname))
                    os.mkdir(pathname)
                APPCONFIG[computer]["success"] = os.path.join(APPCONFIG[computer]["prefix_dir"], "success")
                print("extensions_allowed {}".format(APPCONFIG[computer]["success"]))

        if CONFIG.has_option('default', 'extensions_all'):
            APPCONFIG['extensions_all'] = CONFIG.get('default', 'extensions_all').split(',')
            logger.debug('all allowed extensions loaded: %s', APPCONFIG['extensions_all'])
        if CONFIG.has_option('default', 'archival_dir'):
            APPCONFIG['archival_dir'] = CONFIG.get('default', 'archival_dir')
            if not os.path.exists(APPCONFIG['archival_dir']):
                logger.debug("{} doesnt exist".format(APPCONFIG['archival_dir']))
                os.mkdir(APPCONFIG['archival_dir'])
        APPCONFIG['ca_bundle'] = False
        if CONFIG.has_option('default', 'ca_bundle'):
            APPCONFIG['ca_bundle'] = CONFIG.get('default', 'ca_bundle')

    if CONFIG.has_section('manager'):
        if CONFIG.has_option('manager', 'converters'):
            list_converters = CONFIG.get('manager', 'converters').split(',')
            APPCONFIG['converters'] = {}
            for converter in list_converters:
                APPCONFIG['converters'][converter] = {}
                if CONFIG.has_option(converter, 'extensions_allowed'):
                    APPCONFIG['converters'][converter]['extensions_allowed'] = \
                        CONFIG.get(converter, 'extensions_allowed').split(',')
                else:
                    logger.debug('converter %s is not properly defined', converter)
                    raise DoconverterException(
                        "{} is not properly defined: {} is missing.".format(converter, 'extensions_allowed'))
                if CONFIG.has_option(converter, 'output_allowed'):
                    APPCONFIG['converters'][converter]['output_allowed'] = \
                        CONFIG.get(converter, 'output_allowed').split(',')
                else:
                    logger.debug('converter %s is not properly defined', converter)
                    raise DoconverterException(
                        "{} is not properly defined: {} is missing.".format(converter, 'output_allowed'))
                if CONFIG.has_option(converter, 'type'):
                    APPCONFIG['converters'][converter]['type'] = CONFIG.get(converter, 'type')
                else:
                    logger.debug('converter %s is not properly defined', converter)
                    raise DoconverterException(
                        "{} is not properly defined: {} is missing.".format(converter, 'type'))
                if CONFIG.has_option(converter, 'exe'):
                    APPCONFIG['converters'][converter]['exe'] = CONFIG.get(converter, 'exe')
                else:
                    logger.debug('converter %s is not properly defined, missing exe', converter)
                    raise DoconverterException(
                        "{} is not properly defined: {} is missing.".format(converter, 'exe'))
        if CONFIG.has_option('manager', 'stopper'):
            APPCONFIG['stopper'] = CONFIG.get('manager', 'stopper')

    if CONFIG.has_section('monitor'):
        if CONFIG.has_option('monitor', 'emails'):
            APPCONFIG['emails'] = CONFIG.get('monitor', 'emails').split(',')
        if CONFIG.has_option('monitor', 'tasksalert'):
            APPCONFIG['taskalert'] = CONFIG.get('monitor', 'tasksalert')
        if CONFIG.has_option('monitor', 'smtpserver'):
            APPCONFIG['smtpserver'] = CONFIG.get('monitor', 'smtpserver')

    if CONFIG.has_section('database'):
        host = None
        port = None
        db = None
        user = None
        password = None
        if CONFIG.has_option('database', 'host'):
            host = CONFIG.get('database', 'host')
        if CONFIG.has_option('database', 'port'):
            port = CONFIG.get('database', 'port')
        if CONFIG.has_option('database', 'db'):
            db = CONFIG.get('database', 'db')
        if CONFIG.has_option('database', 'user'):
            user = CONFIG.get('database', 'user')
        if CONFIG.has_option('database', 'password'):
            password = CONFIG.get('database', 'password')
        if host and port and db and user and password:
            APPCONFIG['SQLALCHEMY_DATABASE_URI'] = '{}:{}@{}:{}/{}'.format(user, password, host, port, db)
        else:
            raise DoconverterException("Some db config is not defined")

except IOError as e:
    traceback.print_exc(file=sys.stdout)
    sys.exit(e.code)
except configparser.NoOptionError:
    traceback.print_exc(file=sys.stdout)
    sys.exit(1)
