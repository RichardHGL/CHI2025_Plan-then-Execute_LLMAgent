from langchain.tools import tool, BaseTool
from langchain.pydantic_v1 import BaseModel, Field
from typing import Optional, Type
import math

@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

@tool
def get_square(a: float) -> float:
    """get the square of a number."""
    return a * a

@tool
def get_sqrt(a: float) -> str:
    """get the square root of a number."""
    if a >= 0:
        return "%.3f"%math.sqrt(a)
    else:
        return "Error, number which is less than 0 do not have a real value for square root"
