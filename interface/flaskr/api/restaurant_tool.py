from langchain.tools import tool, BaseTool
from langchain.pydantic_v1 import BaseModel, Field
from typing import Optional, Type, List, Dict, Literal


# Please order a Spicy Hot Pot for me at the restaurant, add two extra servings of beef and a plate of hand-torn cabbage, then place the order using my table ID 10, and help me check out.
# test-271

dishes = ["Spicy Hot Pot", "Beef", "Hand-torn cabbage", "Rice"]

food_price = {
    "Spicy Hot Pot": 58,
    "Beef": 20,
    "Hand-torn cabbage": 15,
    "Rice": 5
}

class AddOrderInput(BaseModel):
    user_id: str = Field(description="User ID")
    table_id: int = Field(description="Table ID")
    dish_name: Literal["Spicy Hot Pot", "Beef", "Hand-torn cabbage", "Rice"] = Field(description="The name of dish")
    amount: int = Field(description="The number of dishes to add", ge=0, le=99, default=1)
    # order_dict: Dict = Field(description="A dict to show the ordered dishes for one table. The name of dish as key and the amount of each dish is used as value")

# To check, whether we should define the number for each dish here?
# Do we support multiple actions to execute?
@tool("add_single_dish_to_order", return_direct=True, args_schema=AddOrderInput)
def add_single_dish_to_order(user_id:str, table_id:int, dish_name: str, amount:int) -> Dict:
    '''Add the amount of dishes to current table. Each call will add only one type of dishes'''
    if amount <= 0:
        return {"message": "Invalid actions with a non-positive number of dishes"}
    else:

        kargs = {}
        for i in range(4):
            kargs[f"dish_{i+1}"] = 0

        var_name = "dish_{}".format(dishes.index(dish_name) + 1)
        # print(dish_name, var_name)
        kargs[var_name] = amount
        # print(kargs)
        order_id = create_new_order(user_id=user_id, **kargs)
        message = f"You placed a new order (ID {order_id}), it contains {dish_name} * {amount}"
        return {"message": message}
    
class FoodMultiInput(BaseModel):
    user_id: str = Field(description="User ID")
    table_id: int = Field(description="Table ID")
    spicy_hot_pot: int = Field(description="The number of Spicy Hot Pot", ge=0, le=99, default=0)
    beef: int = Field(description="The number of beef", ge=0, le=99, default=0)
    hand_torn_cabbage: int = Field(description="The number of Hand-torn cabbage", ge=0, le=99, default=0)
    rice: int = Field(description="The number of Rice", ge=0, le=99, default=0)
    # order_dict: Dict = Field(description="A dict to show the ordered dishes for one table. The name of dish as key and the amount of each dish is used as value")


@tool("add_multiple_dish_to_order", return_direct=True, args_schema=FoodMultiInput)
def add_multiple_dish_to_order(user_id:str, table_id:int=10, spicy_hot_pot:int=0, beef:int=0, hand_torn_cabbage:int=0, rice:int=0) -> Dict:
    '''Add the amount of dishes to current table. Each call can add multiple types of dishes'''

    kargs = {}
    kargs[f"dish_1"] = spicy_hot_pot
    kargs[f"dish_2"] = beef
    kargs[f"dish_3"] = hand_torn_cabbage
    kargs[f"dish_4"] = rice
    
    order_id = create_new_order(user_id=user_id, **kargs)
    # order_id = create_new_order(user_id=user_id, dish_1=dish_1, dish_2=dish_2, dish_3=dish_3, dish_4=dish_4)
    message = f"You placed a new order (ID {order_id}), it contains:\n"
    message += f"Spicy Hot Pot * {spicy_hot_pot}\n"
    message += f"Beef * {beef}\n"
    message += f"Hand-torn cabbage * {hand_torn_cabbage}\n"
    message += f"Rice * {rice}\n"
    return {"message": message}

class CheckOrderInput(BaseModel):
    user_id: str = Field(description="User ID")
    table_id: str = Field(description="Table ID")

# order_dict: Dict = Field(description="A dict to show the ordered dishes for one table. The name of dish as key and the amount of each dish is used as value")

@tool("place_order", return_direct=True, args_schema=CheckOrderInput)
def place_order(user_id: str, table_id: int = 10) -> str:
    '''Place all orders from a table and show cost summary. note: One table can be associated with multiple orders'''
    order_summary = f"Dear customer in table {table_id}, you ordered: "
    total_cost = 0
    order_dict = get_order_dict(user_id=user_id)
    for dish_name in order_dict:
        amount = order_dict[dish_name]
        order_summary += f"{dish_name} * {amount}, "
        total_cost += food_price[dish_name] * amount
    order_summary += f"and in total it cost {total_cost} USD."
    return {"message": order_summary}

@tool("check_out", return_direct=True, args_schema=CheckOrderInput)
def check_out(user_id:str, table_id: int = 10) -> Dict:
    '''Pay bills accoringd to all ordered food in table <table_id>'''
    order_dict = get_order_dict(user_id)
    total_cost = 0
    for dish_name in order_dict:
        amount = order_dict[dish_name]
        total_cost += food_price[dish_name] * amount
    order_summary = f"Dear customer in table {table_id}, you paid bills of tatal {total_cost} USD. Hope you enjoy our food! Have a nice day!"
    return {"message": order_summary}

# DB Operations
from flaskr.db import UserOrder, FoodOrder
from sqlalchemy import update, select, delete
from flaskr.db import get_db_outside
def initialize_restaurant(user_id:str):
    db = get_db_outside()

    q = db.query(UserOrder.user_id).filter(UserOrder.user_id==user_id)
    exist_flag = db.query(q.exists()).scalar()

    if not exist_flag:
        # if there is no record associated with user, create one order with 2 Rice
        # associate that order with the user
        create_new_order(user_id=user_id)

def create_new_order(user_id:str, dish_1:int=0, dish_2:int=0, dish_3:int=0, dish_4:int=2):
    db = get_db_outside()

    q = db.query(FoodOrder.order_id).filter(FoodOrder.dish_1==dish_1, FoodOrder.dish_2==dish_2, FoodOrder.dish_3==dish_3, FoodOrder.dish_4==dish_4)
    exist_flag = db.query(q.exists()).scalar()

    # print("Create new order", exist_flag)

    if exist_flag:
        order_id = q.first()[0]
    else:
        order_id = db.query(FoodOrder).count()
        order_obj = FoodOrder(order_id=order_id, dish_1=dish_1, dish_2=dish_2, dish_3=dish_3, dish_4=dish_4)
        db.add(order_obj)
        db.commit()

    q = db.query(UserOrder.user_id).filter(UserOrder.user_id==user_id, UserOrder.order_id==order_id)
    exist_flag = db.query(q.exists()).scalar()

    if not exist_flag:
        tp_obj = UserOrder(user_id=user_id, table_id=10, order_id=order_id)
        db.add(tp_obj)
        db.commit()

    return order_id

def get_order_dict(user_id:str) -> Dict:
    db = get_db_outside()
    stmt = (
        select(UserOrder.user_id, FoodOrder.dish_1, FoodOrder.dish_2, FoodOrder.dish_3, FoodOrder.dish_4)
        .where(UserOrder.user_id==user_id)
        .join(FoodOrder, UserOrder.order_id == FoodOrder.order_id)
    )
    # print(stmt)
    result = db.execute(stmt).all()
    tp_dict = {}
    for dish in dishes:
        tp_dict[dish] = 0
    for row in result:
        # get all orders associated with user / table 10
        # adding the number of dishes from all orders
        user_id, dish_1, dish_2, dish_3, dish_4 = row
        # print(dish_1, dish_2, dish_3, dish_4)
        for index, dish_name in enumerate(dishes):
            tp_dict[dish_name] += eval(f"dish_{index + 1}")
            # print(dish_name, eval(f"dish_{index + 1}"))
            # It takes dish_1, dish_2, ... to the dict
    return tp_dict
