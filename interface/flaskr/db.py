import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext
import datetime
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, MetaData, DateTime, Text, Float
from sqlalchemy.dialects import oracle

tp_dict = {}

def close_db(e=None):
    # close the session
    db = g.pop('db', None)

    if db is not None:
        db.close()

Base = declarative_base()

# Define Pre questionnaire table:
# More info here: https://ati-scale.org
class ATI_PreQ (Base):
    # table name
    __tablename__ = 'ATI_preq'

    # table structure
    user_id = Column(String(30), primary_key=True)
    answer_1 = Column(String(20))
    answer_2 = Column(String(20))
    answer_3 = Column(String(20))
    answer_4 = Column(String(20))
    answer_5 = Column(String(20))
    answer_6 = Column(String(20))
    answer_7 = Column(String(20))
    answer_8 = Column(String(20))
    answer_9 = Column(String(20))
    created_time = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):    # make it printable
        init_str = "<user_id:{}".format(user_id)
        for i in range(1, 10):
            init_str += " answer_{}: {}".format(i, get_attr(self, 'answer_%d'%(i)))
        return init_str

# Define Trust in Automation Post questionnaire table:
# https://github.com/moritzkoerber/TiA_Trust_in_Automation_Questionnaire
class TiA_PostQ(Base):
    # table name
    __tablename__ = 'TiA_postq'

    # table structure
    user_id = Column(String(30), primary_key=True)
    answer_1 = Column(String(20))
    answer_2 = Column(String(20))
    answer_3 = Column(String(20))
    answer_4 = Column(String(20))
    answer_5 = Column(String(20))
    answer_6 = Column(String(20))
    answer_7 = Column(String(20))
    answer_8 = Column(String(20))
    answer_9 = Column(String(20))
    answer_10 = Column(String(20))
    answer_11 = Column(String(20))
    answer_12 = Column(String(20))
    answer_13 = Column(String(20))
    answer_14 = Column(String(20))
    answer_15 = Column(String(20))
    answer_16 = Column(String(20))
    answer_17 = Column(String(20))
    answer_18 = Column(String(20))
    answer_19 = Column(String(20))
    created_time = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):    # make it printable
        init_str = "<user_id:{}".format(user_id)
        for i in range(1, 20):
            init_str += " answer_{}: {}".format(i, get_attr(self, 'answer_%d'%(i)))
        return init_str

class UserInfo(Base):
    # table name
    __tablename__ = 'userinfo'

    # table structure
    user_id = Column(String(200), primary_key=True)
    task_order_str = Column(String(500))
    user_group = Column(String(200))
    created_time = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):    # make it printable
        return "<id:{0} task_id:{1} user_group:{2}>".format(self.user_id,
         self.task_order_str, self.user_group)

class UserBehavior(Base):
    # table name
    __tablename__ = 'userbehavior'

    # table structure
    user_id = Column(String(30), primary_key=True)
    event_desc = Column(String(200), primary_key=True)
    user_behavior = Column(String(200))
    created_time = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):    # make it printable
        return "<id:{0} event:{1} behavior:{2}>".format(self.user_id,
         self.event_desc, self.user_behavior)

class UserFeedback(Base):
    # table name
    __tablename__ = 'userfeedback'

    # table structure
    user_id = Column(String(30), primary_key=True)
    task_id = Column(String(200), primary_key=True)
    feedback_type = Column(String(200), primary_key=True)
    user_feedback = Column(Text, default=None)
    created_time = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):    # make it printable
        return "<id:{0} task_id:{1} feedback:{2}>".format(self.user_id,
         self.task_id, self.user_feedback)

# Define User-Task table:
class UserTask(Base):
    # table name
    __tablename__ = 'usertask'

    # table structure
    user_id = Column(String(30), primary_key=True)
    task_id = Column(String(200), primary_key=True)
    answer_type = Column(String(200), primary_key=True)
    choice = Column(String(200))
    created_time = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):    # make it printable
        return "<id:{0} task_id:{1} answer_type:{2} choice:{3}>".format(self.user_id,
         self.task_id, self.answer_type, self.choice)


# ----------------
# tables for toolkits in the planning tasks

class UserAlarm(Base):
    # table name
    __tablename__ = 'useralarm'

    # table structure
    user_id = Column(String(30), primary_key=True)
    alarm_id = Column(Integer, primary_key=True)
    created_time = Column(DateTime, default=datetime.datetime.utcnow)


# Alarms:
class Alarm(Base):
    # table name
    __tablename__ = 'alarm'

    # table structure
    alarm_id = Column(Integer, primary_key=True)
    hour = Column(Integer)
    minute = Column(Integer)
    date = Column(String(200))
    repeat = Column(String(200))
    created_time = Column(DateTime, default=datetime.datetime.utcnow)

# Restaurant:
class UserOrder(Base):
    # table name
    __tablename__ = 'userorder'

    # table structure
    user_id = Column(String(30), primary_key=True)
    table_id = Column(Integer, default=10, primary_key=True)
    order_id = Column(Integer, primary_key=True)
    created_time = Column(DateTime, default=datetime.datetime.utcnow)

class FoodOrder(Base):
    # table name
    __tablename__ = 'foodorder'

    # table structure
    order_id = Column(Integer, primary_key=True)
    dish_1 = Column(Integer, default=0)
    dish_2 = Column(Integer, default=0)
    dish_3 = Column(Integer, default=0)
    dish_4 = Column(Integer, default=0)
    created_time = Column(DateTime, default=datetime.datetime.utcnow)

# Flight:
class UserFlight(Base):
    # table name
    __tablename__ = 'userflight'

    # table structure
    user_id = Column(String(30), primary_key=True)
    flight_id = Column(String(30), primary_key=True)
    flight_class = Column(String(200))
    created_time = Column(DateTime, default=datetime.datetime.utcnow)

# Finance:
class UserBalance(Base):
    # table name
    __tablename__ = 'userbalance'

    # table structure
    user_id = Column(String(30), primary_key=True)
    account = Column(String(30), primary_key=True)
    passwd = Column(String(30))
    USD = Column(Float(3).with_variant(oracle.FLOAT(binary_precision=16), "oracle"), default=0)
    RMB = Column(Float(3).with_variant(oracle.FLOAT(binary_precision=16), "oracle"), default=0)
    JPY = Column(Float(3).with_variant(oracle.FLOAT(binary_precision=16), "oracle"), default=0)
    EUR = Column(Float(3).with_variant(oracle.FLOAT(binary_precision=16), "oracle"), default=0)
    created_time = Column(DateTime, default=datetime.datetime.utcnow)


class CardBalance(Base):
    # table name
    __tablename__ = 'cardbalance'

    # table structure
    card = Column(String(30), primary_key=True)
    card_type = Column(String(30))
    user_id = Column(String(30), primary_key=True)
    balance = Column(Float(3).with_variant(oracle.FLOAT(binary_precision=16), "oracle"), default=0)
    created_time = Column(DateTime, default=datetime.datetime.utcnow)


class LoanStatus(Base):
    # table name
    __tablename__ = 'loanstatus'

    # table structure
    user_id = Column(String(30), primary_key=True)
    loan_id = Column(String(30), primary_key=True)
    loan_status = Column(String(30), default=0)
    submission_time = Column(String(30), primary_key=True)
    review_time = Column(String(30), primary_key=True)
    created_time = Column(DateTime, default=datetime.datetime.utcnow)


@click.command('init-db')
@with_appcontext
def init_db_command():
    """create new tables."""
    g.debug = current_app.config["DEBUG"]
    init_db()
    click.echo('Initialized the database.')

def init_db():
    create_all_tables()
    get_db()

# Create engine through sqlalchemy
prefix = "postgresql+psycopg2://"
external_link = "" # put your DB link
internal_link = "" # deployment option with internal DB link in server or service provider

# deployment on server
engine = create_engine(prefix + internal_link, echo=False)
# development on local machine
# engine = create_engine(prefix + external_link, echo=False)

# Create database if not exists
if not database_exists(engine.url): 
    create_database(engine.url)         # Create database if it doesn't exist.


def get_db_outside():
    # ideally, the db connection is shared
    if 'db' not in tp_dict:
        DBSession = sessionmaker(bind=engine)

        # 创建session对象:
        tp_dict['db'] = DBSession()

    return tp_dict['db']

def get_db():
    # create a session
    if 'db' not in g:
        DBSession = sessionmaker(bind=engine)

        # 创建session对象:
        g.db = DBSession()
        tp_dict['db'] = g.db

    return g.db

def get_engine():
    return engine

def create_all_tables():
    Base.metadata.create_all(engine)   # 创建表结构
    # if table exist, it will ignore this operation

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
