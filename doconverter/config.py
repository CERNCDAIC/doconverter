#!c:\Python34\python.exe
# -*- coding: utf-8 -*-

# Copyright (C) 2016, CERN
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
from doconverter.DoconverterException import DoconverterException

CONFIG = None
APPCONFIG = {}

with open("PATHTOlogging.conf") as jdata:
    config_logging = json.load(jdata)

logging.config.dictConfig(config_logging)
logger = logging.getLogger('doconverter-api')

logger.debug("logger has been initialised")

try:
    # Load configuration from file
    CONFIG = configparser.ConfigParser()
    CONFIG.read("PATHTOdoconverter.ini")
    # Get usual values
    if CONFIG.has_section("default"):
        if CONFIG.has_option("default", "prefix_dir"):
            APPCONFIG["prefix_dir"] = CONFIG.get("default", "prefix_dir")
            # logger.debug("checking directory: " + APPCONFIG["prefix_dir"])
            if not os.path.exists(APPCONFIG["prefix_dir"]):
                raise DoconverterException(APPCONFIG["prefix_dir"] + " doesnt exist")

            # logger.debug("checking directory: " + os.path.join( APPCONFIG["prefix_dir"], "tasks"))
            if not os.path.exists(os.path.join(APPCONFIG["prefix_dir"], "tasks")):
                pathname = os.path.join(APPCONFIG["prefix_dir"], "tasks")
                raise DoconverterException(pathname + " doesnt exist")
            APPCONFIG["tasks"] = os.path.join(APPCONFIG["prefix_dir"], "tasks")

            # logger.debug("checking directory: " + os.path.join(APPCONFIG["prefix_dir"], "uploadsresults"))
            if not os.path.exists(os.path.join(APPCONFIG["prefix_dir"], "uploadsresults")):
                pathname = os.path.join(os.path.join(APPCONFIG["prefix_dir"], "uploadsresults"))
                raise DoconverterException("{} doesnt exist".format(pathname))
            APPCONFIG["uploadsresults"] = os.path.join(APPCONFIG["prefix_dir"], "uploadsresults")

            # logger.debug("checking directory: " + os.path.join(APPCONFIG["prefix_dir"], "error"))
            if not os.path.exists(os.path.join(APPCONFIG["prefix_dir"], "error")):
                pathname = os.path.join(os.path.join(APPCONFIG["prefix_dir"], "error"))
                raise DoconverterException("{} doesnt exist".format(pathname))
            APPCONFIG["error"] = os.path.join(APPCONFIG["prefix_dir"], "error")

            # logger.debug("checking directory: " + os.path.join(APPCONFIG["prefix_dir"], "success"))
            if not os.path.exists(os.path.join(APPCONFIG["prefix_dir"], "success")):
                pathname = os.path.join(os.path.join(APPCONFIG["prefix_dir"], "success"))
                raise DoconverterException("{} doesnt exist".format(pathname))
            APPCONFIG["success"] = os.path.join(APPCONFIG["prefix_dir"], "success")
        if CONFIG.has_option('default', 'extensions_all'):
            APPCONFIG['extensions_all'] = CONFIG.get('default', 'extensions_all').split(',')
            logger.debug('all allowed extensions loaded: %s', APPCONFIG['extensions_all'])
        if CONFIG.has_option('default', 'archival_dir'):
            APPCONFIG['archival_dir'] = CONFIG.get('default', 'archival_dir')

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
except IOError as e:
    traceback.print_exc(file=sys.stdout)
    sys.exit(e.code)
except configparser.NoOptionError:
    traceback.print_exc(file=sys.stdout)
    sys.exit(1)
