from flaskr.db import get_db, UserTask, UserBehavior, UserInfo, TiA_PostQ, UserFeedback, engine
from flaskr.db import Alarm, UserAlarm, UserFlight
from sqlalchemy.sql import text
from sqlalchemy import update, select, delete
from flask.cli import with_appcontext
from sqlalchemy.orm import Session

# tools are outside of flask context, so we do not get global db connection
def book_flight_ticket(user_id:str, flight_id:str, flight_class:str):
    with Session(engine) as db:
        q = db.query(UserFlight.user_id).filter(UserFlight.user_id==user_id and UserFlight.flight_id == flight_id)
        exist_flag = db.query(q.exists()).scalar()
        if not exist_flag:
            tp_obj = UserFlight(user_id=user_id, flight_id=flight_id, flight_class=flight_class)
            db.add(tp_obj)
            db.commit()
            return False
        else:
            return True

# only used in flask app context
def save_user_info(user_id, user_task_order, user_group):
    db = get_db()
    q = db.query(UserInfo.user_id).filter(UserInfo.user_id==user_id)
    exist_flag = db.query(q.exists()).scalar()
    # if exist_flag:
    #     return True
    task_order_str = "|".join(user_task_order)

    if not exist_flag:
        ui_obj = UserInfo(user_id=user_id, task_order_str=task_order_str, user_group=user_group)
        db.add(ui_obj)
        db.commit()
    else:
        stmt = update(UserInfo).where(UserInfo.user_id==user_id).values(task_order_str=task_order_str, user_group=user_group).execution_options(synchronize_session="fetch")
        result = db.execute(stmt)
        db.commit()
        # current_app.logger.info("User {} exist, update userinfo".format(user_id))
        return True
    return False

def save_event(user_id, event_desc, user_behavior):
    db = get_db()
    tp_obj = UserBehavior(user_id=user_id, event_desc=event_desc, user_behavior=user_behavior)
    q = db.query(UserBehavior.user_id).filter(UserBehavior.user_id==user_id, UserBehavior.event_desc==event_desc)
    exist_flag = db.query(q.exists()).scalar()
    if not exist_flag:
        db.add(tp_obj)
        db.commit()
    else:
        stmt = update(UserBehavior).where(UserBehavior.user_id==user_id, UserBehavior.event_desc==event_desc).values(user_behavior=user_behavior).execution_options(synchronize_session="fetch")
        result = db.execute(stmt)
        db.commit()
        # current_app.logger.info("User {} has record taskid-answer_type:{}-{} exist, update usertask".format(user_id, task_id, answer_type))

def save_user_trust(answer_dict, user_id):
    db = get_db()
    q = db.query(TiA_PostQ.user_id).filter(TiA_PostQ.user_id==user_id)
    exist_flag = db.query(q.exists()).scalar()
    if not exist_flag:
        preq_obj = TiA_PostQ(**answer_dict)
        db.add(preq_obj)
        db.commit()

def save_user_choice(user_id, task_id, choice, answer_type="attention"):
    db = get_db()
    q = db.query(UserTask.user_id).filter(UserTask.user_id==user_id, UserTask.task_id==task_id, UserTask.answer_type==answer_type)
    exist_flag = db.query(q.exists()).scalar()
    if not exist_flag:
        ut_obj = UserTask(user_id=user_id, task_id=task_id, choice=choice, answer_type=answer_type)
        db.add(ut_obj)
        db.commit()
    else:
        stmt = update(UserTask).where(UserTask.user_id==user_id, UserTask.task_id==task_id, UserTask.answer_type==answer_type).values(choice=choice).execution_options(synchronize_session="fetch")
        result = db.execute(stmt)
        db.commit()
        # current_app.logger.info("User {} has record taskid-answer_type:{}-{} exist, update usertask".format(user_id, task_id, answer_type))

def save_user_feedback(user_id, task_id, content, feedback_type):
    db = get_db()
    q = db.query(UserFeedback.user_id).filter(UserFeedback.user_id==user_id, UserFeedback.task_id==task_id, UserFeedback.feedback_type==feedback_type)
    exist_flag = db.query(q.exists()).scalar()
    if not exist_flag:
        ut_obj = UserFeedback(user_id=user_id, task_id=task_id, user_feedback=content, feedback_type=feedback_type)
        db.add(ut_obj)
        db.commit()
    else:
        # stmt = (
        #         update(UserFeedback).
        #         where(UserFeedback.user_id==user_id, UserFeedback.task_id==task_id).
        #         values(user_feedback=plan)
        #     )
        stmt = update(UserFeedback).where(UserFeedback.user_id==user_id, UserFeedback.task_id==task_id, UserFeedback.feedback_type==feedback_type).values(user_feedback=content).execution_options(synchronize_session="fetch")
        result = db.execute(stmt)
        db.commit()
        # current_app.logger.info("User {} has record taskid-answer_type:{}-{} exist, update usertask".format(user_id, task_id, answer_type))

def save_user_plan(user_id, task_id, plan):
    save_user_feedback(user_id, task_id, content=plan, feedback_type="plan")
