from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from langchain.agents.agent import AgentExecutor, ExceptionTool
# from flaskr.agents.agent import AgentExecutor
from langchain.agents.structured_chat.base import StructuredChatAgent
from langchain.tools import BaseTool
from langchain.memory import ConversationBufferMemory
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts.chat import MessagesPlaceholder
from langchain_core.agents import AgentAction, AgentFinish, AgentStep
from flaskr.agents.executor.base import ChainExecutor
from langchain_core.exceptions import OutputParserException
from langchain_core.callbacks import (
    AsyncCallbackManagerForChainRun,
    AsyncCallbackManagerForToolRun,
    BaseCallbackManager,
    CallbackManagerForChainRun,
    CallbackManagerForToolRun,
    Callbacks,
)
from langchain.agents.tools import InvalidTool
import time
from langchain_core.utils.input import get_color_mapping

HUMAN_MESSAGE_TEMPLATE_1 = """User ID: {user_id}

Current objective: {current_step}

{agent_scratchpad}"""

HUMAN_MESSAGE_TEMPLATE_2 = """Previous steps: {previous_steps}

Current objective: {current_step}

{agent_scratchpad}"""

TASK_PREFIX = """{objective}

User ID: {user_id}

"""


# memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

class CustomizedAgentExecutor(AgentExecutor):

    def execute_actions(
        self,
        actions: List[AgentAction],
        name_to_tool_map: Dict[str, BaseTool],
        color_mapping: Dict[str, str],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Union[AgentFinish, List[Tuple[AgentAction, str]]]:
        """Execute the actions predicted or specified.

        """
        return self._consume_next_step(
            [
                a
                for a in self._customized_execution(
                    actions,
                    name_to_tool_map,
                    color_mapping,
                    run_manager,
                )
            ]
        )
    
    def _customized_execution(
        self,
        actions: List[AgentAction],
        name_to_tool_map: Dict[str, BaseTool],
        color_mapping: Dict[str, str],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Iterator[Union[AgentFinish, AgentAction, AgentStep]]:
        for agent_action in actions:
            yield self._perform_agent_action(
                name_to_tool_map, color_mapping, agent_action, run_manager
            )

    def decode_actions(
        self, 
        values: List[Union[AgentFinish, AgentAction, AgentStep]]
    ) -> Union[AgentFinish, List[AgentAction]]:
        if isinstance(values[-1], AgentFinish):
            assert len(values) == 1
            return values[-1]
        else:
            return [a for a in values if isinstance(a, AgentAction)]
    
    # def _call_first_step(
    #     self,
    #     inputs: Dict[str, str],
    #     intermediate_steps: List[Tuple[AgentAction, str]],
    #     run_manager: Optional[CallbackManagerForChainRun] = None,
    # ) -> List[AgentAction]:
    #     return self.decode_actions(
    #         [
    #             a
    #             for a in self.take_one_action(
    #                 inputs,
    #                 intermediate_steps,
    #                 run_manager,
    #             )
    #         ]
    #     )

    def _call_first(
        self,
        inputs: Dict[str, str],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Union[AgentFinish, List[AgentAction]]:
        '''the agent will predict the actions to take in this step'''
        intermediate_steps: List[Tuple[AgentAction, str]] = []
        return self.decode_actions(
            [
                a
                for a in self.take_one_action(
                    inputs,
                    intermediate_steps,
                    run_manager,
                )
            ]
        )
        
    def _call_second(
        self,
        inputs: Dict[str, str],
        actions: Union[List[AgentAction], AgentFinish],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        """Run text through and get agent response."""

        # very similar to _call in the original _call
        # the difference is that we sepate the action prediction to _call_first
        # Construct a mapping of tool name to tool for easy lookup
        name_to_tool_map = {tool.name: tool for tool in self.tools}
        # We construct a mapping from each tool to a color, used for logging.
        color_mapping = get_color_mapping(
            [tool.name for tool in self.tools], excluded_colors=["green", "red"]
        )
        intermediate_steps : List[Tuple[AgentAction, str]] = []
        # Let's start tracking the number of iterations and time elapsed

        # if isinstance(actions, AgentFinish):
        #     print("Agent finish")
        #     return self._return(
        #         actions, intermediate_steps, run_manager=run_manager
        #     )

        iterations = 0
        time_elapsed = 0.0
        start_time = time.time()
        while self._should_continue(iterations, time_elapsed):
            if iterations == 0:
                # execute the actions from previous action prediction
                next_step_output = self.execute_actions(
                        actions,
                        name_to_tool_map,
                        color_mapping,
                        run_manager=run_manager,
                    )
                # if isinstance(next_step_output, AgentFinish):
                #     # If the predicted action is AgentFinish, let's continue to execute another action
                #     iterations += 1
                #     time_elapsed = time.time() - start_time
                #     continue
            else:
                # if the actions to execute showed error
                next_step_output = self._take_next_step(
                    name_to_tool_map,
                    color_mapping,
                    inputs,
                    intermediate_steps,
                    run_manager=run_manager,
                )
            
            if isinstance(next_step_output, AgentFinish):
                print("Agent finish")
                return self._return(
                    next_step_output, intermediate_steps, run_manager=run_manager
                )

            intermediate_steps.extend(next_step_output)
            if len(next_step_output) == 1:
                next_step_action = next_step_output[0]
                # See if tool should return directly
                tool_return = self._get_tool_return(next_step_action)
                print("Get only one tool output")
                if tool_return is not None:
                    return self._return(
                        tool_return, intermediate_steps, run_manager=run_manager
                    )
            iterations += 1
            time_elapsed = time.time() - start_time
        output = self.agent.return_stopped_response(
            self.early_stopping_method, intermediate_steps, **inputs
        )
        return self._return(output, intermediate_steps, run_manager=run_manager)

    def take_one_action(
        self,
        inputs: Dict[str, str],
        intermediate_steps: List[Tuple[AgentAction, str]],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Iterator[Union[AgentFinish, AgentAction, AgentStep]]:
        """Take a single step in the thought-action-observation loop.

        Override this to take control of how the agent makes and acts on choices.
        """
        try:
            intermediate_steps = self._prepare_intermediate_steps(intermediate_steps)
            # print("_iter_next_step: intermediate_steps", intermediate_steps)
            # Call the LLM to see what to do.
            output = self.agent.plan(
                intermediate_steps,
                callbacks=run_manager.get_child() if run_manager else None,
                **inputs,
            )
            # print("_iter_next_step: agent.plan output", output)
        except OutputParserException as e:
            if isinstance(self.handle_parsing_errors, bool):
                raise_error = not self.handle_parsing_errors
            else:
                raise_error = False
            if raise_error:
                raise ValueError(
                    "An output parsing error occurred. "
                    "In order to pass this error back to the agent and have it try "
                    "again, pass `handle_parsing_errors=True` to the AgentExecutor. "
                    f"This is the error: {str(e)}"
                )
            text = str(e)
            if isinstance(self.handle_parsing_errors, bool):
                if e.send_to_llm:
                    observation = str(e.observation)
                    text = str(e.llm_output)
                else:
                    observation = "Invalid or incomplete response"
            elif isinstance(self.handle_parsing_errors, str):
                observation = self.handle_parsing_errors
            elif callable(self.handle_parsing_errors):
                observation = self.handle_parsing_errors(e)
            else:
                raise ValueError("Got unexpected type of `handle_parsing_errors`")
            output = AgentAction("_Exception", observation, text)
            if run_manager:
                run_manager.on_agent_action(output, color="green")
            tool_run_kwargs = self.agent.tool_run_logging_kwargs()
            observation = ExceptionTool().run(
                output.tool_input,
                verbose=self.verbose,
                color=None,
                callbacks=run_manager.get_child() if run_manager else None,
                **tool_run_kwargs,
            )
            yield AgentStep(action=output, observation=observation)
            return

        # If the tool chosen is the finishing tool, then we end and return.
        if isinstance(output, AgentFinish):
            yield output
            return

        actions: List[AgentAction]
        if isinstance(output, AgentAction):
            actions = [output]
        else:
            actions = output
        for agent_action in actions:
            yield agent_action

    def _call(
        self,
        inputs: Dict[str, str],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        """Run text through and get agent response."""
        # Construct a mapping of tool name to tool for easy lookup
        name_to_tool_map = {tool.name: tool for tool in self.tools}
        # We construct a mapping from each tool to a color, used for logging.
        color_mapping = get_color_mapping(
            [tool.name for tool in self.tools], excluded_colors=["green", "red"]
        )
        intermediate_steps: List[Tuple[AgentAction, str]] = []
        # Let's start tracking the number of iterations and time elapsed
        iterations = 0
        time_elapsed = 0.0
        start_time = time.time()
        # We now enter the agent loop (until it returns something).
        while self._should_continue(iterations, time_elapsed):
            next_step_output = self._take_next_step(
                name_to_tool_map,
                color_mapping,
                inputs,
                intermediate_steps,
                run_manager=run_manager,
            )
            # print("step-output", next_step_output) # test running through
            # print("iterations", iterations) # test running through
            if isinstance(next_step_output, AgentFinish):
                # print("Agent finish")
                return self._return(
                    next_step_output, intermediate_steps, run_manager=run_manager
                )

            intermediate_steps.extend(next_step_output)
            if len(next_step_output) == 1:
                next_step_action = next_step_output[0]
                # See if tool should return directly
                tool_return = self._get_tool_return(next_step_action)
                # print("Get only one tool output")
                if tool_return is not None:
                    return self._return(
                        tool_return, intermediate_steps, run_manager=run_manager
                    )
            iterations += 1
            time_elapsed = time.time() - start_time
        output = self.agent.return_stopped_response(
            self.early_stopping_method, intermediate_steps, **inputs
        )
        return self._return(output, intermediate_steps, run_manager=run_manager)

    def _perform_agent_action(
        self,
        name_to_tool_map: Dict[str, BaseTool],
        color_mapping: Dict[str, str],
        agent_action: AgentAction,
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> AgentStep:
        if run_manager:
            # user_session = run_manager.user_session, keep the user session in run_manager
            # tp_json = {"tool_name": agent_action.tool, "tool_input": agent_action.tool_input}
            # send_action_detail(user_session, agent_action.tool, agent_action.tool_input)
            run_manager.on_agent_action(agent_action, color="green")
        # before agent execute the action, revise it from the human input
        # Design a way to obtain user manual input from interface
        # Otherwise we lookup the tool
        if agent_action.tool in name_to_tool_map:
            tool = name_to_tool_map[agent_action.tool]
            return_direct = tool.return_direct
            color = color_mapping[agent_action.tool]
            tool_run_kwargs = self.agent.tool_run_logging_kwargs()
            if return_direct:
                tool_run_kwargs["llm_prefix"] = ""
            # We then call the tool on the tool input to get an observation
            observation = tool.run(
                agent_action.tool_input,
                verbose=self.verbose,
                color=color,
                callbacks=run_manager.get_child() if run_manager else None,
                **tool_run_kwargs,
            )
        else:
            tool_run_kwargs = self.agent.tool_run_logging_kwargs()
            observation = InvalidTool().run(
                {
                    "requested_tool_name": agent_action.tool,
                    "available_tool_names": list(name_to_tool_map.keys()),
                },
                verbose=self.verbose,
                color=None,
                callbacks=run_manager.get_child() if run_manager else None,
                **tool_run_kwargs,
            )
        return AgentStep(action=agent_action, observation=observation)


def load_agent_executor(
    llm: BaseLanguageModel,
    tools: List[BaseTool],
    verbose: bool = False,
    use_chat_history: bool = False,
    include_task_in_prompt: bool = False,
) -> ChainExecutor:
    """
    Load an agent executor.

    Args:
        llm: BaseLanguageModel
        tools: List[BaseTool]
        verbose: bool. Defaults to False.
        include_task_in_prompt: bool. Defaults to False.

    Returns:
        ChainExecutor
    """
    if use_chat_history:
        input_variables = ["chat_history", "current_step", "agent_scratchpad", "user_id", "reflection"]
        template = HUMAN_MESSAGE_TEMPLATE_1
    else:
        # if chat history is not used, it will be organized in one message with previous steps
        input_variables = ["previous_steps", "current_step", "agent_scratchpad", "user_id", "reflection"]
        template = HUMAN_MESSAGE_TEMPLATE_2
        # objective is only used when use_chat_history = False
        if include_task_in_prompt:
            input_variables.append("objective")
            template = TASK_PREFIX + template

    # keep chat_history and reflection as two placeholders
    chat_history = MessagesPlaceholder(variable_name="chat_history")
    # placeholder to obtain user feedback
    reflection = MessagesPlaceholder(variable_name="reflection", optional=True)
    # In the execution process, the prompt composes of:
    # system_prompt, chat_history, reflection, human_message_template
    memory_prompts = [chat_history, reflection]

    agent = StructuredChatAgent.from_llm_and_tools(
        llm,
        tools,
        human_message_template=template,
        memory_prompts=memory_prompts,
        input_variables=input_variables,
    )
    # .with_config({"tags": ["agent_llm"]})
    # the tag agent_llm will be the reference to get message in callback handler
    agent_executor = CustomizedAgentExecutor.from_agent_and_tools(
        agent=agent, tools=tools, verbose=verbose
    )
    return ChainExecutor(chain=agent_executor)