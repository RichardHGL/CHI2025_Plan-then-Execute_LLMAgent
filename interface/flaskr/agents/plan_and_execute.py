from typing import Any, Dict, List, Optional, Union

from langchain.callbacks.manager import (
    AsyncCallbackManagerForChainRun,
    CallbackManagerForChainRun,
)
from langchain.chains.base import Chain
from langchain_core.agents import AgentAction, AgentFinish
from langchain_experimental.plan_and_execute.executors.base import BaseExecutor
from langchain_experimental.plan_and_execute.planners.base import BasePlanner
from flaskr.agents.schema import (
    BaseStepContainer,
    ListStepContainer,
    StepResponse,
    ChatHistoryContainer
)
from langchain_experimental.pydantic_v1 import Field
from langchain_experimental.plan_and_execute.schema import (
    Plan,
)
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from flaskr.agents.streaming import TokenByTokenHandler

def parse_chunk(chunk) -> str:
    out_str = ""
    # Agent Action
    if "actions" in chunk:
        for action in chunk["actions"]:
            out_str += f"Calling Tool: `{action.tool}` with input `{action.tool_input}`\n"
            # print(f"Calling Tool: `{action.tool}` with input `{action.tool_input}`")
    # Observation
    elif "steps" in chunk:
        for step in chunk["steps"]:
            out_str += f"Tool Result: `{step.observation}`\n"
            # print(f"Tool Result: `{step.observation}`")
    # Final result
    elif "output" in chunk:
        out_str += f'Final Output: {chunk["output"]}'
        # print(f'Final Output: {chunk["output"]}\n')
    else:
        raise ValueError()
    # print("---")
    out_str += ("---\n")

class StepWiseExecution():
    """Execute a plan step-by-step."""

    def __init__(self, executor, task:str, user_id:str, use_chat_history=False) -> None:
        self.executor = executor
        self.objective = task
        self.user_id = user_id
        self.step_container = ListStepContainer()
        self.input_key = "input"
        self.output_key = "output"
        self.use_chat_history = use_chat_history
        self.exec_index = 0
        # initialize the chat history with setting up the objective
        if self.use_chat_history:
            self.history = ChatHistoryContainer(tp_query=task)

    @property
    def input_keys(self) -> List[str]:
        return [self.input_key]

    @property
    def output_keys(self) -> List[str]:
        return [self.output_key]

    def assign_plan(self, plan: Plan):
        self.plan = plan.steps
    
    def get_cur_step(self):
        step_index = self.exec_index
        if step_index >= len(self.plan):
            return "execution done"
        else:
            current_step = self.plan[step_index]
        return current_step.value
    
    def prepare_inputs(self,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        step_index = self.exec_index
        previous_steps = self.step_container.get_steps()
        current_step = self.plan[step_index]
        objective = self.objective
        if self.use_chat_history:
            # In this way, we use conversation to guide the whole task solving process
            if "reflection" in inputs and inputs["reflection"].lower() != "none":
                # When user reflection exist, add user reflection before the current step
                chat_history = self.history.get_chat_history() + [('human', inputs["reflection"])]
            else:
                chat_history = self.history.get_chat_history()
            _new_inputs = {
                "user_id": self.user_id,
                "chat_history": chat_history,
                "current_step": current_step,
            }
            # print(_new_inputs)
        else:
            # In this way, each time we only show previous steps as history in a prompt message
            _new_inputs = {
                "user_id": self.user_id,
                "previous_steps": previous_steps,
                "current_step": current_step,
                "objective": objective,
            }
        new_inputs = {**_new_inputs, **inputs}
        return new_inputs
    
    def one_step_first(
        self,
        inputs: Dict[str, Any],
        callbacks: TokenByTokenHandler=None
    ) -> Union[str, List[AgentAction], AgentFinish]:
        # split the agent step into two stages
        # stage-1: predict actions to execute
        step_index = self.exec_index
        if step_index >= len(self.plan):
            return "execution done"
        new_inputs = self.prepare_inputs(inputs=inputs)
        self.actions_to_execute = self.executor.action_prediction(
            new_inputs,
            callbacks=callbacks,
        )
        return self.actions_to_execute
    
    def one_step_second(
        self,
        inputs: Dict[str, Any],
        actions: List[AgentAction],
        callbacks: TokenByTokenHandler=None,
    ) -> Dict[str, Any]:
        step_index = self.exec_index
        if step_index >= len(self.plan):
            return "execution done"
        current_step = self.plan[step_index]
        if actions is not None:
            actions_to_execute = actions
        else:
            actions_to_execute = self.actions_to_execute

        new_inputs = self.prepare_inputs(inputs=inputs)
        response, data_dict = self.executor.action_execution(
            inputs=new_inputs,
            actions=actions_to_execute,
            callbacks=callbacks,
        )

        self.step_container.add_step(current_step, response)
        # After execution, if we found that agentfinish is executed, we keep the step?
        if actions is not None:
            if len(actions) == 1 and actions[-1].tool == "AgentFinish":
                self.exec_index = self.exec_index - 1
        else:
            if isinstance(actions_to_execute, AgentFinish):
                # Agent Finish, we should trace back
                self.exec_index = self.exec_index - 1
        self.exec_index = self.exec_index + 1
        if self.use_chat_history:
            self.history.add_step(current_step, response)
        self.step_container.add_step(current_step, response)

        # print(type(data_dict))
        data_dict["task_end"] = self.execution_done()
        return data_dict

    # def one_step_second(
    #     self,
    #     inputs: Dict[str, Any],
    #     actions: List[AgentAction]=None,
    #     callbacks: TokenByTokenHandler=None,
    # ) -> Dict[str, Any]:
    #     # split the agent step into two stages
    #     # stage-2: execute the actions after confirmation with users
    #     step_index = self.exec_index
    #     if step_index >= len(self.plan):
    #         return "execution done"
    #     current_step = self.plan[step_index]
    #     if actions is None:
    #         actions_to_execute = self.actions_to_execute
    #     else:
    #         actions_to_execute = actions

    #     new_inputs = self.prepare_inputs(inputs=inputs)
    #     response, data_dict = self.executor.action_execution(
    #         inputs=new_inputs,
    #         actions=actions_to_execute,
    #         callbacks=callbacks,
    #     )
    #     self.step_container.add_step(current_step, response)
    #     self.exec_index = self.exec_index + 1
    #     if self.use_chat_history:
    #         self.history.add_step(current_step, response)
    #     self.step_container.add_step(current_step, response)
    #     return {self.output_key: response.response}

    def execution_done(self) -> bool:
        if self.exec_index >= len(self.plan):
            return True
        return False

    def one_step(
        self,
        inputs: Dict[str, Any],
        callbacks: TokenByTokenHandler=None
    ) -> Dict[str, Any]:
        # print(inputs)
        # print("One step - ", self.exec_index)
        # print("-" * 17)
        step_index = self.exec_index
        if step_index >= len(self.plan):
            return "execution done"
        previous_steps = self.step_container.get_steps()
        current_step = self.plan[step_index]
        objective = self.objective
        if self.use_chat_history:
            # In this way, we use conversation to guide the whole task solving process
            if "reflection" in inputs and inputs["reflection"].lower() != "none":
                # When user reflection exist, add user reflection before the current step
                chat_history = self.history.get_chat_history() + [('human', inputs["reflection"])]
            else:
                chat_history = self.history.get_chat_history()
            _new_inputs = {
                "user_id": self.user_id,
                "chat_history": chat_history,
                "current_step": current_step,
            }
            # print(_new_inputs)
        else:
            # In this way, each time we only show previous steps as history in a prompt message
            _new_inputs = {
                "user_id": self.user_id,
                "previous_steps": previous_steps,
                "current_step": current_step,
                "objective": objective,
            }
        new_inputs = {**_new_inputs, **inputs}
        response, data_dict = self.executor.step(
            new_inputs,
            callbacks=callbacks,
        )
        if self.use_chat_history:
            self.history.add_step(current_step, response)
        self.step_container.add_step(current_step, response)
        self.exec_index = self.exec_index + 1
        return {self.output_key: response.response}
    
    def step_back(self):
        self.exec_index = self.exec_index - 1
        self.step_container.remove_step()
        if self.use_chat_history:
            self.history.remove_step()

    def reflection_step(self,
        inputs: Dict[str, Any],
        callbacks: TokenByTokenHandler,
    ) -> Union[str, List[AgentAction]]:
        # this function will be used if user want to reflect after action prediction
        assert "reflection" in inputs
        # we can call this if user want to re-try one step
        return self.one_step_first(inputs, callbacks)
    
    # def revise_step(self,
    #     inputs: Dict[str, Any],
    #     callbacks: TokenByTokenHandler,
    # ) -> Union[str, List[AgentAction]]:
    #     # reset the execution status
    #     # this function will be used if user want to re-do one step after execution
    #     self.step_back()
    #     # re-execution with extra human input
    #     assert "reflection" in inputs
    #     # we can call this if user want to re-try one step
    #     return self.one_step_first(inputs, callbacks)

class PlanAndExecute(Chain):
    """Plan and execute a chain of steps."""

    planner: BasePlanner
    """The planner to use."""
    executor: BaseExecutor
    """The executor to use."""
    step_container: BaseStepContainer = Field(default_factory=ListStepContainer)
    """The step container to use."""
    input_key: str = "input"
    output_key: str = "output"

    @property
    def input_keys(self) -> List[str]:
        return [self.input_key]

    @property
    def output_keys(self) -> List[str]:
        return [self.output_key]

    def assign_plan(self, plan: Plan, inputs: Dict[str, Any]):
        self.plan = plan
        self.exec_index = 0
        self.objective = inputs[self.input_key]

    # def one_step_first(
    #     self,
    #     inputs: Dict[str, Any],
    #     run_manager: Optional[CallbackManagerForChainRun] = None,
    # ) -> Dict[str, Any]:
    #     step_index = self.exec_index
    #     if step_index >= len(self.plan):
    #         return "execution done"
    #     previous_steps = self.step_container.get_steps()
    #     current_step = self.plan[step_index]
    #     objective = self.objective
    #     _new_inputs = {
    #         "previous_steps": previous_steps,
    #         "current_step": current_step,
    #         "objective": objective,
    #     }
    #     new_inputs = {**_new_inputs, **inputs}
    #     self.actions_to_execute = self.executor.action_prediction(
    #         new_inputs,
    #         callbacks=run_manager.get_child() if run_manager else None,
    #     )
    #     return self.actions_to_execute
        
    # def one_step_second(
    #     self,
    #     actions: List[AgentAction],
    #     run_manager: Optional[CallbackManagerForChainRun] = None,
    # ) -> Dict[str, Any]:
    #     step_index = self.exec_index
    #     if step_index >= len(self.plan):
    #         return "execution done"
    #     current_step = self.plan[step_index]
    #     if actions is not None:
    #         actions_to_execute = actions
    #     else:
    #         actions_to_execute = self.actions_to_execute
    #     response = self.executor.action_execution(
    #         actions_to_execute,
    #         callbacks=run_manager.get_child() if run_manager else None,
    #     )
    #     self.step_container.add_step(current_step, response)
    #     self.exec_index = self.exec_index + 1
    #     return {self.output_key: response.response}

    def one_step(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        step_index = self.exec_index
        if step_index >= len(self.plan):
            return "execution done"
        previous_steps = self.step_container.get_steps()
        current_step = self.plan[step_index]
        objective = self.objective
        _new_inputs = {
            "previous_steps": previous_steps,
            "current_step": current_step,
            "objective": objective,
        }
        new_inputs = {**_new_inputs, **inputs}
        response = self.executor.step(
            new_inputs,
            callbacks=run_manager.get_child() if run_manager else None,
        )
        self.step_container.add_step(current_step, response)
        self.exec_index = self.exec_index + 1
        return {self.output_key: response.response}
    
    def revise_step(self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        # reset the execution status
        self.exec_index = self.exec_index - 1
        self.step_container.remove_step()
        # re-execution with extra human input
        return self.one_step(inputs, run_manager)

    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        plan = self.planner.plan(
            inputs,
            callbacks=run_manager.get_child() if run_manager else None,
        )
        if run_manager:
            run_manager.on_text(str(plan), verbose=self.verbose)
        for step in plan.steps:
            _new_inputs = {
                "previous_steps": self.step_container,
                "current_step": step,
                "objective": inputs[self.input_key],
            }
            new_inputs = {**_new_inputs, **inputs}
            response = self.executor.step(
                new_inputs,
                callbacks=run_manager.get_child() if run_manager else None,
            )
            if run_manager:
                run_manager.on_text(
                    f"*****\n\nStep: {step.value}", verbose=self.verbose
                )
                run_manager.on_text(
                    f"\n\nResponse: {response.response}", verbose=self.verbose
                )
            self.step_container.add_step(step, response)
        return {self.output_key: self.step_container.get_final_response()}

    async def _acall(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[AsyncCallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        plan = await self.planner.aplan(
            inputs,
            callbacks=run_manager.get_child() if run_manager else None,
        )
        if run_manager:
            await run_manager.on_text(str(plan), verbose=self.verbose)
        for step in plan.steps:
            _new_inputs = {
                "previous_steps": self.step_container,
                "current_step": step,
                "objective": inputs[self.input_key],
            }
            new_inputs = {**_new_inputs, **inputs}
            response = await self.executor.astep(
                new_inputs,
                callbacks=run_manager.get_child() if run_manager else None,
            )
            if run_manager:
                await run_manager.on_text(
                    f"*****\n\nStep: {step.value}", verbose=self.verbose
                )
                await run_manager.on_text(
                    f"\n\nResponse: {response.response}", verbose=self.verbose
                )
            self.step_container.add_step(step, response)
        return {self.output_key: self.step_container.get_final_response()}