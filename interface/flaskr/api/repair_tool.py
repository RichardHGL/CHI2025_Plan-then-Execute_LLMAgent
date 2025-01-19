from langchain.tools import tool, BaseTool
from langchain.pydantic_v1 import BaseModel, Field
from typing import Optional, Type, List, Dict, Literal
import numpy as np


repair_service_point = {
    "Sony": [
        ("Sony01", "Sydney Street, 2632 GB", 2.3, "sonyservice_03@xx.com", "+xx 86420915"), 
        ("Sony03", "Charley Town, 6523 HC", 3.7, "sonyservice_09@xx.com", "+xx 782038431")
    ],
    "Apple": [
        ("Apple02", "Roma Street, 2632 LD", 15.6, "appleservice_23@xx.com", "+xx 123456789"), 
        ("Apple04", "Milan valey, 3678 HB", 5, "appleservice_19@xx.com", "+xx 654321789")
    ],
    "Samsung": [
        ("Samsung05", "Adelaide Street, 5240 ZL", 15.6, "samsungservice_62@xx.com", "+xx 564321789"), 
        ("Samsung06", "Logan Road, 4122 QP", 5, "samsungservice_55@xx.com", "+xx 621345609")
    ]
}

class UserInfoInput(BaseModel):
    user_id: str = Field(description="user name / ID")


@tool("obtain_user_info", return_direct=True, args_schema=UserInfoInput)
def obtain_user_info(user_id: str) -> Dict:
    '''Obtain user contact information, including email, phone and address'''
    message = f"Some user info details:\n"
    message += '-'* 17
    message += '\n'
    message += "Email: zxcasd_pql.com\nPhone: +xx 25364719\n"
    message += "Address: xyz street PQD\n"
    return {"message": message}


class SearchServiceInput(BaseModel):
    brand: Literal["Apple", "Sony", "Samsung"] = Field(description="The brand of electronics")
    

@tool("search_service_provider", return_direct=True, args_schema=SearchServiceInput)
def search_service_provider(brand: Literal["Apple", "Sony", "Samsung"]) -> Dict:
    '''Search for the repair service provider with brand name'''
    if brand in repair_service_point:
        message = f"We found following service point for {brand}:\n"
        message += '-'* 17
        message += '\n'
        for service_id, address, distance, email, phone in repair_service_point[brand]:
            message += f"{service_id}, {address}, with a distance of {distance} with email {email} and phone number: {phone}\n\n"
        return {"message": message, "service_provider": repair_service_point[brand]}
    else:
        return {"message": f"I do not find any service provide for brand {brand}"}

class ServiceProviderInput(BaseModel):
    brand: Literal["Apple", "Sony", "Samsung"] = Field(description="The list of repair service points")

@tool("select_service_provider", return_direct=True, args_schema=ServiceProviderInput)
def select_service_provider(brand: Literal["Apple", "Sony", "Samsung"]) -> Dict:
    '''Select the nearest service point for further info'''
    shortest_distance = 100000
    contact_info = None
    message = ""
    service_provider = repair_service_point[brand]
    for service_id, address, distance, email, phone in service_provider:
        if distance < shortest_distance:
            contact_info = (email, phone)
            shortest_distance = distance
            message = f"We decided to contact service point {service_id}: {address}, with a distance of {distance} km, with email {email} and phone number: {phone}\n"
    return {"message": message, "contact info": contact_info}

class RepairRequestInput(BaseModel):
    applianceType: Literal['TV', 'Fridge', 'Light'] = Field(description="The type of appliance for repair")
    applianceModel: Literal['X800H', 'X900H', 'Z500L'] = Field(description="The unique model for the appliance for repair")
    servicepointID: Literal['Sony01', 'Sony03', 'Apple02', 'Apple04', 'Samsung05', 'Samsung06'] = Field(description="The unique ID of the repair service point")
    issueDescription: Literal["Screen issue", "Battery issue", "Refund"] = Field(description="The description of issues for repairement", default='Screen issue')
    contact_info: str = Field(description="The contact information of customer includes email and phone number", default='zxcasd_pql.com, +xx 25364719 (autofilled by assistant)')
    address: str = Field(description="The address of the customer", default='xyz street PQD (autofilled by assistant)')
    appointment_time: str = Field(description="The time to check the appliance")

def generate_reservation_number():
    prefix = np.random.choice(['C', 'J', 'K', "L", "R"], 1)
    number = np.random.randint(low=10000, high=99999, size=1)
    return f"{prefix}{number}"

@tool("appliance_repair_request", return_direct=True, args_schema=RepairRequestInput)
def appliance_repair_request(applianceType: str, applianceModel: str, servicepointID:str, issueDescription: str, contact_info: str, address: str, appointment_time:str) -> Dict:
    '''Request a repair service to customer's address, '''
    reservation_number = generate_reservation_number()
    message = f'''
    Dear customer, we have received your repair request {reservation_number}.
    We will arrange repair service to your address: {address} at {appointment_time}.
    Here, we try to resend you details of the request, please contact us if anything is wrong:
    --------------
    Appliance Type: {applianceType}
    Appliance Model: {applianceModel}
    Service Point: {servicepointID}
    Issue Description: {issueDescription}
    Your contact information: {contact_info}
    --------------
    '''
    return {"message": message, "reservation_number": reservation_number}