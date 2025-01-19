import functools
import datetime
from typing import (
    Dict, Union
)
import flask
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app, Response, jsonify
)
from werkzeug.security import check_password_hash, generate_password_hash
from flaskr.questionnaire import NasatlxForm, PlanningForm, ExpertiseForm, planning_form, FeedbackForm, TiA_Form, ExecutionForm, QualificationForm_1, QualificationForm_2
from flaskr.db_utli import save_user_info, save_user_choice, save_event, save_user_feedback, save_user_trust
from flaskr.form_util import submit_form
from flaskr.agents.executor.agent_executor import (
    load_agent_executor,
)
from flaskr.agents.plan_and_execute import StepWiseExecution

import os
import re
import pandas as pd
import numpy as np
import json
# from langchain_community.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain_core.agents import AgentAction, AgentFinish
from dotenv import load_dotenv
load_dotenv()

plan_bp = Blueprint('planning_agent', __name__, url_prefix='/planning_agent')

success_link = "https://app.prolific.com/submissions/complete?cc=CUYUONYC"
failure_link = "https://app.prolific.com/submissions/complete?cc=CZVOBZ23"
screenout_link = "https://app.prolific.com/submissions/complete?cc=CKXKN85J"

def get_llm():
    # create a llm
    if 'llm' not in g:

        # for langchain-openai:
        g.llm = ChatOpenAI(
            openai_api_key=os.environ["OPENAI_API_KEY"],
            verbose=False,
            streaming=True,
            temperature=0.7,
        )
        # langchain_community.chat_models.ChatOpenAI
        # ChatOpenAI(
        #     openai_api_key=os.environ["OPENAI_API_KEY"],
        #     verbose=False,
        #     streaming=True,
        #     temperature=0.7,
        # )

    return g.llm

def check_plan(tp_plan):
    new_plan = []
    for step in tp_plan:
        plan_text = step["step"]
        index = plan_text.split(" ")[0]
        plan_text = plan_text[len(index)+1:]
        if len(index.split(".")) == 3:
            # x.y.z
            data_level = 3
        elif index[-1] == ".":
            # x.
            data_level = 1
        else:
            # x.y
            data_level = 2
        tp_obj = {
            "step": plan_text,
            "data_level": data_level,
            "index": index
            # "tool": step["tool"]
        }
        new_plan.append(tp_obj)
    return new_plan

class PlanningDataset(object):

    def __init__(self, tp_task):
        self.task_id = tp_task['id']
        self.plan = check_plan(tp_task['plan'])
        # self.tools = tp_task['tools']
        self.task_query = tp_task['question']
        self.domain = tp_task["domain"]
        self.ground_truth = tp_task['plan']

    def print_generation_task(self):
        task_str = ""
        task_str += "Task %s: %s"%(self.task_id, self.task_query)
        task_str += ", with label %s"%(self.prediction)
        task_str += ", with ground truth %s"%(self.ground_truth)
        return task_str

    def serize(self):
        return {
            "task_id": self.task_id,
            "plan": self.plan,
            # "tools": self.tools,
            "task_query": self.task_query,
            "ground_truth": self.ground_truth,
            "domain": self.domain
        }

def load_data(filename="flaskr/static/data/UltraTool/dev.json"):
    f = open(filename)
    # task_list = []
    # for line in f:
    #     task_obj = json.loads(line)
    #     task_list.append(task_obj)
    # f.close()
    task_list = json.load(f)
    f.close()
    data_dict = {}
    task_ID_list = []
    for index, task_obj in enumerate(task_list):
        # try:
        # task_obj["id"] = "dev-{}".format(index)
        tp_data = PlanningDataset(task_obj)
        # except:
        #     print(task_list[i]['id'], "is not executed correctly, to check")
        #     continue
        task_id = str(tp_data.task_id)
        data_dict[task_id] = tp_data
        if task_id in ["onbarding-example", "onbarding-auto"]:
            # We skip the example task in formal task list
            continue
        task_ID_list.append(task_id)
        # if index >= 10:
        #     break
    # print(data_dict['T003'].print_generation_task())
    return task_ID_list, data_dict

# filename = "flaskr/static/data/UltraTool/selected_example_new.json"
filename = "flaskr/static/data/UltraTool/simplified_example_original.json"
task_ID_list, planning_task_dict = load_data(filename)

from flaskr.agents.planner.agent import PlanningOutputParser
parser = PlanningOutputParser()
user_agent_execution: Dict[str, StepWiseExecution] = {}
user_chat_history = {}

from flaskr.api.finance_tool import finance_initilize
from flaskr.api.restaurant_tool import initialize_restaurant
def initiliaze_user(user_id:str):
    finance_initilize(user_id=user_id)
    initialize_restaurant(user_id=user_id)


# To-do: create DB initial operations when user start the tasks
@plan_bp.route('/user_port', methods=['GET', 'POST'])
def user_port():
    user_id = request.args.get('PROLIFIC_PID')
    # To-do: recognize participated users, and ask them to leave
    # we may record the time user enter our web app
    # show the user profile for that user
    session['user_id'] = user_id
    session['task_id'] = 0
    session['var_list'] = []
    session['attention_chck_right'] = 0
    session['attention_chck_fail'] = 0
    session['condition'] = "pilot_check"
    session['plan'] = None
    # temp_task_ID_list = ['test-200', 'test-271', 'test-497']
    temp_task_ID_list = task_ID_list
    session['attention_check'] = np.random.randint(low=1,high=len(temp_task_ID_list))
    
    # tp_task_ID_list = np.random.permutation(task_ID_list).tolist()
    tp_task_ID_list = np.random.permutation(temp_task_ID_list).tolist()
    session['task_ID_list'] = tp_task_ID_list
    initiliaze_user(user_id=user_id)
    # session['check_pass'] = False
    # session['check_pass_2'] = False
    # print(tp_task_ID_list)
    # current_app.logger.info("User {} log in, test it".format(user_id))
    exist_flag = save_user_info(user_id=user_id, user_task_order=tp_task_ID_list, user_group="pilot_check")
    # return redirect(url_for("planning_agent.instruction"))
    return redirect(url_for("planning_agent.instruction"))

@plan_bp.route('/user_port_1', methods=['GET', 'POST'])
def user_port_1():
    user_id = request.args.get('PROLIFIC_PID')
    # To-do: recognize participated users, and ask them to leave
    # we may record the time user enter our web app
    # show the user profile for that user
    session['user_id'] = user_id
    session['task_id'] = 0
    session['var_list'] = []
    session['attention_chck_right'] = 0
    session['attention_chck_fail'] = 0
    session['condition'] = "AP-AE"
    # Automatic Planning, Automatic Execution
    session['plan'] = None
    # temp_task_ID_list = ['test-200', 'test-271', 'test-497']
    temp_task_ID_list = task_ID_list
    session['attention_check'] = np.random.randint(low=1,high=len(temp_task_ID_list))
    
    # tp_task_ID_list = np.random.permutation(task_ID_list).tolist()
    tp_task_ID_list = np.random.permutation(temp_task_ID_list).tolist()
    session['task_ID_list'] = tp_task_ID_list
    initiliaze_user(user_id=user_id)
    # session['check_pass'] = False
    # session['check_pass_2'] = False
    # print(tp_task_ID_list)
    current_app.logger.info("User {} log in, test it".format(user_id))
    exist_flag = save_user_info(user_id=user_id, user_task_order=tp_task_ID_list, user_group="pilot_check")
    # return redirect(url_for("planning_agent.instruction"))
    return redirect(url_for("planning_agent.instruction"))


@plan_bp.route('/user_port_2', methods=['GET', 'POST'])
def user_port_2():
    user_id = request.args.get('PROLIFIC_PID')
    session['user_id'] = user_id
    session['task_id'] = 0
    session['var_list'] = []
    session['attention_chck_right'] = 0
    session['attention_chck_fail'] = 0
    session['condition'] = "AP-UE"
    session['plan'] = None
    # temp_task_ID_list = ['test-200', 'test-271', 'test-497']
    temp_task_ID_list = task_ID_list
    session['attention_check'] = np.random.randint(low=1,high=len(temp_task_ID_list))
    
    tp_task_ID_list = np.random.permutation(temp_task_ID_list).tolist()
    session['task_ID_list'] = tp_task_ID_list
    initiliaze_user(user_id=user_id)
    # session['check_pass'] = False
    # session['check_pass_2'] = False
    # current_app.logger.info("User {} log in, test it".format(user_id))
    exist_flag = save_user_info(user_id=user_id, user_task_order=tp_task_ID_list, user_group="pilot_check")
    return redirect(url_for("planning_agent.instruction"))


@plan_bp.route('/user_port_3', methods=['GET', 'POST'])
def user_port_3():
    user_id = request.args.get('PROLIFIC_PID')
    session['user_id'] = user_id
    session['task_id'] = 0
    session['var_list'] = []
    session['attention_chck_right'] = 0
    session['attention_chck_fail'] = 0
    session['condition'] = "UP-AE"
    session['plan'] = None
    # temp_task_ID_list = ['test-200', 'test-271', 'test-497']
    temp_task_ID_list = task_ID_list
    session['attention_check'] = np.random.randint(low=1,high=len(temp_task_ID_list))
    
    # tp_task_ID_list = np.random.permutation(task_ID_list).tolist()
    tp_task_ID_list = np.random.permutation(temp_task_ID_list).tolist()
    session['task_ID_list'] = tp_task_ID_list
    initiliaze_user(user_id=user_id)
    # session['check_pass'] = False
    # session['check_pass_2'] = False
    # current_app.logger.info("User {} log in, test it".format(user_id))
    exist_flag = save_user_info(user_id=user_id, user_task_order=tp_task_ID_list, user_group="pilot_check")
    return redirect(url_for("planning_agent.instruction"))

@plan_bp.route('/user_port_4', methods=['GET', 'POST'])
def user_port_4():
    user_id = request.args.get('PROLIFIC_PID')
    session['user_id'] = user_id
    session['task_id'] = 0
    session['var_list'] = []
    session['attention_chck_right'] = 0
    session['attention_chck_fail'] = 0
    session['condition'] = "UP-UE"
    session['plan'] = None
    # temp_task_ID_list = ['test-200', 'test-271', 'test-497']
    temp_task_ID_list = task_ID_list
    session['attention_check'] = np.random.randint(low=1,high=len(temp_task_ID_list))
    
    # tp_task_ID_list = np.random.permutation(task_ID_list).tolist()
    tp_task_ID_list = np.random.permutation(temp_task_ID_list).tolist()
    session['task_ID_list'] = tp_task_ID_list
    initiliaze_user(user_id=user_id)
    # session['check_pass'] = False
    # session['check_pass_2'] = False
    # current_app.logger.info("User {} log in, test it".format(user_id))
    exist_flag = save_user_info(user_id=user_id, user_task_order=tp_task_ID_list, user_group="pilot_check")
    return redirect(url_for("planning_agent.instruction"))



@plan_bp.route('/instruction', methods=['GET', 'POST'])
def instruction():
    form = ExpertiseForm()
    tp_condition = session['condition']
    if request.method == 'POST':
        user_id = session['user_id']
        llm_expertise = form.llm_expertise.data
        assistant_expertise = form.assistant_expertise.data
        save_event(user_id, "llm_expertise", llm_expertise)
        save_event(user_id, "assistant_expertise", assistant_expertise)
        return redirect(url_for('planning_agent.intro'))

    return render_template('planning_agent/instruction.html', condition=tp_condition, form=form)

@plan_bp.route('/intro', methods=['GET', 'POST'])
def intro():
    tp_condition = session['condition']
    if request.method == 'POST':
        return redirect(url_for('planning_agent.intro_plan'))

    return render_template('planning_agent/intro.html', condition=tp_condition)

@plan_bp.route('/intro_plan', methods=['GET', 'POST'])
def intro_plan():
    tp_condition = session['condition']
    if tp_condition.startswith("AP"):
        # a correct plan
        tp_task_ID = 'onbarding-auto'
    else:
        # a task with necessary edits
        tp_task_ID = 'onbarding-example'
    tp_data = planning_task_dict[tp_task_ID].serize()
    tp_query = tp_data["task_query"]
    tp_plan = tp_data["plan"]
    potential_actions = get_potential_actions(tp_task_ID)
    if request.method == 'POST':
        return redirect(url_for('planning_agent.intro_execution'))
    if tp_condition.startswith("AP"):
        # AP-AE, AP-UE
        html_path = "planning_agent/intro_plan_auto.html"
    else:
        # UP-AE, UP-UE, pilot-check
        html_path = "planning_agent/intro_plan.html"
    return render_template(html_path, condition=tp_condition, tp_query=tp_query, tp_plan=tp_plan, action_list=potential_actions)


# @plan_bp.route('/example_plan', methods=['GET', 'POST'])
# def example_plan():
#     form = PlanningForm()
#     tp_task_ID = 'test-113'
#     tp_data = planning_task_dict[tp_task_ID].serize()
#     tp_query = tp_data["task_query"]
#     tp_plan = tp_data["plan"]
#     potential_actions = get_potential_actions(tp_task_ID)
#     # To ensure previous tasks will not affect current task plan
#     session['plan'] = None
#     if request.method == 'POST':
#         user_id = session['user_id']
#         return redirect(url_for('planning_agent.intro_execution'))

#     return render_template('planning_agent/example_plan.html', form = form, tp_query=tp_query, tp_plan=tp_plan, action_list=potential_actions)

@plan_bp.route('/intro_execution', methods=['GET', 'POST'])
def intro_execution():
    tp_condition = session['condition']
    if request.method == 'POST':
        return redirect(url_for('planning_agent.example_execution'))
    if tp_condition.endswith("AE"):
        # AP-AE, UP-AE
        html_path = "planning_agent/intro_execution_auto.html"
    else:
        # AP-UE, UP-UE, pilot-check
        html_path = "planning_agent/intro_execution.html"
    return render_template(html_path, condition=tp_condition)

@plan_bp.route('/qualification_test', methods=['GET', 'POST'])
def qualification_test():
    tp_condition = session['condition']
    if tp_condition.startswith("AP"):
        # For conditions with automatic planning
        form = QualificationForm_2()
    else:
        # For conditions with user-involved planning
        form = QualificationForm_1()
    if request.method == 'POST':
        answer_1 = form.question_1.data
        answer_2 = form.question_2.data
        if answer_1 == '1' and answer_2 == '3':
            return redirect(url_for('planning_agent.planning'))
        else:
            return redirect(screenout_link)

    return render_template('planning_agent/qualification_test.html', condition=tp_condition, form=form)


@plan_bp.route('/example_execution', methods=['GET', 'POST'])
def example_execution():
    form = ExecutionForm()
    tp_condition = session['condition']
    if tp_condition.startswith("AP"):
        tp_task_ID = 'onbarding-auto'
    else:
        tp_task_ID = 'onbarding-example'
    user_id = session['user_id']
    if request.method == 'POST':
        # after the current task, delete the agent execution class
        if user_id in user_agent_execution:
            del user_agent_execution[user_id]
        # Shall we save the example interactions?
        save_user_actions(user_id=user_id, task_id="example|" + tp_task_ID, feedback_type="action")
        user_trust = form.correctness.data
        user_confidence = form.confidence.data
        save_user_choice(user_id, task_id=tp_task_ID, choice=user_trust, answer_type="trust_execution")
        save_user_choice(user_id, task_id=tp_task_ID, choice=user_confidence, answer_type="confidence_execution")
        # reset the task_id
        session['task_id'] = 0
        # formally starting the tasks
        # Or we can add one qualification test
        return redirect(url_for('planning_agent.qualification_test'))
    tp_data = planning_task_dict[tp_task_ID].serize()
    # print(tp_data.keys())
    tp_query = tp_data["task_query"]
    # based on user input in the previous page, we may have update plan
    if "plan" not in session or session['plan'] is None or tp_condition.startswith("AP"):
        # Case 1: session['plan'] is not updated or null
        # Case 2: it's condition with automatic planning
        new_plan = tp_data["plan"]
    else:
        # only take plan user-edited plan in condition with user-involved planning
        new_plan = session["plan"]
    steps_list = []
    for item in new_plan:
        tp_index = item["index"]
        tp_step = item["step"]
        steps_list.append(f"{tp_index} {tp_step}")
    new_plan_str = "\n".join(steps_list)
    # session['plan'] = new_plan_str
    tp_plan = new_plan_str
    # print(tp_plan)
    # create a step-wise execution for this session
    if user_id in user_agent_execution:
        del user_agent_execution[user_id]
    if user_id in user_chat_history:
        del user_chat_history[user_id]
    # renew user_agent_execution
    llm = get_llm()
    tools = get_task_tools(tp_task_ID)
    # use chat history will change the prompt structure in the agent executor
    executor = load_agent_executor(llm, tools, verbose=True, 
                                   use_chat_history=True, include_task_in_prompt=True)
    # define the step-wise execution class
    agent = StepWiseExecution(executor=executor, 
                              task=tp_query, 
                              user_id=user_id, 
                              use_chat_history=True)
    plan = parser.parse(tp_plan)
    # assign plan to the step-wise execution
    agent.assign_plan(plan)
    # initialize the execution agent with plan
    user_agent_execution[user_id] = agent
    # initialize user chat history
    user_chat_history[user_id] = []

    # special case for the example
    session['task_id'] = -1

    # It seems the execution agent can't be associated with one session, how can we solve it?
    # Now we used a global dict to manage it, to further check
    if tp_condition.endswith("AE"):
        # Automatic Execution
        # AP-AE, UP-AE
        html_path = "planning_agent/execution_auto.html"
    else:
        # User-involved Execution
        # AP-UE, UP-UE, pilot-check
        html_path = "planning_agent/execution_page.html"
    potential_actions = get_potential_actions(tp_task_ID)
    return render_template(html_path, task_index=0, task_total=len(task_ID_list), tp_query = tp_query, tp_plan=tp_plan, form=form, action_list=potential_actions)

@plan_bp.route('/show_task', methods=['GET', 'POST'])
def show_task():
    form = PlanningForm()
    tp_task_ID = request.args.get('task_id')
    tp_data = planning_task_dict[tp_task_ID].serize()
    session['user_id'] = 'User XYZ'
    session['task_id'] = 0
    session['condition'] = "pilot_check"
    session['task_ID_list'] = [tp_task_ID]
    session['attention_check'] = 1
    tp_query = tp_data["task_query"]
    tp_plan = tp_data["plan"]
    session['task_id_test'] = tp_task_ID
    initiliaze_user(user_id='User XYZ')
    # if planning_task_dict[tp_task_ID].domain == "Travel":
    #     session['task_id'] = session['task_id'] + 1
    # skip travel now
    # tp_tools = tp_data["tools"]
    if request.method == 'POST':
        return redirect(url_for('planning_agent.planning_auto'))

    potential_actions = get_potential_actions(tp_task_ID)
    print(potential_actions)
    return render_template('planning_agent/task_show.html', task_index=0, task_total=len(task_ID_list), form=form, tp_query=tp_query, tp_plan=tp_plan, action_list = potential_actions)

from flaskr.agents.planner.agent import plan_split
@plan_bp.route('/updateplan', methods=['POST'])
def updateplan():
    user_id = session['user_id']
    task_id = session['task_id']
    task_ID_list = session['task_ID_list']
    tp_task_ID = task_ID_list[task_id]
    new_plan = request.get_json()['plan']
    steps_list = []
    for item in new_plan:
        tp_index = item["index"]
        tp_step = item["step"]
        steps_list.append(f"{tp_index} {tp_step}")
    new_plan_str = "\n".join(steps_list)
    # session['plan'] = new_plan_str
    session['plan'] = new_plan
    # parser.parse_ori(new_plan_str)
    # print(new_plan_str)
    # print(session['plan'])
    # print(type(new_plan_str), len(new_plan_str))
    # save_user_plan(user_id, tp_task_ID, new_plan_str)
    save_user_feedback(user_id=user_id, task_id=tp_task_ID, content=new_plan_str, feedback_type="plan")
    print("save new plan successfully")
    # print(tp_task_ID, new_plan)
    return ('', 204)
    # Response(status=204)

@plan_bp.route('/action_recording', methods=['POST'])
def action_recording():
    user_id = session['user_id']
    # task_id = session['task_id']
    # task_ID_list = session['task_ID_list']
    # tp_task_ID = task_ID_list[task_id]
    user_action = request.get_json()['action']
    action_parameters = request.get_json()['action_input']
    if user_action == "attention_check":
        user_choice = action_parameters["button"]
        if user_choice != "Reflection":
            session['attention_chck_fail'] += 1
            if session['attention_chck_fail'] >= 2:
                return redirect(failure_link)
    tp_user_action = {
        "action_event": user_action,
        "action_parameters": action_parameters
    }
    if user_action == "task_end":
        # record the whole conversation from the frontend
        task_id = session['task_id']
        task_ID_list = session['task_ID_list']
        tp_task_ID = task_ID_list[task_id]
        json_str = json.dumps(action_parameters)
        save_user_feedback(user_id=user_id, task_id=tp_task_ID, content=json_str, feedback_type="conversation")
    else:
        # record the actions in structured manner
        if user_id not in user_chat_history:
            user_chat_history[user_id] = []
        user_chat_history[user_id].append(tp_user_action)
        # print("user action recorded")
    return ('', 204)
    # Response(status=204)

@plan_bp.route('/planning_auto', methods=['GET', 'POST'])
def planning_auto():
    form = PlanningForm()
    tp_condition = session['condition']
    task_id = session['task_id']
    task_ID_list = session['task_ID_list']
    tp_task_ID = task_ID_list[task_id]
    # tp_task_ID = 'dev-0'
    tp_data = planning_task_dict[tp_task_ID].serize()
    tp_query = tp_data["task_query"]
    # tp_plan = tp_data["plan"]

    # if "plan" not in session or session['plan'] is None or tp_condition.startswith("AP"):
    if tp_condition.startswith('AP'):
        # Case 1: session['plan'] is not updated or null
        # Case 2: it's condition with automatic planning
        tp_plan = tp_data["plan"]
    else:
        # only take plan user-edited plan in condition with user-involved planning
        if session['plan'] is None:
            tp_plan = tp_data["plan"]
        else:
            tp_plan = session["plan"]
    # To ensure previous tasks will not affect current task plan
    # session['plan'] = None
    # if planning_task_dict[tp_task_ID].domain == "Travel":
    #     session['task_id'] = session['task_id'] + 1
    # skip travel now
    # tp_tools = tp_data["tools"]
    if request.method == 'POST':
        user_trust = form.correctness.data
        user_confidence = form.confidence.data
        user_id = session['user_id']
        save_user_choice(user_id, task_id=tp_task_ID, choice=user_trust, answer_type="trust_planning")
        save_user_choice(user_id, task_id=tp_task_ID, choice=user_confidence, answer_type="confidence_planning")
        # The plan is updated with update_plan function
        # parser.parse_ori(new_plan_str)
        # print(new_plan_str)
        # print(session['plan'])
        # print(type(new_plan_str), len(new_plan_str))
        return redirect(url_for('planning_agent.execution'))
    potential_actions = get_potential_actions(tp_task_ID)
    html_path = "planning_agent/planning_auto.html"
    return render_template(html_path, task_index=task_id + 1, task_total=len(task_ID_list), form = form, tp_query=tp_query, tp_plan=tp_plan, action_list=potential_actions)

@plan_bp.route('/planning', methods=['GET', 'POST'])
def planning():
    tp_condition = session['condition']
    # To ensure previous tasks will not affect current task plan
    # Refresh will also clear the plan
    session['plan'] = None
    # redirect auto_planning, directly to next page
    if tp_condition.startswith("AP"):
        return redirect(url_for('planning_agent.planning_auto'))
    form = planning_form()
    task_id = session['task_id']
    task_ID_list = session['task_ID_list']
    tp_task_ID = task_ID_list[task_id]
    # tp_task_ID = 'dev-0'
    tp_data = planning_task_dict[tp_task_ID].serize()
    tp_query = tp_data["task_query"]
    tp_plan = tp_data["plan"]
    # if planning_task_dict[tp_task_ID].domain == "Travel":
    #     session['task_id'] = session['task_id'] + 1
    # skip travel now
    # tp_tools = tp_data["tools"]
    if request.method == 'POST':
        user_id = session['user_id']
        save_user_actions(user_id, tp_task_ID, feedback_type="planning")
        # After user involve in the planning phase, we show plan again and assess trust and confidence
        return redirect(url_for('planning_agent.planning_auto'))
    # initialize user chat history for planning
    user_chat_history[user_id] = []
    potential_actions = get_potential_actions(tp_task_ID)
    html_path = "planning_agent/task_show.html"
    return render_template(html_path, task_index=task_id + 1, task_total=len(task_ID_list), form = form, tp_query=tp_query, tp_plan=tp_plan, action_list=potential_actions)

from flaskr.api.finance_tool import *
from flaskr.api.tracking_tool import *
from flaskr.api.restaurant_tool import *
from flaskr.api.flight_tool import *
from flaskr.api.repair_tool import *
from flaskr.api.alarm_tool import *
from flaskr.api.travel_tool import *
from langchain.tools import BaseTool


# We simplify the tool selection, we provide task-specific tool set
def get_task_tools(task_id: str) -> List[BaseTool]:
    # finance_tools = [bank_account_login, check_balance, buy_currency, sell_currency, search_card, 
    #                  check_credit_card_debt, check_deposite_product, loan_application, check_loan_status, 
    #                  pay_credit_card, check_credit_card_bills]
    flight_tools = [search_flight, book_flight]
    travel_tools = [travel_itinerary_planner, select_itinerary, hotel_suggestion]
    repair_tools = [search_service_provider, select_service_provider, appliance_repair_request, obtain_user_info]
    alarm_tools = [create_alarm, cancel_alarm]
    tracking_tools = [check_order_status, check_order_customer]
    restaurant_tools = [add_single_dish_to_order, add_multiple_dish_to_order, place_order, check_out]
    # print(task_id, planning_task_dict[task_id].domain)
    if planning_task_dict[task_id].domain == "Finance":
        if task_id == "test-113" or task_id == "onbarding-example" or task_id == "onbarding-auto" :
            finance_tools = [bank_account_login, check_balance]
        elif task_id == "test-149":
            finance_tools = [bank_account_login, check_balance, buy_currency, sell_currency]
        elif task_id == "test-184":
            finance_tools = [check_deposite_product, loan_application, check_loan_status]
        elif task_id == 'test_200':
            finance_tools = [search_card, bank_account_login, pay_credit_card, check_credit_card_bills]
        else:
            finance_tools = [bank_account_login, check_balance, buy_currency, sell_currency, search_card, 
                     check_credit_card_debt, check_deposite_product, loan_application, check_loan_status, 
                     pay_credit_card, check_credit_card_bills]
        return finance_tools
    elif planning_task_dict[task_id].domain == "Flight":
        return flight_tools
    elif planning_task_dict[task_id].domain == "Travel":
        return travel_tools
    elif planning_task_dict[task_id].domain == "Repair":
        return repair_tools
    elif planning_task_dict[task_id].domain == "Alarm":
        return alarm_tools
    elif planning_task_dict[task_id].domain == "Tracking":
        return tracking_tools
    elif planning_task_dict[task_id].domain == "Restaurant":
        return restaurant_tools
    else:
        raise NotImplementedError(f"No tools implemented for task {task_id}")

@plan_bp.route('/cur_step', methods=['POST'])
def cur_step():
    task_id = session['task_id']
    task_ID_list = session['task_ID_list']
    tp_task_ID = task_ID_list[task_id]
    # tp_task_ID = 'dev-0'
    user_id = session['user_id']
    tp_data = planning_task_dict[tp_task_ID].serize()
    # print(tp_data.keys())
    # print("Entering One step")
    tp_query = tp_data["task_query"]
    tp_step = user_agent_execution[user_id].get_cur_step()
    data = {
        "query": tp_query,
        "step": tp_step
    }
    print(tp_query)
    print(tp_step)
    # print(data)
    return jsonify(data)

def save_user_actions(user_id:str, task_id:str, feedback_type:str="action"):
    if user_id in user_chat_history:
        tp_history = user_chat_history[user_id]
        json_str = json.dumps(tp_history)
        # dump the list to json str
        save_user_feedback(user_id=user_id, task_id=task_id, content=json_str, feedback_type="action")
        # after saving the current user action list, we delete it
        del user_chat_history[user_id]

@plan_bp.route('/execution', methods=['GET', 'POST'])
def execution():
    form = ExecutionForm()
    task_id = session['task_id']
    task_ID_list = session['task_ID_list']
    tp_condition = session['condition']
    tp_task_ID = task_ID_list[task_id]
    # tp_task_ID = 'dev-0'
    user_id = session['user_id']
    if request.method == 'POST':
        session['task_id'] = session['task_id'] + 1
        # after the current task, delete the agent execution class
        if user_id in user_agent_execution:
            del user_agent_execution[user_id]
        save_user_actions(user_id=user_id, task_id=tp_task_ID, feedback_type="action")
        user_trust = form.correctness.data
        user_confidence = form.confidence.data
        save_user_choice(user_id, task_id=tp_task_ID, choice=user_trust, answer_type="trust_execution")
        save_user_choice(user_id, task_id=tp_task_ID, choice=user_confidence, answer_type="confidence_execution")
        if session['task_id'] == len(task_ID_list):
            # return render_template('thanks.html', reason_str="Thanks for your efforts!")
            # Users finished all tasks, enter post-task questionnaire
            return redirect(url_for('planning_agent.nasatlx'))
        return redirect(url_for('planning_agent.planning'))
    tp_data = planning_task_dict[tp_task_ID].serize()
    # print(tp_data.keys())
    tp_query = tp_data["task_query"]
    # based on user input in the previous page, we may have update plan
    if "plan" not in session or session['plan'] is None or tp_condition.startswith("AP"):
        # Case 1: session['plan'] is not updated or null
        # Case 2: it's condition with automatic planning
        new_plan = tp_data["plan"]
    else:
        # only take plan user-edited plan in condition with user-involved planning
        new_plan = session["plan"]
    steps_list = []
    for item in new_plan:
        tp_index = item["index"]
        tp_step = item["step"]
        steps_list.append(f"{tp_index} {tp_step}")
    new_plan_str = "\n".join(steps_list)
    # session['plan'] = new_plan_str
    tp_plan = new_plan_str
    # print(tp_plan)
    # create a step-wise execution for this session
    if user_id in user_agent_execution:
        del user_agent_execution[user_id]
    if user_id in user_chat_history:
        del user_chat_history[user_id]
    # renew user_agent_execution
    llm = get_llm()
    tools = get_task_tools(tp_task_ID)
    # use chat history will change the prompt structure in the agent executor
    executor = load_agent_executor(llm, tools, verbose=True, 
                                   use_chat_history=True, include_task_in_prompt=True)
    # define the step-wise execution class
    agent = StepWiseExecution(executor=executor, 
                              task=tp_query, 
                              user_id=user_id, 
                              use_chat_history=True)
    plan = parser.parse(tp_plan)
    # assign plan to the step-wise execution
    agent.assign_plan(plan)
    # initialize the execution agent with plan
    user_agent_execution[user_id] = agent
    # initialize user chat history
    user_chat_history[user_id] = []

    # It seems the execution agent can't be associated with one session, how can we solve it?
    # Now we used a global dict to manage it, to further check
    if tp_condition.endswith("AE"):
        # AP-AE, UP-AE
        html_path = 'planning_agent/execution_auto.html'
    else:
        # AP-UE, UP-UE, pilot-check
        html_path = 'planning_agent/execution_page.html'
    potential_actions = get_potential_actions(tp_task_ID)
    return render_template(html_path, task_index=task_id + 1, task_total=len(task_ID_list), tp_query = tp_query, tp_plan=tp_plan, form=form, action_list=potential_actions)

from flaskr.agents.util import ThreadedGenerator, ChainStreamHandler
from flaskr.agents.streaming import TokenByTokenHandler

# handler = TokenByTokenHandler(tags_of_interest=["agent_llm"])

# define the generation of one step in a llm thread, callback will stream the output
# To check what the output of callbacks here
# def llm_thread(g, user_id, tp_query, userInput):
#     agent = user_agent_execution[user_id]
#     # print("Entering LLM Thread")
#     try:
#         if userInput == "None":
#             agent.one_step_first(inputs={"input": tp_query}, 
#                            callbacks=[TokenByTokenHandler(tags_of_interest=["agent_llm"], gen=g)])
#         else:
#             reflection = [("human", userInput)]
#             # It's an optional parameter to the chat history
#             # the execution will be traced back to last step
#             agent.revise_step(inputs={"input": tp_query, "reflection":reflection}, 
#                            callbacks=[TokenByTokenHandler(tags_of_interest=["agent_llm"], gen=g)])
#     finally:
#         g.close()

# def execution_thread(g, user_id, tp_query, actions:List[AgentAction]=None):
#     agent = user_agent_execution[user_id]
#     # print("Entering LLM Thread")
#     try:
#         agent.one_step_second(
#             inputs = {"input": tp_query},
#             actions=actions, 
#             callbacks=[TokenByTokenHandler(tags_of_interest=["agent_llm"], gen=g)]
#         )
#     finally:
#         g.close()

def get_potential_actions(tp_task_ID):
    tools = get_task_tools(tp_task_ID)
    # tp_task_ID = 'dev-0'
    
    potential_actions = []
    for tool in tools:
        tp_dict = {
            "tool_name": tool.name,
            "description": tool.description.split(" - ")[1],
            "schema": tool.args
        }
        potential_actions.append(tp_dict)
    return potential_actions

@plan_bp.route('/potential_actions', methods=['POST'])
def potential_actions():
    task_id = session['task_id']
    if task_id >= 0:
        task_ID_list = session['task_ID_list']
        tp_task_ID = task_ID_list[task_id]
    else:
        tp_condition = session['condition']
        if tp_condition.startswith("AP"):
            # a correct plan
            tp_task_ID = 'onbarding-auto'
        else:
            # a task with necessary edits
            tp_task_ID = 'onbarding-example'
    # tp_task_ID = 'dev-0'
    
    potential_actions = get_potential_actions(tp_task_ID)

    data = {
        "actions": potential_actions
    }
    return jsonify(data)

def parse_action_prediction_output(actions: Union[str, List[AgentAction], AgentFinish]):
    if isinstance(actions, str):
        data = {
            "message": "execution done"
        }
    elif isinstance(actions, AgentFinish):
        tp_log = actions.log
        if "action" in tp_log and "action_input" in tp_log:
            # print(tp_log)
            predicted_action = json.loads(tp_log)
            data = {
                "tool_name": predicted_action["action"],
                "tool_input": predicted_action["action_input"],
                "log": '```\n' + actions.log + '\n```'
            }
        else:
            data = {
                "tool_name": "Agent Finish",
                "tool_input": {},
                "log": 'This is one special event, the LLM Assistance fails to figure out one specific action. Please specify one action manually. ```\n' + actions.log + '\n```'
            }
    else:
        # get predicted actions from LLM Agent
        predicted_action = actions[0]
        data = {
            "tool_name": predicted_action.tool,
            "tool_input": predicted_action.tool_input,
            "log": predicted_action.log
        }
    return jsonify(data)

@plan_bp.route('/action_prediction', methods=['POST'])
def action_prediction():
    user_id = session['user_id']
    
    task_id = session['task_id']
    task_ID_list = session['task_ID_list']
    tp_task_ID = task_ID_list[task_id]
    # tp_task_ID = 'dev-0'
    tp_data = planning_task_dict[tp_task_ID].serize()
    tp_query = tp_data["task_query"]

    # determine whether it's reflection / step-back
    data_dict = request.get_json()
    userInput = data_dict['message']
    mode = data_dict['mode'] # prediction | step_back | reflection

    if mode == "prediction":
        inputs = {"input": tp_query}
    else:
        inputs = {"input": tp_query, "reflection": userInput}

    agent = user_agent_execution[user_id]
    if mode == "step_back":
        # after execution of one step, user give feedback to re-try
        agent.step_back()
    actions = agent.one_step_first(inputs=inputs, callbacks=None)
    return parse_action_prediction_output(actions)

@plan_bp.route('/action_execution', methods=['POST'])
def action_execution():
    user_id = session['user_id']
    data_dict = request.get_json()
    tool_name = data_dict['tool_name']
    input_variables = data_dict['tool_input']
    tp_step = user_agent_execution[user_id].get_cur_step()
    # shall we create one string based on the action, we can further check
    actions = [AgentAction(
        tool_name, input_variables, tp_step
    )]
    # now we only support single action from user
    task_id = session['task_id']
    task_ID_list = session['task_ID_list']
    tp_task_ID = task_ID_list[task_id]
    # tp_task_ID = 'dev-0'
    tp_data = planning_task_dict[tp_task_ID].serize()
    # print(tp_data.keys())
    # print("Entering One step")
    tp_query = tp_data["task_query"]
    agent = user_agent_execution[user_id]
    execution_res = agent.one_step_second(inputs={"input": tp_query}, actions=actions, callbacks=None)
    # now we conduct attention check after the execution of the first step of one task
    if task_id + 1 == session['attention_check'] and agent.exec_index == 1:
        execution_res["attention_check"] = True
    else:
        execution_res["attention_check"] = False
    return jsonify(execution_res)

@plan_bp.route('/TiA_postq', methods=('GET', 'POST'))
def TiA_postq():
    form = TiA_Form()
    if request.method == 'POST' and form.validate_on_submit():
        user_id = session['user_id']
        # current_app.logger.info("User {} filled in TiA post-questionnaire".format(user_id))
        answer_dict = {"user_id": user_id}
        for i in range(19):
            tp_key = 'answer_{}'.format(i + 1)
            answer_dict[tp_key] = getattr(form, tp_key).data
        tp_choice = form.answer_20.data
        save_user_choice(user_id, task_id="TiA_attention", choice=tp_choice, answer_type="attention")
        if tp_choice == '1':
            session['attention_chck_right'] += 1
        else:
            session['attention_chck_fail'] += 1
            if session['attention_chck_fail'] >= 2:
                return redirect(failure_link)
        save_user_trust(answer_dict=answer_dict, user_id=user_id)
        # current_app.logger.info("User {}'s data is saved into database, then move to post-task questionaire".format(user_id))
        return redirect(url_for('planning_agent.open_feedback'))
        # flash(error)
    return render_template('questionnaire/TiA_post.html', form=form)

@plan_bp.route('/nasatlx', methods=['GET', 'POST'])
def nasatlx():
    form = NasatlxForm()
    if request.method == 'POST' and form.validate_on_submit():
        user_id = session['user_id']
        error = None
        mental_demand = form.mental_demand.data
        physical_demand = form.physical_demand.data
        temporal_demand = form.temporal_demand.data
        performance = form.performance.data
        effort = form.effort.data
        frustration = form.frustration.data
        save_event(user_id, "mental_demand", mental_demand)
        save_event(user_id, "physical_demand", physical_demand)
        save_event(user_id, "temporal_demand", temporal_demand)
        save_event(user_id, "performance", performance)
        save_event(user_id, "effort", effort)
        save_event(user_id, "frustration", frustration)
        # the whole process finished and we give back completion code
        # return redirect(url_for('thanks'))
        # return render_template('thanks.html', form=form)
        return redirect(url_for('planning_agent.TiA_postq'))
        # return render_template('thanks.html', reason_str="Thanks for your efforts!")
        # Replace with the Prolific link

        flash(error)
    return render_template('questionnaire/nasatlx.html', form=form)

@plan_bp.route('/open_feedback', methods=['GET', 'POST'])
def open_feedback():
    form = FeedbackForm()
    if request.method == 'POST' and form.validate_on_submit():
        user_id = session['user_id']
        error = None
        planning_feedback = form.planning_feedback.data
        execution_feedback = form.execution_feedback.data
        other_feedback = form.other_feedback.data
        save_user_feedback(user_id=user_id, task_id='task_end', content=planning_feedback, feedback_type="planning")
        save_user_feedback(user_id=user_id, task_id='task_end', content=execution_feedback, feedback_type="execution")
        save_user_feedback(user_id=user_id, task_id='task_end', content=other_feedback, feedback_type="other")
        # the whole process finished and we give back completion code
        # return redirect(url_for('thanks'))
        # return render_template('thanks.html', form=form)
        return redirect(success_link)
        # return render_template('thanks.html', reason_str="Thanks for your efforts!")
        # Replace with the Prolific link

        flash(error)
    return render_template('questionnaire/feedback_llm_agent.html', form=form)

# @plan_bp.route('/chat1')
# def chat1():
#     return render_template('planning_agent/chat.html')

