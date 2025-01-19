from langchain.tools import tool, BaseTool
from langchain.pydantic_v1 import BaseModel, Field
from typing import Optional, Type, List, Dict, Literal
import json
# from flaskr.db_utli import add_alarm, delete_alarm, get_alarms

# weekday = ["monday", "tuesday", "wednesday", "thursday", "friday"]
# weekend = ["saturday", "sunday"]
weekday = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
weekend = ["Saturday", "Sunday"]
# Tools

class AlarmInput(BaseModel):
    user_id: str = Field(description="User ID")
    hour: int = Field(description="The hour to run the alarm, valid input range from 0 to 23", ge=0, le=23)
    minute: int = Field(description="The minute to run the alarm, valid input range from 0 to 59", ge=0, le=59)
    repeat: Literal['Once', 'Weekly'] = Field(description="Whether the alarm repeat weekly. Valid input: Once, Weekly")
    frequency: Literal["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Weekday", "Weekend"] = Field(description="How often to run the alarm in one week. Valid input: Monday to Sunday, weekday, Weekend")

def check_clock_input(hour: int, minute:int, repeat:str, frequency: str):
    if hour < 0 or hour >= 24:
        return False, {
            "user_message": f"Invalid hour input: {hour}, valid input range from 0-23",
            "message": f"Invalid hour input: {hour}, valid input range from 0-23",
        }
    if minute < 0 or minute >= 60:
        return False, {
            "user_message": f"Invalid hour input: {minute}, valid input range from 0-59",
            "message": f"Invalid hour input: {minute}, valid input range from 0-59"
        }
    if repeat not in ["Once", "Weekly"]:
        return False, {
            "user_message": f"Invalid repeat input: {repeat}, valid input: once | weekly",
            "message": f"Invalid repeat input: {repeat}, valid input: once | weekly"
        }
    # weekday = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    # weekend = ["saturday", "sunday"]
    # tp_freq = frequency.lower()
    if frequency in ["Weekday", "Weekend"]:
        return True, {}
    elif frequency in weekday or frequency in weekend:
        return True, {}
    else:
        return False, {
            "user_message": f"Invalid frequency input: {frequency}, valid input in [Weekday, Weekend, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday]",
            "message": f"Invalid frequency input: {frequency}, valid input in [Weekday, Weekend, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday]"
        }

@tool("create_alarm", return_direct=True, args_schema=AlarmInput)
def create_alarm(user_id: str, hour: int, minute:int, repeat:str, frequency: str) -> Dict:
    '''Create an alarm with hour, minute, repeat and frequency as input'''
    check_flag, response = check_clock_input(hour=hour, minute=minute, repeat=repeat, frequency=frequency)
    if not check_flag:
        return response
    # tp_freq = frequency.lower()
    # alarms = []
    if frequency == "Weekday":
        for day in weekday:
            add_alarm(user_id=user_id, hour=hour, minute=minute, repeat=repeat, date=day)
    elif frequency == "Weekend":
        for day in weekend:
            add_alarm(user_id=user_id, hour=hour, minute=minute, repeat=repeat, date=day)
    elif frequency in weekday or frequency in weekend:
        add_alarm(user_id=user_id, hour=hour, minute=minute, repeat=repeat, date=frequency)
    else:
        return {
            "user_message": f"Invalid frequency input: {frequency}, valid input in [Weekday, Weekend, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday]",
            "message": f"Invalid frequency input: {frequency}, valid input in [Weekday, Weekend, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday]"
        }
    alarms = get_alarms(user_id=user_id)
    # print(alarms)
    alarm_string = "Alarm created, currently you have following alarms:\n"
    for index, alarm in enumerate(alarms):
        hour, minute, repeat, date = alarm
        # uid_ = alarm["user_id"]
        # hour = alarm["hour"]
        # minute = alarm["minute"]
        # repeat = alarm["repeat"]
        # freq = alarm["freq"]
        alarm_string += f"{index+1}. {hour}:{minute} on {date}, repeat: {repeat}\n"
    # alarm_string += "alarms = " + json.dumps(alarms)
    res = {
        "alarms": alarms,
        "message": alarm_string,
        "user_message": alarm_string
    }
    return res

@tool("cancel_alarm", return_direct=True, args_schema=AlarmInput)
def cancel_alarm(user_id: str, hour: int, minute:int, repeat:str, frequency: str) -> str:
    '''Given existing alarms. Cancel an alarm with hour, minute, repeat and frequency as input'''
    # ensure that the input of this tool is valid
    check_flag, response = check_clock_input(hour=hour, minute=minute, repeat=repeat, frequency=frequency)
    if not check_flag:
        return response
    index_to_delete = -1
    alarms = get_alarms(user_id=user_id)
    for index, alarm in enumerate(alarms):
        hour_, minute_, repeat_, date_ = alarm
        # hour, minute, repeat, date = alarm
        # uid_ = alarm.user_id
        # hour_ = alarm["hour"]
        # minute_ = alarm["minute"]
        # repeat_ = alarm["repeat"]
        # freq_ = alarm["freq"]
        if int(hour_) == hour and int(minute_) == minute and repeat == repeat_ and date_ == frequency:
            index_to_delete = index
            break
    if index_to_delete == -1:
        return {
            "message": "the alarm to cancel does not exist",
            "user_message": "the alarm to cancel does not exist"
        }
    else:
        # remove the alarm in the index
        # item = alarm.pop(index_to_delete)
        # hour, minute, repeat, freq = item
        flag, user_message = delete_alarm(user_id=user_id, hour=hour, minute=minute, repeat=repeat, date=frequency)
        # user_message = f"successfully removed alarm: {hour}:{minute} on {frequency}, repeat: {repeat}\n"
        res = {
            "message": user_message,
            "user_message": user_message
        }
        return res


# To-do: implement update alarm




# DB operations
from flaskr.db import Alarm, UserAlarm
from sqlalchemy import update, select, delete
from sqlalchemy.orm import Session
from flaskr.db import engine, get_db_outside

# tools are outside of flask context, so we do not get global db connection
def add_alarm(user_id:str, hour:int, minute:int, repeat:str, date:str):
    # step-1 search alarm in table alarm
    db = get_db_outside()
    # with Session(engine) as db:
    # step-1 search alarm in table alarm, get tp_index as alarm_id
    q = db.query(Alarm.alarm_id).filter(Alarm.hour==hour, Alarm.minute==minute, Alarm.date==date, Alarm.repeat==repeat)
    exist_flag = db.query(q.exists()).scalar()
    
    # If there does not exist such alarm, add to alarm table
    tp_index = -1
    if not exist_flag:
        alarm_count = db.query(Alarm).count()
        tp_obj = Alarm(alarm_id=alarm_count, hour=hour, minute=minute, date=date, repeat=repeat)
        db.add(tp_obj)
        db.commit()
        tp_index = alarm_count
    else:
        tp_index = q.first()[0]
    
    # step-2: add user_id, alarm_id and repeat
    q = db.query(UserAlarm.user_id).filter(UserAlarm.user_id==user_id, UserAlarm.alarm_id==tp_index)
    exist_flag = db.query(q.exists()).scalar()
    if not exist_flag:
        tp_obj = UserAlarm(user_id=user_id, alarm_id=tp_index)
        db.add(tp_obj)
        db.commit()
        return False
    else:
        return True

# tools are outside of flask context, so we do not get global db connection
def get_alarms(user_id:str):
    db = get_db_outside()
    alarms = []
    # with Session(engine) as db:
    stmt = (
        select(UserAlarm.user_id, Alarm.hour, Alarm.minute, Alarm.repeat, Alarm.date)
        .where(UserAlarm.user_id==user_id)
        .join(Alarm, UserAlarm.alarm_id == Alarm.alarm_id)
    )
    # print(stmt)
    result = db.execute(stmt).all()
    for row in result:
        user_id, hour, minute, repeat, date = row
        # print(row[1])
        alarms.append((hour, minute, repeat, date))
    # print(alarms)
    return alarms

# tools are outside of flask context, so we do not get global db connection
def delete_alarm(user_id:str, hour:int, minute:int, repeat:str, date:str):
    db = get_db_outside()
    # with Session(engine) as db:
    # step-1 search alarm in table alarm, get tp_index as alarm_id
    q = db.query(Alarm.alarm_id).filter(Alarm.hour==hour, Alarm.minute==minute, Alarm.date==date, Alarm.repeat==repeat)
    exist_flag = db.query(q.exists()).scalar()
    
    # If there does not exist such alarm, return False and message
    if not exist_flag:
        return False, f"You have not setup such an alarm: {hour}:{minute} on {date}, repeat: {repeat}\n"
    
    tp_index = q.first()[0]
    # step-2: add user_id, alarm_id and repeat
    q = db.query(UserAlarm.user_id).filter(UserAlarm.user_id==user_id, UserAlarm.alarm_id==tp_index)
    exist_flag = db.query(q.exists()).scalar()
    # print(f"User Alarm {user_id}-{tp_index} exist? {exist_flag}")
    if exist_flag:
        delete_stmt = delete(UserAlarm).where(UserAlarm.user_id == user_id, UserAlarm.alarm_id==tp_index)
        print(delete_stmt)
        db.execute(delete_stmt)
        db.commit()
        message = f"successfully removed alarm: {hour}:{minute} on {date}, repeat: {repeat}\n"
        return True, message
    else:
        return False, f"You have not setup such an alarm: {hour}:{minute} on {date}, repeat: {repeat}\n"
