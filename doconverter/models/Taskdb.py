#!c:\Python34\python.exe
# -*- coding: utf-8 -*-

# Copyright (C) 2017, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.

import logging
from sqlalchemy.orm.exc import NoResultFound
from doconverter.tools.Utils import Utils
from datetime import datetime, timedelta
from doconverter.models.extensions import db
from doconverter.tools.Task import Task


class Taskdb(db.Model):
    __tablename__ = 'taskdb'
    __table_args__ = (db.Index('timefortaskdb_col', 'logdate'),
                      db.Index('converterextension_col', 'converter', 'extension'),
                      {'schema': 'doconverter', 'extend_existing': True})

    extension = db.Column(db.String(16), nullable=False)
    newfilename = db.Column(db.String(128), nullable=False)
    fullocalpath = db.Column(db.String(256), nullable=False)
    uploadedfile = db.Column(db.String(128), nullable=False)
    taskid = db.Column(db.Integer(), nullable=False, primary_key=True)
    urlresponse = db.Column(db.String(256), nullable=False)
    converter = db.Column(db.String(16), nullable=False)
    logdate = db.Column(db.DateTime, nullable=False)
    server = db.Column(db.String(64), nullable=False, primary_key=True)
    db.PrimaryKeyConstraint('server', 'taskid')

    def __init__(self, extension, newfilename, fullocalpath, uploadedfile, taskid, urlresponse, converter, server=None):
        self.extension = extension
        self.newfilename = newfilename
        self.taskid = taskid
        self.converter = converter
        self.fullocalpath = fullocalpath
        self.uploadedfile = uploadedfile
        self.urlresponse = urlresponse
        if not server:
            self.server = Utils.getserver()
        else:
            self.server = server
        self.logdate = datetime.now()

    def fill(self, fields, _=None):
        """
            Fill the current object with the values in the param fields
        """
        self.extension = fields.get('extension')
        if not self.extension:
            raise ValueError('extension name must be set')
        self.newfilename = fields.get('newfilename')
        if not self.newfilename:
            raise ValueError('newfilename name must be set')
        self.taskid = fields.get('taskid')
        if not self.taskid:
            raise ValueError('taskid name must be set')
        self.converter = fields.get('converter')
        if not self.converter:
            raise ValueError('converter name must be set')
        self.uploadedfile = fields.get('uploadedfile')
        if not self.uploadedfil:
            raise ValueError('uploadedfile name must be set')
        self.urlresponse = fields.get('urlresponse')
        if not self.urlresponse:
            raise ValueError('urlresponse name must be set')
        self.fullocalpath = fields.get('fullocalpath')
        if not self.fullocalpath:
            raise ValueError('fullocalpath name must be set')
        self.server = Utils.getserver()
        self.logdate = datetime.now()

    @classmethod
    def create_new_task(cls, fields):
        task = Task(fields)
        task.fill(fields)
        return task

    def __repr__(self):
        return '<taskid {} converter {} urlresponse {}>'.format(self.taskid,
                                                                self.converter,
                                                                self.urlresponse)


class TaskMapper(object):
    """
        TaskMapper to define bindings and operations between classes and database tables
    """
    def __init__(self):
        pass

    @classmethod
    def fetchby_id(cls, id):
        """
            Fetch one object by primary key or common name
        """
        try:
            result = Taskdb.query.filter((Taskdb.taskid == id)).one()
        except NoResultFound:
            result = None
        return result

    @classmethod
    def fetchby_server_taskid(cls, server, taskid):
        """
            Fetch one object by primary key or common name
        """
        try:
            result = Taskdb.query.filter(
                (Taskdb.taskid == taskid) & (Taskdb.server == server)).all()
        except NoResultFound:
            result = None
        return result

    @classmethod
    def fetchall_by_serverandextension(cls, datesince=30):
        """
            Fetch all contects order by server and extension since a month ago by default, 30 days
        """
        tasks = db.session.\
            query(Taskdb.server, Taskdb.extension, Taskdb.converter, db.func.count(Taskdb.converter).label("Count"))\
            .filter(Taskdb.logdate >= datetime.now() - timedelta(days=datesince))\
            .group_by(Taskdb.server, Taskdb.extension, Taskdb.converter)\
            .order_by(db.func.count(Taskdb.converter).desc())\
            .all()
        return tasks

    @classmethod
    def fetchall_by_server(cls, datesince=30):
        """
            Fetch all contects order by server and extension since a month ago by default, 30 days
        """
        tasks = db.session. \
            query(Taskdb.server, Taskdb.converter, db.func.count(Taskdb.converter).label("Count")) \
            .filter(Taskdb.logdate >= datetime.now() - timedelta(days=datesince)) \
            .group_by(Taskdb.server, Taskdb.converter) \
            .all()
        return tasks

    @classmethod
    def insert(cls, task):
        """
            Insert the object given by param.
        """
        try:
            db.session.add(task)
            db.session.commit()
        except Exception as ex:
            logging.getLogger('doconverter-api').debug(ex)
            db.session.rollback()
            return False
        return True

    @classmethod
    def insert_from_taskfile(cls, task):
        """
            Insert the object given by param which is a Task file instead a Task db (row representation).
        """

        taskdb = Taskdb(task.extension, task.newfilename, task.fullocalpath, task.uploadedfile,
                        task.taskid, task.urlresponse, task.converter
                        )
        return TaskMapper.insert(taskdb)

    @classmethod
    def delete(cls, server, taskid):
        """
            Delete the object identified by the room_name
        """
        try:
            task = Task.query.filter_by(server=server, taskid=taskid).one()
            print('from task')
            print(task)
            db.session.delete(task)
            db.session.commit()
        except Exception as ex:
            logging.getLogger('doconverter-api').debug(ex)
            db.session.rollback()
            return False
        return True
