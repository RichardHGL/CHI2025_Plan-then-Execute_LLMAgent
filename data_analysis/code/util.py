import json
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import csv
from calc_measures import calc_TiA_scale, compare_action_seq_strict
from calc_measure_action_seq import evaluate_action_sequence
# task_ID_list_to_check = ['test-113', 'test-149', 'test-184', 'test-200', 'test-256', 'test-271', 'test-388', 'test-497', 'test-675', 'test-859']
task_ID_list_to_check = ['test-149', 'test-200', 'test-388', 'test-497', 'test-675', 'test-859']
task_order = ['test-149', 'test-200', 'test-859', 'test-388', 'test-497', 'test-675']
def collect_file_users(filename):
    # df = pd.read_csv(filename, usecols=['user_id'])
    df = pd.read_csv(filename, usecols=['userid'], quoting=csv.QUOTE_MINIMAL)
    user_list = df.values.tolist()
    user_set = set([item[0] for item in user_list])
    # f = open(filename)
    # f.readline()
    # user_set = set()
    # num_lines = 0
    # for line in f:
    # 	prolific_id = line.strip().split(",")[0]
    # 	user_set.add(prolific_id)
    # 	num_lines += 1
    print(filename, len(user_set))
    return user_set

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
filename = "../simplified_example_original.json"
task_ID_list, planning_task_dict = load_data(filename)
confidence_map = {
    "unconfident": 1,
    "somewhat unconfident": 2,
    "neutral": 3,
    "somewhat confident": 4,
    "confident": 5
}
def load_user_data(folder_name="../sample_data", reserved_users=None):
    user_open_feedback = {} # user -> feedback_type planning | execution | other
    user_task_action = {} # user -> task_id -> action_list in execution stage
    user_task_plan = {} # user -> task_id -> plan text
    user_task_confidence_dict = {} # user -> task_id -> planning|execution
    user_task_trust_dict = {} # user -> task_id -> planning|execution
    user_risk_perception = {} # user -> task_id -> risk
    user_attention_dict = {}
    user_task_conversation = {}
    user_task_precise_action = {}
    user_task_ai_suggestion = {}
    user2condition = {}
    user_planning_actions = {}
    user_task_order = {}
    user_expertise = {}
    user_cognitive_load = {}
    userinfo_dict = {}
    user_TiA_scale = {}

    def load_feedback(reserved_users=None):
        filename=os.path.join(folder_name, "userfeedback.csv")
        used_cols = ['user_id', 'task_id', 'feedback_type', 'user_feedback']
        df = pd.read_csv(filename, usecols=used_cols)
        if reserved_users is not None:
            # filter some invalid users
            df = df.drop(df[~df['user_id'].isin(reserved_users)].index)
        user_data_list = df.values.tolist()
        for user_id, task_id, feedback_type, user_feedback in user_data_list:
            if task_id == "task_end":
                # open_feedback, three types
                assert feedback_type in ["planning", "execution", "other"]
                if user_id not in user_open_feedback:
                    user_open_feedback[user_id] = {}
                user_open_feedback[user_id][feedback_type] = user_feedback
            elif task_id == "tutorial":
                assert feedback_type in ["planning", "execution", "other"]
            else:
                if feedback_type == "action":
                    if user_id not in user_task_action:
                        user_task_action[user_id] = {}
                    action_list = json.loads(user_feedback)
                    user_task_action[user_id][task_id] = action_list
                elif feedback_type == "plan":
                    user_plan = user_feedback
                    if user_id not in user_task_plan:
                        user_task_plan[user_id] = {}
                    user_task_plan[user_id][task_id] = user_plan
                elif feedback_type == "planning":
                    planning_actions = user_feedback
                    if user_id not in user_planning_actions:
                        user_planning_actions[user_id] = {}
                    user_planning_actions[user_id][task_id] = planning_actions
                elif feedback_type == "conversation":
                    if user_id not in user_task_conversation:
                        user_task_conversation[user_id] = {}
                    user_task_conversation[user_id][task_id] = user_feedback
                else:
                    raise NotImplementedError(f"Unknown feedback type: {feedback_type}")
    
    def load_user_choice(reserved_users=None):
        filename=os.path.join(folder_name, "usertask.csv")
        used_cols = ['user_id', 'task_id', 'answer_type', 'choice']
        df = pd.read_csv(filename, usecols=used_cols)
        if reserved_users is not None:
            # filter some invalid users
            df = df.drop(df[~df['user_id'].isin(reserved_users)].index)
        user_data_list = df.values.tolist()
        for user_id, task_id, answer_type, choice in user_data_list:
            if user_id not in user_task_trust_dict:
                user_task_trust_dict[user_id] = {}
            if task_id not in user_task_trust_dict[user_id]:
                user_task_trust_dict[user_id][task_id] = {}
            if user_id not in user_task_confidence_dict:
                user_task_confidence_dict[user_id] = {}
            if task_id not in user_task_confidence_dict[user_id]:
                user_task_confidence_dict[user_id][task_id] = {}
            if user_id not in user_risk_perception:
                user_risk_perception[user_id] = {}
            if answer_type == "trust_planning":
                user_task_trust_dict[user_id][task_id]["planning"] = choice
                # binary, Yes / No
            elif answer_type == "trust_execution":
                user_task_trust_dict[user_id][task_id]["execution"] = choice
                # binary, Yes / No
            elif answer_type == "confidence_execution":
                user_task_confidence_dict[user_id][task_id]["execution"] = confidence_map[choice]
                # binary, Yes / No
            elif answer_type == "confidence_planning":
                user_task_confidence_dict[user_id][task_id]["planning"] = confidence_map[choice]
            elif answer_type == "risk":
                user_risk_perception[user_id][task_id] = int(choice)
            elif answer_type == "attention":
                # TiA attention and qualification_2
                if user_id not in user_attention_dict:
                    user_attention_dict[user_id] = {}
                user_attention_dict[user_id][task_id] = int(choice)
            else:
                # if answer_type == "attention":
                #     # TiA attention
                #     if user_id not in user_attention_dict:
                #         user_attention_dict[user_id] = {}
                #     user_attention_dict[user_id][task_id] = int(choice)
                print(f"Answer type {answer_type} not handled")

    def load_plan_quality_evaluation(reserved_users=None):
        filename = os.path.join(folder_name, "user_plan_quality.csv")
        usecols = ['user_id', 'task_id', 'plan_quality']
        df = pd.read_csv(filename, usecols=usecols)
        df = pd.read_csv(filename, usecols=usecols)
        if reserved_users is not None:
            # filter some invalid users
            df = df.drop(df[~df['user_id'].isin(reserved_users)].index)
        user_status_list = df.values.tolist()
        plan_quality_evaluation = {}
        for user_id, task_id, plan_quality in user_status_list:
            if user_id not in plan_quality_evaluation:
                plan_quality_evaluation[user_id] = {}
            plan_quality_evaluation[user_id][task_id] = int(plan_quality)
        return plan_quality_evaluation

    def load_userinfo(reserved_users=None, required_condtions=None):
        filename = os.path.join(folder_name, "userinfo.csv")
        usecols = ['user_id', 'task_order_str', 'user_group', 'created_time']
        df = pd.read_csv(filename, usecols=usecols)
        if reserved_users is not None:
            # filter some invalid users
            df = df.drop(df[~df['user_id'].isin(reserved_users)].index)
        user_status_list = df.values.tolist()
        # userinfo_dict = {}
        # user_task_order = {}
        for user_id, task_order_str, user_group, created_time in user_status_list:
            if required_condtions is not None:
                if user_group not in required_condtions:
                    continue
            user2condition[user_id] = user_group
            user_task_order[user_id] = task_order_str.split("|")
        return userinfo_dict, user_task_order
    
    def load_expertise_cognitiveload(reserved_users=None, required_condtions=None):
        filename = os.path.join(folder_name, "userbehavior.csv")
        df = pd.read_csv(filename, usecols=['user_id', 'event_desc', 'user_behavior'])
        if reserved_users is not None:
            # filter some invalid users
            df = df.drop(df[~df['user_id'].isin(reserved_users)].index)
        user_data_list = df.values.tolist()
        # user_expertise = {}
        # user_cognitive_load = {}
        expertise_keys = ['llm_expertise', 'assistant_expertise']
        cognitive_load_keys = ['mental_demand', 'physical_demand', 'temporal_demand', 'performance', 'effort', 'frustration']
        for user_id, event_desc, user_behavior in user_data_list:
            if event_desc in cognitive_load_keys:
                if user_id not in user_cognitive_load:
                    user_cognitive_load[user_id] = {}
                user_cognitive_load[user_id][event_desc] = int(user_behavior)
            if event_desc in expertise_keys:
                if user_id not in user_expertise:
                    user_expertise[user_id] = {}
                user_expertise[user_id][event_desc] = int(user_behavior)
        for user in user_cognitive_load:
            tp_list = []
            for tp_key in cognitive_load_keys:
                assert tp_key in user_cognitive_load[user]
                tp_list.append(user_cognitive_load[user][tp_key])
            user_cognitive_load[user]['avg_cognitive_load'] = np.mean(tp_list)
        return user_expertise, user_cognitive_load
    
    def clean_action_list(user, task_id):
        action_list = user_task_action[user][task_id]
        new_action_list = []
        reserved_actions = ["action_prediction", "execute_action", "Next Step", "Proceed"]
        for index, action in enumerate(action_list):
            action_event = action['action_event']
            # action_parameters = action['action_parameters']
            if action_event in reserved_actions:
                new_action_list.append(action)
            # if action_event == "attention_check":
            #     if user not in user_attention_dict:
            #         user_attention_dict[user] = {}
            #     user_attention_dict[user]["execution"] = action_parameters["button"]
        return new_action_list
    
    def obtain_attention_check_in_execution(valid_users, task_list):
        for user in valid_users:
            for task_id in task_list:
                for index, action in enumerate(user_task_action[user][task_id]):
                    action_event = action['action_event']
                    action_parameters = action['action_parameters']
                    if action_event == "attention_check":
                        if user not in user_attention_dict:
                            user_attention_dict[user] = {}
                        user_attention_dict[user]["execution"] = action_parameters["button"]
    
    def action_sequence_parsing(valid_users, task_list):
        for user in valid_users:
            user_task_precise_action[user] = {}
            user_task_ai_suggestion[user] = {}
            for task_id in task_list:
                action_seq_execute = []
                action_seq_predict = []
                action_list = clean_action_list(user, task_id)
                last_index_execute = -1
                last_index_predict = -1
                flag_execute = False
                flag_predict = False
                flag_proceed = False
                for index, action in enumerate(action_list):
                    action_event = action['action_event']
                    # action_parameters = action['action_parameters']
                    if action_event == "execute_action":
                        last_index_execute = index
                        flag_execute = True
                    if action_event == "Proceed":
                        flag_proceed = True
                    if action_event == "action_prediction":
                        last_index_predict = index
                        flag_predict = True
                    if action_event == "Next Step":
                        if flag_execute:
                            # there is one action execution before this step
                            action_seq_execute.append(action_list[last_index_execute]["action_parameters"])
                            # reset execute action flag
                            flag_execute = False
                            # When next step occurs, ensure there is one execute
                            flag_proceed = False
                            # reset proceed flag after execute one action
                            # Then we collect predict as AI suggestion
                            if flag_predict:
                                # there is one action prediction before this step
                                action_seq_predict.append(action_list[last_index_predict]["action_parameters"])
                                flag_predict = False
                # finally, check the flags and append the last action execution / last action prediction
                if flag_execute:
                    # there is one action execution before this step
                    action_seq_execute.append(action_list[last_index_execute]["action_parameters"])
                    # reset execute action flag
                    flag_execute = False
                    # We only append action prediction when there is a action_execution
                    if flag_predict:
                        # ideally the last_index_predict should be action_list[-2]
                        action_seq_predict.append(action_list[last_index_predict]["action_parameters"])
                        flag_predict = False
                else:
                    if flag_predict:
                        action_seq_predict.append(action_list[last_index_predict]["action_parameters"])
                        flag_predict = False
                        if flag_proceed:
                            # user choose proceed, but there is execute after that, incomplete records?
                            action_seq_execute.append(action_list[last_index_predict]["action_parameters"])
                user_task_precise_action[user][task_id] = action_seq_execute
                user_task_ai_suggestion[user][task_id] = action_seq_predict

                # # After execute the last action, the whole execution is done
                # try:
                #     assert action_list[-1]["action_event"] == "execute_action"
                #     action_seq_execute.append(action_list[-1]["action_parameters"])
                #     user_task_precise_action[user][task_id] = action_seq_execute
                # except:
                #     # print(user, task_id, action_list)
                #     user_task_precise_action[user][task_id] = action_seq_execute

                # try:
                #     assert action_list[-2]["action_event"] == "action_prediction"
                #     action_seq_predict.append(action_list[-2]["action_parameters"])
                #     user_task_ai_suggestion[user][task_id] = action_seq_predict
                # except:
                #     # print(user, task_id, action_list)
                #     user_task_ai_suggestion[user][task_id] = action_seq_predict

    def find_complete_users(user_set):
        complete_users = set()
        TiA_subscales = ["Reliability/Competence", "Understanding/Predictability", 
            "Propensity to Trust", "Trust in Automation", "Familiarity"]
        for user in user_set:
            # if user.startswith('Gaole'):
            #     continue
            flag = False
            if user not in user_task_order or user not in user2condition:
                # print(f"user {user} not in condition dict or task order dict")
                flag = True
                continue
            tp_condition = user2condition[user]
            # print(user, tp_condition)
            # Trust in automation questionnaire
            if user not in user_expertise:
                # print("Missing user expertise")
                flag = True
                continue
            else:
                if 'llm_expertise' not in user_expertise[user] or 'assistant_expertise' not in user_expertise[user]:
                    # print("missing user expertise")
                    flag = True
                    continue
            # Trust in automation questionnaire
            for subscale in TiA_subscales:
                if user not in user_TiA_scale:
                    # print(f"{user} missing TiA")
                    flag = True
                    break
                if subscale not in user_TiA_scale[user]:
                    # print(user_TiA_scale[user])
                    # print(f"{user} missing TiA subscale {subscale}")
                    flag = True
                    break
            # trust and confidence in the main tasks
            if user not in user_task_confidence_dict or user not in user_task_trust_dict:
                # print(f"{user} with incomplete task records of trust/confidence")
                flag = True
                continue
            # user action / user plan
            if tp_condition.startswith("AP"):
                # in conditions with automatic planning, there is no user plan
                pass
            else:
                if user not in user_task_plan:
                    # print(f"{user} with incomplete task records or plan")
                    flag = True
                    continue
            if user not in user_task_action:
                # print(f"{user} with incomplete task records or action sequence")
                flag = True
                continue
            if user not in user_risk_perception:
                # print(f"{user} missing user risk perception")
                flag = True
            # Task-specific action / plan / trust / confidence check
            for task_id in task_ID_list_to_check:
                if tp_condition.startswith("AP"):
                    # in conditions with automatic planning, there is no user plan
                    pass
                else:
                    if task_id not in user_task_plan[user]:
                        # print(f"missing task plan on {task_id}")
                        flag = True
                        break
                if task_id not in user_task_action[user]:
                    # print(f"missing task action sequence on {task_id}")
                    flag = True
                    break
                if task_id not in user_risk_perception[user]:
                    # print(f"{user} missing user risk perception on {task_id}")
                    flag = True
                    break
                if task_id not in user_task_confidence_dict[user] or task_id not in user_task_trust_dict[user]:
                    # print(f"missing task trust/confidence on {task_id}")
                    flag = True
                    break
                if 'planning' not in user_task_confidence_dict[user][task_id]:
                    # print(f"missing task confidence before execution on {task_id}")
                    flag = True
                    break
                if 'execution' not in user_task_confidence_dict[user][task_id]:
                    # print(f"missing task confidence after execution on {task_id}")
                    flag = True
                    break
                if 'planning' not in user_task_trust_dict[user][task_id]:
                    # print(f"missing task confidence before execution on {task_id}")
                    flag = True
                    break
                if 'execution' not in user_task_trust_dict[user][task_id]:
                    # print(f"missing task confidence after execution on {task_id}")
                    flag = True
                    break
            # open feedback
            if user not in user_open_feedback:
                # print("missing all open feedback")
                flag = True
                continue
            else:
                for key_ in ["planning", "execution", "other"]:
                    if key_ not in user_open_feedback[user]:
                        # print(f"Missing open feedback {key_}")
                        flag = True
                        break
            if flag:
                continue
            complete_users.add(user)
        return complete_users
    
    def load_ground_truth():
        f = open("ground_truth.json")
        data = json.load(f)
        f.close()
        ground_truth_dict = {}
        for task_item in data:
            task_id = task_item['task_id']
            ground_truth = task_item['ground_truth']
            ground_truth_dict[task_id] = ground_truth
        return ground_truth_dict
    
    def calculate_appropriate_reliance(user_set, user_task_performance, AI_suggestion_performance):
        # This function follows standard definition of appropriate reliance
        # It does not consider the action sequence difference as a starting point
        user_RAIR = {}
        user_RSR = {}
        for user in user_set:
            positive_AI_reliance = 0.0
            negative_AI_reliance = 0.0
            positive_self_reliance = 0.0
            negative_self_reliance = 0.0
            for task_id in task_ID_list_to_check:
                action_seq_1 = user_task_precise_action[user][task_id]
                action_seq_2 = user_task_ai_suggestion[user][task_id]
                AI_correctness = AI_suggestion_performance[user][task_id]["acc_strict"]
                execution_correctness = user_task_performance[user][task_id]["acc_execution"]
                if AI_correctness == 1.0:
                    # when AI system is correct, how often users are correct? take AI advice as correct
                    if compare_action_seq_strict(seq_1=action_seq_1, seq_2=action_seq_2):
                        # When AI system is correct, adopting the same action sequence are defined as positive AI reliance
                        positive_AI_reliance += 1.0
                    else:
                        # When AI system is correct, adopting a different action sequence are defined as negative self reliance
                        negative_self_reliance += 1.0
                else:
                    # When AI system is wrong, how oftern users are correct? take AI advice as wrong
                    if execution_correctness == 1.0:
                        positive_self_reliance += 1.0
                    else:
                        # When AI advice is wrong, user action sequence keeps all the same indicate negative AI reliance
                        if compare_action_seq_strict(seq_1=action_seq_1, seq_2=action_seq_2):
                            negative_AI_reliance += 1.0
            if positive_AI_reliance + negative_self_reliance > 0:
                relative_positive_ai_reliance = positive_AI_reliance / float(positive_AI_reliance + negative_self_reliance)
            else:
                relative_positive_ai_reliance = 0.0

            if positive_self_reliance + negative_AI_reliance > 0:
                relative_positive_self_reliance = positive_self_reliance / float(positive_self_reliance + negative_AI_reliance)
            else:
                relative_positive_self_reliance = 0.0
            user_RAIR[user] = relative_positive_ai_reliance
            user_RSR[user] = relative_positive_self_reliance
        return user_RAIR, user_RSR
    
    def calc_calibrated_trust_planning(user_set, plan_quality_evaluation):
        calibrated_trust_planning = {}
        for user in user_set:
            calibrated_trust_planning[user] = {}
            calibrated_trust = []
            for task_id in task_ID_list_to_check:
                user_trust = user_task_trust_dict[user][task_id]["planning"]
                plan_quality = plan_quality_evaluation[user][task_id]
                if int(plan_quality) == 5:
                    if user_trust == "Yes":
                        tp_value = 1.0
                    else:
                        tp_value = 0.0
                else:
                    if user_trust == "No":
                        tp_value = 1.0
                    else:
                        tp_value = 0.0
                calibrated_trust_planning[user][task_id] = tp_value
                calibrated_trust.append(tp_value)
            calibrated_trust_planning[user]["avg"] = np.mean(calibrated_trust)
        return calibrated_trust_planning

    
    def calc_calibrated_trust_execution(user_set, user_task_performance):
        user_calibrated_trust = {}
        for user in user_set:
            user_calibrated_trust[user] = {}
            calibrated_trust = []
            for task_id in task_ID_list_to_check:
                second_trust = user_task_trust_dict[user][task_id]["execution"]
                execution_correctness = user_task_performance[user][task_id]["acc_execution"]
                if execution_correctness == 0.0:
                    if second_trust == "No":
                        tp_value = 1.0
                    else:
                        tp_value = 0.0
                else:
                    if second_trust == "Yes":
                        tp_value = 1.0
                    else:
                        tp_value = 0.0
                calibrated_trust.append(tp_value)
                user_calibrated_trust[user][task_id] = tp_value
            user_calibrated_trust[user]["avg"] = np.mean(calibrated_trust)
        return user_calibrated_trust
    
    # def calculate_two_stage_calibrated_trust(user_set, user_task_performance, AI_suggestion_performance):
    #     user_calibrated_trust = {}
    #     for user in user_set:
    #         calibrated_trust = []
    #         for task_id in task_ID_list_to_check:
    #             initial_trust = user_task_trust_dict[user][task_id]["planning"]
    #             second_trust = user_task_trust_dict[user][task_id]["execution"]
    #             # AI_correctness = AI_suggestion_performance[user][task_id]["acc_strict"]
    #             execution_correctness = user_task_performance[user][task_id]["execution"]
    #             # How to define calibrated trust with considering two stages?
    #             if initial_trust == "Yes":
    #                 # initial trust, but the execution is wrong
    #                 # If user choose No finally, 
    #                 if execution_correctness == 0.0: 
    #                     if second_trust == "No":
    #                         calibrated_trust.append(1.0)
    #                     else:
    #                         calibrated_trust.append(0.0)
    #             else:
    #                 # initial distrust, but the execution is correct
    #                 # If user choose Yes finally, 
    #                 if execution_correctness == 1.0:
    #                     if second_trust == "Yes":
    #                         calibrated_trust.append(1.0)
    #                     else:
    #                         calibrated_trust.append(0.0)
    #         if len(calibrated_trust) == 0:
    #             user_calibrated_trust[user] = 0.0
    #         else:
    #             user_calibrated_trust[user] = np.mean(calibrated_trust)
    #     return user_calibrated_trust
    
    def evaluate_calibrated_trust(user_set, user_task_performance):
        user_calibrated_trust = {}
        for user in user_set:
            calibrated_trust = []
            user_calibrated_trust[user] = {}
            for task_id in task_ID_list_to_check:
                accuracy_strict = user_task_performance[user][task_id]["acc_strict"]
                if accuracy_strict == 1.0:
                    # the execution is correct considering the action sequence
                    if user_task_trust_dict[user][task_id]["execution"] == "Yes":
                        tp_trust = 1.0
                    else:
                        tp_trust = 0.0
                else:
                    # the execution is wrong considering the action sequence
                    if user_task_trust_dict[user][task_id]["execution"] == "Yes":
                        tp_trust = 0.0
                    else:
                        tp_trust = 1.0
                calibrated_trust.append(tp_trust)
                user_calibrated_trust[user][task_id] = tp_trust
            user_calibrated_trust[user]["avg"] = np.mean(calibrated_trust)
        return user_calibrated_trust


    load_feedback(reserved_users=reserved_users)
    load_user_choice(reserved_users=reserved_users)
    load_userinfo(reserved_users=reserved_users)
    load_expertise_cognitiveload(reserved_users=reserved_users)
    plan_quality_evaluation = load_plan_quality_evaluation(reserved_users=reserved_users)
    user_TiA_scale = calc_TiA_scale(folder_name)
    # Only check users who finished all tasks with post-task questionnaire
    user_set_1 = set(user_cognitive_load.keys())
    print(f"{len(user_set_1)} complete the NASA-TLX")
    # First check all users who finished the post-task questionnaire
    complete_users = find_complete_users(user_set=user_set_1)
    print(f"{len(complete_users)} complete the whole study")
    # for user in complete_users:
    #     print(user)
    # Then confirm users who passed all the attention checks
    obtain_attention_check_in_execution(complete_users, task_ID_list_to_check)
    valid_users = set()
    # filter users who failed any attention checks
    for user in complete_users:
        flag = False
        assert user in user_attention_dict
        check_dict = {
            "execution": "Reflection",
            "qualification_2": 3,
            "TiA_attention": 1
        }
        for key_ in check_dict:
            if key_ not in user_attention_dict[user]:
                # print(f"user {user} miss attention check data for {key_}")
                flag = True
                break
            else:
                if user_attention_dict[user][key_] != check_dict[key_]:
                    # print(f"user {user} failed attention check - {key_} with {user_attention_dict[user][key_]}")
                    flag = True
                    break
        if flag:
            # if user2condition[user] == "UP-UE":
            #     print("-" * 34)
            continue
        valid_users.add(user)
    action_sequence_parsing(valid_users, task_ID_list_to_check)
    ground_truth_dict=load_ground_truth()
    user_task_performance = evaluate_action_sequence(user_set=valid_users,
                                                     user_precise_action=user_task_precise_action,
                                                     ground_truth_dict=ground_truth_dict)
    AI_suggestion_performance = evaluate_action_sequence(user_set=valid_users,
                                                     user_precise_action=user_task_ai_suggestion,
                                                     ground_truth_dict=ground_truth_dict)
    # user_calibrated_trust = evaluate_calibrated_trust(user_set=valid_users, user_task_performance=user_task_performance)
    user_RAIR, user_RSR = calculate_appropriate_reliance(valid_users, user_task_performance, AI_suggestion_performance)
    # user_calibrated_trust = calculate_two_stage_calibrated_trust(valid_users, user_task_performance, AI_suggestion_performance)
    calibrated_trust_execution = calc_calibrated_trust_execution(valid_users, user_task_performance)
    calibrated_trust_planning = calc_calibrated_trust_planning(valid_users, plan_quality_evaluation)
    tp_data = {
        'complete_users': complete_users,
        'user2condition': user2condition,
        'user_task_action': user_task_action,
        'user_task_conversation': user_task_conversation,
        'user_RAIR': user_RAIR,
        'user_RSR': user_RSR,
        'task_order': user_task_order,
        'user_task_plan': user_task_plan,
        "trust_in_automation": user_TiA_scale,
        'precise_action': user_task_precise_action,
        'risk_perception': user_risk_perception,
        'calibrated_trust_planning': calibrated_trust_planning,
        'calibrated_trust_execution': calibrated_trust_execution,
        'task_performance': user_task_performance,
        'user_expertise': user_expertise,
        'cognitive_load': user_cognitive_load,
        'confidence': user_task_confidence_dict,
        'user_planning_actions': user_planning_actions,
        'open_feedback': user_open_feedback,
        'user_trust': user_task_trust_dict,
        'plan_quality': plan_quality_evaluation,
        'ground_truth': ground_truth_dict
    }
    return valid_users, tp_data