from abc import abstractmethod
from typing import List, Tuple

from langchain_core.output_parsers import BaseOutputParser

from langchain_experimental.pydantic_v1 import BaseModel, Field


class Step(BaseModel):
    """Step."""

    value: str
    """The value."""


class Plan(BaseModel):
    """Plan."""

    steps: List[Step]
    """The steps."""


class StepResponse(BaseModel):
    """Step response."""

    response: str
    """The response."""


class BaseStepContainer(BaseModel):
    """Base step container."""

    @abstractmethod
    def add_step(self, step: Step, step_response: StepResponse) -> None:
        """Add step and step response to the container."""

    @abstractmethod
    def get_final_response(self) -> str:
        """Return the final response based on steps taken."""


class ChatHistoryContainer:

    def __init__(self, tp_query):
        self.history = [("human", tp_query)]
    
    def add_step(self, step: Step, step_response: StepResponse) -> None:
        self.history.append(("human", step.value))
        self.history.append(("ai", step_response.response))

    def get_chat_history(self) -> List[Tuple[str, str]]:
        return self.history
    
    def remove_step(self) -> None:
        # if at least one step get executed, there should be at least 3 elements in self.history
        if len(self.history) > 2:
            self.history.pop()
            self.history.pop()

class ListStepContainer(BaseStepContainer):
    """Container for List of steps."""

    steps: List[Tuple[Step, StepResponse]] = Field(default_factory=list)
    """The steps."""

    def add_step(self, step: Step, step_response: StepResponse) -> None:
        self.steps.append((step, step_response))

    def get_steps(self) -> List[Tuple[Step, StepResponse]]:
        return self.steps
    
    def remove_step(self) -> None:
        if len(self.steps) > 0:
            self.steps.pop()

    def get_final_response(self) -> str:
        return self.steps[-1][1].response


class PlanOutputParser(BaseOutputParser):
    """Plan output parser."""

    @abstractmethod
    def parse(self, text: str) -> Plan:
        """Parse into a plan."""