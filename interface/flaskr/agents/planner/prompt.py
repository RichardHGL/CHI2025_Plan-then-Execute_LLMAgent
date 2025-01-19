
# One example for planning

planning_example = {
    "input": "Please help me find the current exchange rate of US dollars to Japanese yen, and calculate how much yen I would get for exchanging 5000 US dollars, but there is no need to actually perform the exchange transaction at this stage.",
    "reference": "1. Find the current exchange rate of US dollars to Japanese yen\n1.1 Obtain currency pair information (Currency pair: USD/JPY)\n1.2 Query the current exchange rate\n1.3 Obtain the current exchange rate (Exchange rate: Current exchange rate)\n2. Calculate the exchange amount\n2.1 Obtain exchange amount information (Amount: 5000 US dollars)\n2.2 Apply the current exchange rate for calculation\n2.3 Output the calculation result (Amount of yen obtained: Calculated amount of yen)"
}

# one example is given in the prompt below

Planning_prompt = '''You are a professional planning assistant. 

Given a user's question, your task is to fully understand the user's question and create a reasonable, executable multi-step plan to complete the user's task. Specifically, your plan should be like a tree with multiple subtasks. 

The output format is a string (content is a series of subtasks separated by newline characters), for example: 1. Task 1 \n 1.1 Task 1.1 \n 1.2 Task 1.2 \n 1.2.1 Task 1.2.1 \n ... \n 2. Task 2 \n ...\n",

Example: 
Question:
Please help me find the current exchange rate of US dollars to Japanese yen, and calculate how much yen I would get for exchanging 5000 US dollars, but there is no need to actually perform the exchange transaction at this stage.

Output:
1. Find the current exchange rate of US dollars to Japanese yen\n1.1 Obtain currency pair information (Currency pair: USD/JPY)\n1.2 Query the current exchange rate\n1.3 Obtain the current exchange rate (Exchange rate: Current exchange rate)\n2. Calculate the exchange amount\n2.1 Obtain exchange amount information (Amount: 5000 US dollars)\n2.2 Apply the current exchange rate for calculation\n2.3 Output the calculation result (Amount of yen obtained: Calculated amount of yen)

Let us Begin!

Question:
{{task}}

Output:
'''

USER_FIRST = '''Task Requirements:
{{task}}
Come up with an abstract plan to perform this task in a couple of steps. Give me the subtasks between <subtask> and </subtask>.'''

USER_PROMPT = """Subtask Results:\n{{observation}}
"""
# from agents.main_agent.prompt import USER_OVER_PROMPT as main_user_over_prompt

# USER_OVER_PROMPT = USER_PROMPT + main_user_over_prompt

# RESULT_PROMPT=USER_PROMPT+'''Current task:
# {{task}}
# Give me the final result of current task. Surround the result between <result> and </result>'''
