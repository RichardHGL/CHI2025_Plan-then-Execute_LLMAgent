from langchain.tools import tool, BaseTool
from langchain.pydantic_v1 import BaseModel, Field
from typing import Optional, Type, List, Dict, Literal
from flaskr.db_utli import book_flight_ticket

cities = ['London', 'New York', 'Paris', 'Amsterdam']

class FlightSearchInput(BaseModel):
    departure_city: Literal['London', 'New York', 'Paris', 'Amsterdam'] = Field(description="The departure airport/city")
    arrival_city: Literal['London', 'New York', 'Paris', 'Amsterdam'] = Field(description="The arrival airport/city")
    date: Literal["Today", "Tomorrow"] = Field(description="The date for flight departure")
    timePeriod: Literal["No restriction", "Morning", 'Afternoon', 'Evening'] = Field(description="The period of flight departure. Valid input includes 'no restriction', 'Morning', 'Afternoon', 'evening'")

# to generate more flights 
available_flights = [
    ('Amsterdam', 'London', 'Tomorrow', 'Morning', '7:30 am', 'CA19872'),
    ('Amsterdam', 'London', 'Tomorrow', 'Morning', '9:30 am', 'KN12309'),
    ('Amsterdam', 'London', 'Tomorrow', 'Afternoon', '1:30 pm', 'CZ0923'),
    ('Amsterdam', 'London', 'Tomorrow', 'Evening', '7:30 pm', 'TB0213'),
    ('Amsterdam', 'New York', 'Tomorrow', 'Evening', '9:30 pm', 'CA325'),
    ('Amsterdam', 'Paris', 'Tomorrow', 'Evening', '9:30 am', 'CA442'),
    ('London', 'Amsterdam', 'Tomorrow', 'Morning', '8:30 am', 'KL23313'),
    ('London', 'Amsterdam', 'Tomorrow', 'Morning', '11:30 am', 'JL98642'),
    ('London', 'Amsterdam', 'Tomorrow', 'Afternoon', '3:30 pm', 'CY9962'),
    ('London', 'Amsterdam', 'Tomorrow', 'Evening', '9:30 pm', 'CS3345'),
    ('London', 'New York', 'Tomorrow', 'Evening', '9:30 pm', 'CA666'),
    ('London', 'Paris', 'Tomorrow', 'Evening', '9:30 am', 'CA335'),
    ('Paris', 'Amsterdam', 'Tomorrow', 'Morning', '9:30 am', 'CS4223'),
    ('Paris', 'New York', 'Tomorrow', 'Afternoon', '1:30 pm', 'CA123'),
    ('Paris', 'London', 'Tomorrow', 'Evening', '9:30 am', 'CA764'),
    ('New York', 'Amsterdam', 'Tomorrow', 'Morning', '10:30 am', 'JL7652'),
    ('New York', 'Paris', 'Tomorrow', 'Afternoon', '2:30 pm', 'JL6675'),
    ('New York', 'London', 'Tomorrow', 'Evening', '8:30 am', 'KB1234'),
]

# flight_dict = {
#     'CA19872': ('Amsterdam', 'London', 'Tomorrow', 'Morning', '7:30 am', 'CA19872'),
#     'KN12309': ('Amsterdam', 'London', 'Tomorrow', 'Morning', '9:30 am', 'KN12309'),
#     'CZ0923': ('Amsterdam', 'London', 'Tomorrow', 'Afternoon', '13:30 am', 'CZ0923'),
#     'TB0213': ('Amsterdam', 'London', 'Tomorrow', 'Evening', '19:30 am', 'TB0213'),
#     'KL23313': ('London', 'Amsterdam', 'Tomorrow', 'Morning', '8:30 am', 'KL23313'),
#     'JL98642': ('London', 'Amsterdam', 'Tomorrow', 'Morning', '11:30 am', 'JL98642'),
#     'CY9962': ('London', 'Amsterdam', 'Tomorrow', 'Afternoon', '15:30 am', 'CY9962'),
#     'CS3345': ('London', 'Amsterdam', 'Tomorrow', 'Evening', '21:30 am', 'CS3345')
# }

def validate_flight_search_input(departure_city: str, arrival_city:str, date:str, timePeriod:str):
    if departure_city not in cities:
        return False, "No available flight"
    if arrival_city not in cities:
        return False, "No available flight"
    if date not in ["Today", "Tomorrow"]:
        return False, "No available flight"
    if timePeriod not in ['Morning', 'Afternoon', 'Evening', 'No restriction']:
        return False, "unknown time period: {}".format(timePeriod)
    return True, "valid flight search"

@tool("search_flight", return_direct=True, args_schema=FlightSearchInput)
def search_flight(departure_city: str, arrival_city:str, date:str, timePeriod:str='no restriction') -> Dict:
    '''Search flight based on departure city, arrival city, date for flight, and timeperiod'''
    flag, response = validate_flight_search_input(departure_city, arrival_city, date, timePeriod)
    if flag:
        found_flag = False
        message = "The available flights that fit your needs are:\n"
        message += "Flight ID | Departure City | Arrival City | Departure Date | Departure Time |\n"
        for flight in available_flights:
            departure_city_, arrival_city_, date_, timePeriod_, clock, flight_id = flight
            if departure_city_ == departure_city and arrival_city == arrival_city_ and date == date_:
                if timePeriod == "No restriction":
                    found_flag = True
                    message += f"{flight_id} | {departure_city_} | {arrival_city_} | {date_} | {clock}\n"
                else:
                    if timePeriod == timePeriod_:
                        found_flag = True
                        message += f"{flight_id} | {departure_city_} | {arrival_city_} | {date_} | {clock}\n"
        if found_flag:
            return {"message": message}
        else:
            return {"message": "No flight match with current search"}
    else:
        return {"message": response}

class BookFlightInput(BaseModel):
    user_id: str = Field(description="The unique ID for user")
    # user_name: str = Field(description="The name of user who is supposed to take the flight")
    flight_id: str = Field(description="The unique ID for flight")
    flight_class: Literal["Economic", "Business"] = Field(description="The flight class or seat area.")

@tool("book_flight", return_direct=True, args_schema=BookFlightInput)
def book_flight(user_id: str, flight_id: str, flight_class: str) -> str:
    '''Book a flight for user with flight id, flight class, user name and user id as input'''
    # valid_flight_index = -1
    # for index, flight in enumerate(available_flights):
    #     if flight[-1] == flight_id:
    #         valid_flight_index = index
    #         break
    flight_dict = {}
    for flight in available_flights:
        flight_dict[flight[-1]] = flight
    if flight_id not in flight_dict:
        return {"message": f"Flight {flight_id} does not exist in our system"}
    else:
        departure_city_, arrival_city_, date_, timePeriod_, clock, flight_id = flight_dict[flight_id]
        book_flight_ticket(user_id=user_id, flight_id=flight_id, flight_class=flight_class)
        message = f'''Dear customer, we successfully booked one {flight_class} ticket of flight {flight_id} for you. 
        It will departure from {departure_city_} at {clock} on {date_} and arrive at {arrival_city_}.
        Thanks for your booking at our company! Enjoy your trip!
        '''
        return {"message": message}



# DB operations

from flaskr.db import UserFlight
from sqlalchemy import update, select, delete
from sqlalchemy.orm import Session
from flaskr.db import engine

def book_flight_ticket(user_id:str, flight_id:str, flight_class:str):
    with Session(engine) as db:
        q = db.query(UserFlight.user_id).filter(UserFlight.user_id==user_id, UserFlight.flight_id == flight_id)
        exist_flag = db.query(q.exists()).scalar()
        if not exist_flag:
            tp_obj = UserFlight(user_id=user_id, flight_id=flight_id, flight_class=flight_class)
            db.add(tp_obj)
            db.commit()
            return False
        else:
            return True