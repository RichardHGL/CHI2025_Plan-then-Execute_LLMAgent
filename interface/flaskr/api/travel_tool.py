from langchain.tools import tool, BaseTool
from langchain.pydantic_v1 import BaseModel, Field
from typing import Optional, Type, List, Dict, Literal

# Please plan a trip for me departing on October 1st at 8:00 AM to Japan, returning on October 7th at 11:00 PM, including Tokyo Disneyland, Senso-ji Temple, Ginza, Mount Fuji, Kyoto cultural experience, Universal Studios Osaka, and visiting the Nara Deer Park on October 4th, and help me find hotels where the nightly cost does not exceed 10,000 Japanese yen.

route_1 = '''
Oct 1: 8am - 11am, Senso-ji Temple, 1pm - 5pm city walk
Oct 2: 8am - 5pm, Tokyo Disneyland
Oct 3: 8am - 5pm, Kyoto cultural experience
Oct 4: 8am - 5pm, The Island Shrine of Itsukushima, Miyajima
Oct 5: 8am - 5pm, Mount Fuji
Oct 6: 1pm - 5pm, Ginza
Oct 7: 8am - 5pm, Nara Deer Park
'''

route_2 = '''
Oct 1: 8am - 5pm, Tokyo Disneyland
Oct 2: 8am - 11am, Senso-ji Temple, 1pm - 5pm city walk
Oct 3: 8am - 5pm, Mount Fuji
Oct 4: 8am - 5pm, Nara Deer Park
Oct 5: 8am - 5pm, Kyoto cultural experience
Oct 6: 8am - 5pm, Universal Studios Osaka
Oct 7: 1pm - 5pm, Ginza
'''

route_3 = '''
Oct 1: 8am - 5pm, Arashiyama Monkey Park, Kyoto
Oct 2: 8am - 11am, Senso-ji Temple, 1pm - 5pm city walk
Oct 3: 8am - 5pm, Mount Fuji
Oct 4: 8am - 5pm, Shinjuku Gyoen National Garden, Tokyo
Oct 5: 8am - 5pm, Kyoto cultural experience
Oct 6: 8am - 5pm, Universal Studios Osaka
Oct 7: 1pm - 5pm, Ginza
'''

route_4 = '''Oct 1: 8am - 5pm, Tokyo Disneyland'''
route_5 = '''Oct 7: 1pm - 5pm, Ginza'''

itinerary_message = f'''
We have following recommendations for itinerary:
-----------------
route-1:
{route_1}
-----------------
route-2:
{route_2}
-----------------
route-3:
{route_3}
-----------------
Please choose one route that match your interest.
'''

hotel_plan1 = '''
Oct 1: nestay suite tokyo tabata, 9,735 JPY
Oct 2: Ace Inn Shinjuku, 8,030 JPY
Oct 3: Guesthouse Kyoto Arashiyama, 8,500 JPY
Oct 4: Hotel Trend Iwakuni, 7,568 JPY
Oct 5: Hotel Nishimura, 9,200 JPY
Oct 6: Henn na Hotel Tokyo Ginza, 9,999 JPY
Oct 7: Comfy Stay Sakuramachi, 8,999 JPY
'''

hotel_plan2 = '''
Oct 1: Ace Inn Shinjuku, 8,030 JPY
Oct 2: nestay suite tokyo tabata, 9,735 JPY
Oct 3: Hotel Nishimura, 9,200 JPY
Oct 4: Comfy Stay Sakuramachi, 8,999 JPY
Oct 5: Guesthouse Kyoto Arashiyama, 8,500 JPY
Oct 6: Toyoko Inn Osaka Bentencho, 9,450 JPY
Oct 7: Henn na Hotel Tokyo Ginza, 9,999 JPY
'''

hotel_plan3 = '''
Oct 1: Hotel Sagano, 8,960 JPY
Oct 2: nestay suite tokyo tabata, 9,735 JPY
Oct 3: Hotel Nishimura, 9,200 JPY
Oct 4: Rhodes Kagurazaka, 9,600 JPY
Oct 5: Guesthouse Kyoto Arashiyama, 8,500 JPY
Oct 6: Toyoko Inn Osaka Bentencho, 9,450 JPY
Oct 7: Henn na Hotel Tokyo Ginza, 9,999 JPY
'''

hotel_plan4 = '''Oct 1: Ace Inn Shinjuku, 8,030 JPY'''
hotel_plan5 = '''Oct 7: Henn na Hotel Tokyo Ginza, 9,999 JPY'''

hotel_response_template = '''Dear customer, according to the selected route, we would suggest hotel plan:
-----------------
{hotel_plan}
-----------------
'''

# response_1 = f'''Dear customer, you selected route-1, it is:
# -----------------
# {route_1}
# -----------------
# According to that, we would suggest hotel plan:
# -----------------
# {hotel_plan1}
# -----------------
# '''

# response_2 = f'''Dear customer, you selected route-2, it is:
# -----------------
# {route_2}
# -----------------
# According to that, we would suggest hotel plan:
# -----------------
# {hotel_plan2}
# -----------------
# '''

# response_3 = f'''Dear customer, you selected route-3, it is:
# -----------------
# {route_3}
# -----------------
# According to that, we would suggest hotel plan:
# -----------------
# {hotel_plan3}
# -----------------
# '''

# response_4 = '''Dear customer, you selected route-4, it is:
# -----------------
# Oct 1: 8am - 5pm, Tokyo Disneyland
# -----------------
# According to that, we would suggest hotel plan:
# -----------------
# Oct 1: Ace Inn Shinjuku, 8,030 JPY
# -----------------
# '''

# response_5 = f'''Dear customer, you selected route-5, it is:
# -----------------
# Oct 7: 1pm - 5pm, Ginza
# -----------------
# According to that, we would suggest hotel plan:
# -----------------
# Oct 7: Henn na Hotel Tokyo Ginza, 9,999 JPY
# -----------------
# '''

class ItineraryInput(BaseModel):
    destination: Literal['Japan'] = Field(description="Destination")
    departure_time: Literal['October 1st 8:00 AM', 'October 7th 8:00 AM'] = Field(description="The time to departure")
    return_time: Literal['October 1st 11:00 PM', 'October 7th 11:00 PM'] = Field(description="The time to return")
    interests: str = Field(description="Points of Interest, a list of sites like Tokyo Disneyland, Senso-ji Temple etc.")

@tool("travel_itinerary_planner", return_direct=True, args_schema=ItineraryInput)
def travel_itinerary_planner(destination: str, departure_time:str, return_time: str, interests: str) -> Dict:
    '''Travel Itinerary Planning Tool'''
    # To-do return several planned itinerary: [(Date, activity)]
    d_date = int(departure_time.split(" ")[1][0])
    r_date = int(return_time.split(" ")[1][0])
    if d_date > r_date:
        return {"message": "Wrong dates to arrange itinerary. The return time can not be earlier than the departure time"}
    else:
        if d_date == r_date:
            if d_date == 1:
                return {"message": "The planned trip route-4 is:\nOct 1: 8am - 5pm, Tokyo Disneyland"}
            else:
                return {"message": "The planned trip route-5 is:\nOct 7: 1pm - 5pm, Ginza"}
        else:
            return {"message": itinerary_message}
    # return {"message": "Example itinerary", itinerary: [("Day 1. 8 am", "hotel gathering"), ("Day 1. 10 am", "Hot spring")]}
    

# class HotelSearchInput(BaseModel):
#     location: str = Field(description="Hotel location")
#     check_in_date: Dict = Field(description="Check-in date")
#     check_out_date: Dict = Field(description="Check-out date")
#     guests: Dict = Field(description="Number of guests")
#     city: str = Field(description="City of stay")
#     stay_duration: int = Field(description="Duration of stay")
#     budget: int = Field(description="Budget")
#     room_type: str = Field(description="Room type")
#     number_of_rooms: int = Field(description="Number of rooms")


# @tool("hotel_search", return_direct=True, args_schema=HotelSearchInput)
# def hotel_search(location: str, check_in_date: str, check_out_date: str, guests: int, city: str,
#                   stay_duration:int, budget: int, room_type: str, number_of_rooms: int) -> Dict:
#     '''Search for hotels that meet the criteria and return a list'''
#     return {"message": "no hotels meet your filter criteria"}

class SelectItinerary(BaseModel):
    selection: Literal['route-1', 'route-2', 'route-3', 'route-4', 'route-5'] = Field(description="The option of planned itinerary")

response_template = '''Dear customer, you selected {selection}, it is:
-----------------
{route}
-----------------
'''

@tool("select_itinerary", return_direct=True, args_schema=SelectItinerary)
def select_itinerary(selection: str) -> Dict:
    '''Select one itinerary suggested by the system'''
    if selection == "route-1":
        return {"message": response_template.format(selection=selection, route=route_1)}
    elif selection == "route-2":
        return {"message": response_template.format(selection=selection, route=route_2)}
    elif selection == "route-3":
        return {"message": response_template.format(selection=selection, route=route_3)}
    elif selection == "route-4":
        return {"message": response_template.format(selection=selection, route=route_4)}
    elif selection == "route-5":
        return {"message": response_template.format(selection=selection, route=route_5)}
    return {"message": "Unknown route, please specify a route from the recommendations"}

@tool("hotel_suggestion", return_direct=True, args_schema=SelectItinerary)
def hotel_suggestion(selection: str) -> Dict:
    '''Based on the user selection of the itinerary, arrange hotel plan for user'''
    if selection == "route-1":
        return {"message": hotel_response_template.format(hotel_plan=hotel_plan1)}
    elif selection == "route-2":
        return {"message": hotel_response_template.format(hotel_plan=hotel_plan2)}
    elif selection == "route-3":
        return {"message": hotel_response_template.format(hotel_plan=hotel_plan3)}
    elif selection == "route-4":
        return {"message": hotel_response_template.format(hotel_plan=hotel_plan4)}
    elif selection == "route-5":
        return {"message": hotel_response_template.format(hotel_plan=hotel_plan5)}
    return {"message": "Unknown route, please specify a route from the recommendations"}

# @tool("hotel_arrangement", return_direct=True, args_schema=HotelBookingInput)
# def hotel_arrangement(destination: str, departure_time:str, return_time: str, interests: str) -> str:
#     '''Arrange hotel according to the selected routes'''
#     total_cost = 0
#     return order_summary