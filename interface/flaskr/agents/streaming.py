from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, TypeVar, Union
from uuid import UUID

from langchain_core.callbacks.base import AsyncCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatGenerationChunk, GenerationChunk, LLMResult

# Here is a custom handler that will print the tokens to stdout.
# Instead of printing to stdout you can send the data elsewhere; e.g., to a streaming API response


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
        print(f'Final Output: {chunk["output"]}\n')
    else:
        raise ValueError()
    # print("---")
    out_str += ("---\n")

import queue

from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


class ThreadedGenerator:
    def __init__(self):
        self.queue = queue.Queue()

    def __iter__(self):
        return self

    def __next__(self):
        item = self.queue.get()
        if item is StopIteration: raise item
        return item

    def send(self, data):
        self.queue.put(data)

    def close(self):
        self.queue.put(StopIteration)

class ChainStreamHandler(StreamingStdOutCallbackHandler):
    def __init__(self, gen):
        super().__init__()
        self.gen = gen

    def on_llm_new_token(self, token: str, **kwargs):
        self.gen.send(token)

class TokenByTokenHandler(AsyncCallbackHandler):
    def __init__(self, tags_of_interest: List[str], gen: ThreadedGenerator) -> None:
        """A custom call back handler.

        Args:
            tags_of_interest: Only LLM tokens from models with these tags will be
                              printed.
            gen: the output stream will be put into a queue
        """
        self.tags_of_interest = tags_of_interest
        self.gen = gen

    async def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Run when chain starts running."""
        # print("on chain start: ")
        # print(inputs)

    async def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Run when chain ends running."""
        print("On chain end")
        print(outputs)
        # To check whether we can send html element, eg color here
        if 'text' in outputs and "Action" in outputs['text']:
            # send the action to front end
            self.gen.send(outputs['text'])
        if 'output' in outputs and 'user_message' in outputs['output']:
            self.gen.send(outputs['output']['user_message'])

    async def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """Run when a chat model starts running."""
        overlap_tags = self.get_overlap_tags(tags)
        print("On model start")
        # print(messages)
        # print(serialized)
        print("-" * 17)
        if overlap_tags:
            print(",".join(overlap_tags), end=": ", flush=True)

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        inputs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """Run when tool starts running."""
        # print("Tool start")
        # print(serialized)
        # out_str += f"Calling Tool: `{action.tool}` with input `{action.tool_input}`\n"
        if 'name' in serialized:
            self.gen.send("\nTool name: {}\n".format(serialized['name']))
        # if 'description' in serialized:
        #     self.gen.send("description of tool: {}\n".format(serialized['description']))

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """Run when tool ends running."""
        print("Tool end")
        print(str(output))

    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Run when LLM ends running."""
        overlap_tags = self.get_overlap_tags(tags)

        if overlap_tags:
            # Who can argue with beauty?
            print()
            print()

    def get_overlap_tags(self, tags: Optional[List[str]]) -> List[str]:
        """Check for overlap with filtered tags."""
        if not tags:
            return []
        return sorted(set(tags or []) & set(self.tags_of_interest or []))

    # async def on_llm_new_token(
    #     self,
    #     token: str,
    #     *,
    #     chunk: Optional[Union[GenerationChunk, ChatGenerationChunk]] = None,
    #     run_id: UUID,
    #     parent_run_id: Optional[UUID] = None,
    #     tags: Optional[List[str]] = None,
    #     **kwargs: Any,
    # ) -> None:
    #     """Run on new LLM token. Only available when streaming is enabled."""
    #     # overlap_tags = self.get_overlap_tags(tags)
    #     # self.gen.send(token)

    #     # if token and overlap_tags:
    #     #     # self.gen.send(token)
    #     #     print(token, end="|", flush=True)

# To-do, current TokenByTokenHandler works, however, I'd prefer to make the response more structured

# handler = TokenByTokenHandler(tags_of_interest=["tool_llm", "agent_llm"])