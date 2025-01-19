from langchain.tools import tool, BaseTool
from langchain.pydantic_v1 import BaseModel, Field
from typing import Optional, Type, Literal

# Please check the latest status of my two orders with the numbers 123456789 and 987654321, and confirm whether they are both associated with my customer ID A123456.
# test-256

class TrackingInput(BaseModel):
    tracking_number: Literal["123456789", "987654321"] = Field(description="A number used to track delivery package")


@tool("check_order_status", return_direct=True, args_schema=TrackingInput)
def check_order_status(tracking_number: str) -> str:
    '''Check the status of one order with a tracking number'''
    order_status_dict = {
        "123456789": "Order 123456789 is on the way, it just dispatched from point A",
        "987654321": "Order 987654321 arrived at the destination point -- New York, XYZ Street"
    }
    if tracking_number not in order_status_dict:
        return f"Tracking number {tracking_number} does not exist"
    else:
        return order_status_dict[tracking_number]

class OrderCustomerInput(BaseModel):
    tracking_number: Literal["123456789", "987654321"] = Field(description="A number used to track delivery package")
    customer_id: str = Field(description="Customer ID")


@tool("check_order_customer", return_direct=True, args_schema=OrderCustomerInput)
def check_order_customer(tracking_number: str, customer_id: str) -> str:
    '''Check whether a delivery package is associated with specific customer with tracking number and customer id'''
    order_customer_dict = {
        "123456789": "A123456",
        "987654321": "A233996"
    }
    if tracking_number not in order_customer_dict:
        return f"Tracking number {tracking_number} does not exist"
    else:
        actual_customer_id = order_customer_dict[tracking_number]
        if actual_customer_id == customer_id:
            return f"The order {tracking_number} is asscociated with you, customer {customer_id}"
        else:
            return f"The order {tracking_number} is asscociated with another customer. If you have any confusion, please contact our customer service"
