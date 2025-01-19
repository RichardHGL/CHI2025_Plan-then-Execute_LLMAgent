from abc import abstractmethod
from typing import (
    Any,
    List,
    Tuple,
    Union,
    Dict,
    Optional
)
from langchain_core.agents import AgentAction, AgentFinish, AgentStep
from langchain_core.callbacks import (
    CallbackManager,
    Callbacks,
)
from langchain.chains.base import Chain

from flaskr.agents.schema import StepResponse
from langchain_experimental.pydantic_v1 import BaseModel
from langchain_core.runnables import (
    RunnableConfig,
    ensure_config,
)
from langchain_core.load.dump import dumpd

class BaseExecutor(BaseModel):
    """Base executor."""

    @abstractmethod
    def step(
        self, inputs: dict, callbacks: Callbacks = None, **kwargs: Any
    ):
        """Take step."""

    @abstractmethod
    async def astep(
        self, inputs: dict, callbacks: Callbacks = None, **kwargs: Any
    ):
        """Take async step."""


class ChainExecutor(BaseExecutor):
    """Chain executor."""

    chain: Chain
    """The chain to use."""

    def prepare_run_manager(
        self,
        inputs,
        callbacks,
        config: Optional[RunnableConfig] = None,
    ):
        config = ensure_config(config)
        tags = config.get("tags")
        metadata = config.get("metadata")
        run_name = config.get("run_name") or self.chain.get_name()

        callback_manager = CallbackManager.configure(
            callbacks,
            self.chain.callbacks,
            self.chain.verbose,
            tags,
            self.chain.tags,
            metadata,
            self.chain.metadata,
        )

        run_manager = callback_manager.on_chain_start(
            dumpd(self),
            inputs,
            name=run_name,
        )
        return run_manager

    def action_prediction(
        self, inputs: dict, callbacks: Callbacks = None, **kwargs: Any
    ) -> List[AgentAction]:
        """Take step."""
        run_manager = self.prepare_run_manager(inputs=inputs, callbacks=callbacks)
        actions = self.chain._call_first(inputs=inputs, run_manager=run_manager)
        # get the actions to execute
        return actions
    
    def action_execution(
        self, inputs: dict, actions:List[AgentAction], callbacks: Callbacks = None, **kwargs: Any
    ) -> Tuple[StepResponse, Dict[str, Any]]:
        run_manager = self.prepare_run_manager(inputs=inputs, callbacks=callbacks)
        response = self.chain._call_second(inputs=inputs, actions=actions, run_manager=run_manager)
        if isinstance(response, dict) and 'output' in response:
            response = response['output']
        if isinstance(response, str):
            return StepResponse(response=response), {"message": response}
        if isinstance(response, dict):
            # print(response.keys())
            assert "message" in response
            return StepResponse(response=response["message"]), response
        return StepResponse(response=response), response

    def step(
        self, inputs: dict, callbacks: Callbacks = None, **kwargs: Any
    ):
        """Take step."""
        response = self.chain.run(**inputs, callbacks=callbacks)
        data_dict = {}
        if isinstance(response, dict):
            assert "message" in response
            return StepResponse(response=response["message"]), response
        return StepResponse(response=response), data_dict
        # try:
        #     print(response, type(response), flush=True)
        #     return StepResponse(response=response)
        # except:
        #     print(response, type(response), flush=True)
        #     return StepResponse(response="Error occurred")

    async def astep(
        self, inputs: dict, callbacks: Callbacks = None, **kwargs: Any
    ):
        """Take step."""
        response = await self.chain.arun(**inputs, callbacks=callbacks)
        data_dict = {}
        if isinstance(response, dict):
            assert "message" in response
            return StepResponse(response=response["message"]), response
        return StepResponse(response=response), data_dict