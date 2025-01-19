
plan_prompt = '''You are a professional planning assistant. 

Given a user's question, your task is to fully understand the user's question and create a reasonable, executable multi-step plan to complete the user's task. Specifically, your plan should be like a tree with multiple subtasks. 

The output format is a string (content is a series of subtasks separated by newline characters), for example: 1. Task 1 \n 1.1 Task 1.1 \n 1.2 Task 1.2 \n 1.2.1 Task 1.2.1 \n ... \n 2. Task 2 \n ...\n",

Example: 
Question:
Please help me find the current exchange rate of US dollars to Japanese yen, and calculate how much yen I would get for exchanging 5000 US dollars, but there is no need to actually perform the exchange transaction at this stage.

Output:
1. Find the current exchange rate of US dollars to Japanese yen\n1.1 Obtain currency pair information (Currency pair: USD/JPY)\n1.2 Query the current exchange rate\n1.3 Obtain the current exchange rate (Exchange rate: Current exchange rate)\n2. Calculate the exchange amount\n2.1 Obtain exchange amount information (Amount: 5000 US dollars)\n2.2 Apply the current exchange rate for calculation\n2.3 Output the calculation result (Amount of yen obtained: Calculated amount of yen)

'''
from typing import List
from langchain_experimental.plan_and_execute.schema import (
    Plan,
    PlanOutputParser,
    Step,
)
import re

def plan_split(plan_text):
    '''For each x., we take it as one step including sub-steps under x.'''
    step_list = plan_text.split("\n")
    final_steps = []
    tp_list = []
    cur_index = 1
    # print(plan_text)
    for step in step_list:
        if len(step.strip()) == 0:
            continue
        if step.strip().startswith(f"{cur_index}."):
            tp_list.append(step)
        else:
            # print(step)
            cur_index = cur_index + 1
            # x.y.z -> x+1.
            # assert step.strip().startswith(f"{cur_index}.")
            if not step.strip().startswith(f"{cur_index}."):
                print(step)
                print(step_list)
            final_steps.append("\n".join(tp_list))
            tp_list = [step]
    if len(tp_list) > 0:
        final_steps.append("\n".join(tp_list))
    return final_steps

class PlanningOutputParser(PlanOutputParser):
    """Planning output parser."""

    def parse(self, text: str) -> Plan:
        # print(text)
        steps_ = plan_split(plan_text=text)
        steps = [Step(value=v) for v in steps_]
        return Plan(steps=steps)
    
    def parse_ori(self, text: str) -> List[str]:
        # print(text)
        return plan_split(plan_text=text)
    
    def wrap_plan(self, steps_:List[str]) -> Plan:
        steps = [Step(value=v) for v in steps_]
        return Plan(steps=steps)

from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import SystemMessage

from langchain_experimental.plan_and_execute.planners.base import LLMPlanner

SYSTEM_PROMPT = (
    "Let's first understand the problem and devise a plan to solve the problem."
    " Please output the plan starting with the header 'Plan:' "
    "and then followed by a numbered list of steps. "
    "Please make the plan the minimum number of steps required "
    "to accurately complete the task. If the task is a question, "
    "the final step should almost always be 'Given the above steps taken, "
    "please respond to the users original question'. "
    "At the end of your plan, say '<END_OF_PLAN>'"
)

def load_chat_planner(
    llm: BaseLanguageModel, system_prompt: str = plan_prompt
) -> LLMPlanner:
    """
    Load a chat planner.

    Args:
        llm: Language model.
        system_prompt: System prompt.

    Returns:
        LLMPlanner
    """
    prompt_template = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_prompt),
            HumanMessagePromptTemplate.from_template("{input}"),
        ]
    )
    llm_chain = LLMChain(llm=llm, prompt=prompt_template)
    return LLMPlanner(
        llm_chain=llm_chain,
        output_parser=PlanningOutputParser(),
        stop=["<END_OF_PLAN>"],
    )

if __name__ == "__main__":
    steps = plan_split("1. Find the current exchange rate of US dollars to Japanese yen\n1.1 Obtain currency pair information (Currency pair: USD/JPY)\n1.2 Query the current exchange rate\n1.3 Obtain the current exchange rate (Exchange rate: Current exchange rate)\n2. Calculate the exchange amount\n2.1 Obtain exchange amount information (Amount: 5000 US dollars)\n2.2 Apply the current exchange rate for calculation\n2.3 Output the calculation result (Amount of yen obtained: Calculated amount of yen)")
    print(steps)