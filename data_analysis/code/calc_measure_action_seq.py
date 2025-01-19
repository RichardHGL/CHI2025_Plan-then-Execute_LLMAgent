import numpy as np
import os
import pandas as pd
import json

task_ID_list_to_check = ['test-149', 'test-200', 'test-388', 'test-497', 'test-675', 'test-859']

def get_optional_actions(task_id):
    assert task_id in task_ID_list_to_check
    if task_id == 'test-149':
        return ['bank_account_login', 'check_balance']
    if task_id == "test-200":
        return ['search_card', 'bank_account_login', 'check_credit_card_bills']
    if task_id == "test-388":
        return []
    if task_id == "test-497":
        return ['search_flight']
    if task_id == "test-675":
        return ['travel_itinerary_planner']
    if task_id == "test-859":
        return ['obtain_user_info', 'search_service_provider', 'select_service_provider']

def get_reason_invalid_action(action_tp):
    tool_name = action_tp['tool_name']
    if tool_name in ["Agent Finish", "Final Answer"]:
        # Special event
        return "fail to predict"
    tool_input = action_tp['tool_input']
    # first check whether action is template 
    for parameter in tool_input:
        if parameter == 'user_id':
            # ignore user_id
            continue
        if isinstance(tool_input[parameter], dict):
            if 'description' in tool_input[parameter]:
                # action is template 
                return "fail to predict, templates"
    for parameter in tool_input:
        if parameter == 'user_id':
            # ignore user_id
            continue
        if tool_input[parameter] == '':
            # empty str
            return "empty attribute"
    return "unknown reason for invalid action"

def check_invalid_action(action_tp):
    tool_name = action_tp['tool_name']
    if tool_name in ["Agent Finish", "Final Answer"]:
        # Special event
        return True
    tool_input = action_tp['tool_input']
    # first check whether action is template 
    for parameter in tool_input:
        if parameter == 'user_id':
            # ignore user_id
            continue
        if isinstance(tool_input[parameter], dict):
            if 'description' in tool_input[parameter]:
                # action is template 
                return True
    for parameter in tool_input:
        if parameter == 'user_id':
            # ignore user_id
            continue
        if tool_input[parameter] == '':
            # empty str
            return True
    # valid action name and all parameters not empty
    return False

def compare_action_pair(action_tp, reference):
    if action_tp['tool_name'] == reference['tool_name']:
        flag = False
        for parameter in reference['tool_input']:
            value = reference['tool_input'][parameter]
            if isinstance(value, list):
                if action_tp['tool_input'][parameter] not in value:
                    flag = True
                    break
            else:
                if parameter not in action_tp['tool_input']:
                    flag = True
                    break
                # value is a string or number, comparison with str
                if str(action_tp['tool_input'][parameter]) != str(value):
                    flag = True
                    break
        if flag:
            return False
        else:
            return True
    else:
        return False
    
def diagnose_actions(task_id, action_sequence, ground_truth):
    optional_actions = get_optional_actions(task_id)
    index_ground_truth = 0
    correct_flag = True
    reason = []
    for index, action in enumerate(action_sequence):
        # print(index, action)
        try:
            cur_action_name = action['tool_name']
        except:
            print(action)
            print(action_sequence)
        if index_ground_truth < len(ground_truth):
            reference = ground_truth[index_ground_truth]
            # print(action['tool_name'], compare_action_pair(action, reference))
            if compare_action_pair(action, reference):
                index_ground_truth += 1
                continue
            else:
                if cur_action_name in optional_actions:
                    if cur_action_name == reference['tool_name']:
                        reason.append("Action parameter mismatch - skip")
                    else:
                        reason.append("Action name mismatch - skip")
                    continue
                elif check_invalid_action(action):
                    # Ignore invalid actions - system error - fail to predict action
                    # Ignore invalid actions - miss any tool input
                    tp_reason = get_reason_invalid_action(action)
                    reason.append("Invalid Action" + tp_reason)
                    continue
                else:
                    # print("One valid action mismatch with current reference")
                    # reason = "One valid action mismatch with current reference"
                    if cur_action_name == reference['tool_name']:
                        reason.append("Action name mismatch")
                    else:
                        reason.append("Action parameter mismatch")
                    # reason.append("One valid action mismatch with current reference" + json.dumps(action, indent=4))
                    correct_flag = False
                    break
        else:
            # all ground truth actions have been met
            # Only optional actions are allowed, they will not cost anything
            # print(optional_actions)
            # print(cur_action_name)
            if cur_action_name in optional_actions:
                reason.append("Skip optinal action")
                continue
            elif check_invalid_action(action):
                # Ignore invalid actions - system error - fail to predict action
                # Ignore invalid actions - miss any required tool input
                tp_reason = get_reason_invalid_action(action)
                reason.append("Invalid Action" + tp_reason)
                continue
            else:
                # print("After execution, there has at least one wrong action")
                # print(action)
                correct_flag = False
                # reason = "After execution, there has at least one wrong action"
                reason.append("After execution, there has at least one wrong action")
                break
    # print(index_ground_truth, correct_flag)
    if index_ground_truth == len(ground_truth):
        # all necessary actions can be found 
        if correct_flag:
            # precise action sequence
            # only contain optinal actions which won't affect task execution result
            return 1.0, "success"
        else:
            # contain extra actions that will affect task execution results
            return 0.0, reason
    else:
        # miss necessary actions in ground truth
        reason.append("miss necessary action step")
        if len(reason) == 1:
            print(action_sequence)
        return 0.0, reason

def execute_actions(task_id, action_sequence, ground_truth):
    optional_actions = get_optional_actions(task_id)
    index_ground_truth = 0
    correct_flag = True
    for index, action in enumerate(action_sequence):
        # print(index, action)
        try:
            cur_action_name = action['tool_name']
        except:
            print(action)
            print(action_sequence)
        if index_ground_truth < len(ground_truth):
            reference = ground_truth[index_ground_truth]
            # print(action['tool_name'], compare_action_pair(action, reference))
            if compare_action_pair(action, reference):
                index_ground_truth += 1
                continue
            else:
                if cur_action_name in optional_actions:
                    continue
                elif check_invalid_action(action):
                    # Ignore invalid actions - system error - fail to predict action
                    # Ignore invalid actions - miss any tool input
                    continue
                else:
                    # print("One valid action mismatch with current reference")
                    correct_flag = False
                    break
        else:
            # all ground truth actions have been met
            # Only optional actions are allowed, they will not cost anything
            # print(optional_actions)
            # print(cur_action_name)
            if cur_action_name in optional_actions:
                continue
            elif check_invalid_action(action):
                # Ignore invalid actions - system error - fail to predict action
                # Ignore invalid actions - miss any required tool input
                continue
            else:
                # print("After execution, there has at least one wrong action")
                # print(action)
                correct_flag = False
                break
    # print(index_ground_truth, correct_flag)
    if index_ground_truth == len(ground_truth):
        # all necessary actions can be found 
        if correct_flag:
            # precise action sequence
            # only contain optinal actions which won't affect task execution result
            return 1.0
        else:
            # contain extra actions that will affect task execution results
            return 0.0
    else:
        # miss necessary actions in ground truth
        return 0.0

def clean_action_sequence(action_sequence, ground_truth):
    new_action_sequence = []
    for index, action in enumerate(action_sequence):
        tp_flag = False
        tool_name = action['tool_name']
        if tool_name in ["Agent Finish", "Final Answer"]:
            # remove actions with Agent Finish
            continue
        # for action_ in ground_truth:
        #     if compare_action_pair(action, action_):
        #         tp_flag = True
        #         break
        # if tp_flag:
        #     # if this action corresponds to one of the ground truth action, keep it
        #     new_action_sequence.append(action)
        #     continue
        # else:
        #     if check_invalid_action(action):
        #         # skip invalid actions
        #         continue
        #     # keep other valid actions
        #     new_action_sequence.append(action)
        new_action_sequence.append(action)
    return new_action_sequence

def evaluate_action_sequence(user_set, user_precise_action, ground_truth_dict):
    measures = ["acc_strict", "acc_relaxed", "recall", "acc_execution"]
    user_task_performance = {}
    for user in user_set:
        user_task_performance[user] = {}
        tp_dict = {}
        for measure in measures:
            tp_dict[measure] = []
        for task_id in task_ID_list_to_check:
            action_sequence = user_precise_action[user][task_id]
            ground_truth = ground_truth_dict[task_id]
            acc_relaxed, acc_strict = calc_seq_acc(action_sequence, ground_truth)
            execution_acc = execute_actions(task_id, action_sequence, ground_truth)
            recall = calc_seq_recall(seq_to_evaluate=action_sequence, ground_truth=ground_truth)
            user_task_performance[user][task_id] = {
                "acc_strict": acc_strict,
                "acc_relaxed": acc_relaxed,
                "acc_execution": execution_acc,
                "recall": recall
            }
            tp_dict["acc_strict"].append(acc_strict)
            tp_dict["acc_relaxed"].append(acc_relaxed)
            tp_dict["recall"].append(recall)
            tp_dict["acc_execution"].append(execution_acc)
        user_task_performance[user]["avg"] = {
            "recall": np.mean(tp_dict["recall"]),
            "acc_relaxed": np.mean(tp_dict["acc_relaxed"]),
            "acc_strict": np.mean(tp_dict["acc_strict"]),
            "acc_execution": np.mean(tp_dict["acc_execution"]),
        }
    return user_task_performance

def calc_seq_acc(action_sequence, ground_truth):
    # First, clean the action sequence by removing invalid actions
    new_action_sequence = clean_action_sequence(action_sequence, ground_truth)
    if len(new_action_sequence) != len(ground_truth):
        # If the length of action sequence does not match, there exist at least one mismatch
        return 0.0, 0.0
    else:
        acc_relaxed_list = []
        acc_strict_list = []
        for index in range(len(ground_truth)):
            action_tp = new_action_sequence[index]
            reference = ground_truth[index]
            if action_tp['tool_name'] == reference['tool_name']:
                acc_relaxed_list.append(1.0)
                if compare_action_pair(action_tp=action_tp, reference=reference):
                    acc_strict_list.append(1.0)
                else:
                    acc_strict_list.append(0.0)
            else:
                acc_relaxed_list.append(0.0)
                acc_strict_list.append(0.0)
    acc_relaxed = min(acc_relaxed_list)
    acc_strict = min(acc_strict_list)
    return acc_relaxed, acc_strict

# def calc_seq_acc(seq_to_evaluate, ground_truth):
#     action_intent_correctness = []
#     action_detail_correctness = []
#     for index in range(len(ground_truth)):
#         action_tp = seq_to_evaluate[index]
#         action_true = ground_truth[index]
#         if action_tp['tool_name'] == action_true['tool_name']:
#             action_intent_correctness.append(1.0)
#             flag = False
#             for parameter in action_true['tool_input']:
#                 value = action_true['tool_input'][parameter]
#                 if isinstance(value, list):
#                     if action_tp['tool_input'][parameter] not in value:
#                         flag = True
#                         break
#                 else:
#                     # value is a string or number, comparison with str
#                     if str(action_tp['tool_input'][parameter]) != str(value):
#                         flag = True
#                         break
#             if flag:
#                 # print(action_tp)
#                 # print(action_true)
#                 action_detail_correctness.append(0.0)
#             else:
#                 action_detail_correctness.append(1.0)
#         else:
#             # When the action name does not match, give 0.0 for current position
#             action_intent_correctness.append(0.0)
#             action_detail_correctness.append(0.0)
#     return action_intent_correctness, action_detail_correctness

def calc_seq_recall(seq_to_evaluate, ground_truth):
    recall = []
    for index in range(len(ground_truth)):
        action_true = ground_truth[index]
        tp_flag = False
        for action_tp in seq_to_evaluate:
            tp_flag = compare_action_pair(action_tp, reference=action_true)
            if tp_flag:
                break
        if tp_flag:
            # print(action_true, 1.0)
            recall.append(1.0)
        else:
            # print(action_true, 0.0)
            recall.append(0.0)
    return np.mean(recall)
