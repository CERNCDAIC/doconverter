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


class Result_Conversion(db.Model):
    __tablename__ = 'results_conversion'
    __table_args__ = (db.ForeignKeyConstraint(
        ['server', 'taskid'],
        ['doconverter.taskdb.server', 'doconverter.taskdb.taskid'],
        onupdate='cascade', ondelete='cascade'), db.Index('time_col', 'logdate'),
                      db.Index('fk_constraint', 'server', 'taskid'),
                      {'schema': 'doconverter'})

    id = db.Column(db.Integer, primary_key=True)
    from_ext = db.Column(db.String(16), nullable=False)
    to_ext = db.Column(db.String(16), nullable=False)
    taskid = db.Column(db.Integer(), nullable=False)  # db.ForeignKey('doconverter.task.taskid', onupdate='cascade'))

    # converter engine
    converter = db.Column(db.String(64), nullable=False)
    server = db.Column(db.String(64), nullable=False)
    error = db.Column(db.String(2048), nullable=True)
    # size in kb
    size_from = db.Column(db.Integer(), nullable=False)
    size_to = db.Column(db.Integer(), nullable=False)
    # how long it took in secs
    duration = db.Column(db.Integer(), nullable=False)
    logdate = db.Column(db.DateTime, nullable=False)
    task = db.relationship('Taskdb', backref=db.backref('results',
                                                        cascade="all, delete, delete-orphan",
                                                        single_parent=True))

    def __init__(self, from_ext=None, to_ext=None, taskid=None,
                 converter=None, size_from=None, size_to=None, duration=None, error=None):
        self.from_ext = from_ext
        self.to_ext = to_ext
        self.taskid = taskid
        self.converter = converter
        self.size_from = size_from
        self.size_to = size_to
        self.duration = duration
        self.server = Utils.getserver()
        self.logdate = datetime.now()
        self.error = error

    def fill(self, fields, _=None):
        """
            Fill the current object with the values in the param fields
        """
        self.from_ext = fields.get('from_ext')
        if not self.from_ext:
            raise ValueError('from_ext name must be set')
        self.to_ext = fields.get('to_ext')
        if not self.to_ext:
            raise ValueError('to_ext name must be set')
        self.taskid = fields.get('taskid')
        if not self.taskid:
            raise ValueError('taskid name must be set')
        self.converter = fields.get('converter')
        if not self.converter:
            raise ValueError('converter name must be set')
        self.size_from = fields.get('size_from', -1)
        self.size_to = fields.get('size_to', -1)
        self.duration = fields.get('duration', -1)
        self.server = Utils.getserver()
        print(self.server)
        self.logdate = datetime.now()
        self.error = fields.get('error', None)

    @classmethod
    def create_new_result(cls, fields):
        result = Result_Conversion(fields)
        result.fill(fields)
        return result

    def __repr__(self):
        return '<taskid {} from {} to {} size_from {} size_to {} duration {}>'.format(self.taskid,
                                                                                      self.from_ext,
                                                                                      self.to_ext,
                                                                                      self.size_from,
                                                                                      self.size_to,
                                                                                      self.duration)


class Result_ConversionMapper(object):
    """
        Result_ConversionMapper to define bindings and operations between classes and database tables
    """

    def __init__(self):
        pass

    @classmethod
    def fetchby_id(cls, id):
        """
            Fetch one object by primary key or common name
        """
        try:
            result = Result_Conversion.query.filter((Result_Conversion.id == id)).one()
        except NoResultFound:
            result = None
        return result

    @classmethod
    def fetch_topN(cls, column, numberofrows=10, ascending=0, datesince=30):
        """
            Fetch N rows order in ascending mode by a certain column
        """
        try:
            if ascending:
                result = db.session.query(Result_Conversion.taskid,
                                          Result_Conversion.from_ext,
                                          Result_Conversion.to_ext,
                                          Result_Conversion.size_from,
                                          Result_Conversion.size_to,
                                          Result_Conversion.duration) \
                    .filter(Result_Conversion.logdate >= (datetime.now() - timedelta(days=datesince)))\
                    .order_by(column)\
                    .limit(numberofrows)\
                    .all()
            else:
                result = db.session.query(Result_Conversion.taskid,
                                          Result_Conversion.from_ext,
                                          Result_Conversion.to_ext,
                                          Result_Conversion.size_from,
                                          Result_Conversion.size_to,
                                          Result_Conversion.duration) \
                    .filter(Result_Conversion.logdate >= (datetime.now() - timedelta(days=datesince))) \
                    .order_by(column.desc()) \
                    .limit(numberofrows) \
                    .all()
        except NoResultFound:
            result = None
        return result

    @classmethod
    def fetch_top1(cls, datesince=30):
        """
            Fetch 1 rows order in ascending mode by a certain column
        """
        try:
            duration = Result_ConversionMapper.fetch_topN(Result_Conversion.duration,
                                                          numberofrows=1,
                                                          datesince=datesince)
            size_to = Result_ConversionMapper.fetch_topN(Result_Conversion.size_to,
                                                         numberofrows=1,
                                                         datesince=datesince)
            result = duration + size_to
        except NoResultFound:
            result = None
        return result

    @classmethod
    def fetch_balance(cls, datesince=30):
        """
            Fetch N rows order in ascending mode by a certain column
        """
        try:
            total = db.session.query(db.func.count(1)). \
                filter(Result_Conversion.logdate >= (datetime.now() - timedelta(days=datesince))). \
                label('total_jobs')

            result = db.session.query(db.func.count(1), total). \
                filter(Result_Conversion.duration == -1,
                       Result_Conversion.logdate >= (datetime.now() - timedelta(days=datesince)))\
                .all()
        except NoResultFound:
            result = None
        return result

    @classmethod
    def fetchby_server_taskid(cls, server, taskid):
        """
            Fetch one object by primary key or common name
        """
        try:
            result = Result_Conversion.query.filter(
                (Result_Conversion.taskid == taskid) & (Result_Conversion.server == server)).all()
        except NoResultFound:
            result = None
        return result

    @classmethod
    def insert(cls, result):
        """
            Insert the object given by param.
        """
        try:
            db.session.add(result)
            db.session.commit()
        except Exception as ex:
            logging.getLogger('doconverter-api').debug(ex)
            db.session.rollback()
            return False
        return True

    @classmethod
    def insert_dict(cls, result):
        """
            Insert the object given by param, in this case a dictionary.
        """
        re = Result_Conversion()
        re.fill(result)
        return Result_ConversionMapper.insert(re)

    @classmethod
    def delete(cls, server, taskid):
        """
            Delete the object identified by the room_name
        """
        result = Result_Conversion.query.filter(
                (Result_Conversion.taskid == taskid) & (Result_Conversion.server == server)).one()
        try:
            db.session.delete(result)
            db.session.commit()
        except Exception as ex:
            logging.getLogger('doconverter-api').debug(ex)
            db.session.rollback()
            return False
        return True

    @classmethod
    def delete_row(cls, row):
        """
            Delete the object identified by the room_name
        """
        try:
            db.session.delete(row)
            db.session.commit()
        except Exception as ex:
            logging.getLogger('doconverter-api').debug(ex)
            db.session.rollback()
            return False
        return True
