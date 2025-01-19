from langchain.tools import tool, BaseTool
from langchain.pydantic_v1 import BaseModel, Field
from typing import Optional, Type, Literal, Union, Tuple

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

# test-113
# Can you help me log into my two different platform accounts and then check their account balances? The first account ID is 12345678, password is Password123; the second account ID is 87654321, password is 123Password.

# test-149
# My account ID is 54321, and the password is PWD2023. I plan to make two foreign exchange transactions. The first is to buy 10,000 euros, and the second is to sell 5,000 US dollars. Please help me operate.

# test-184
# I need to know the detailed information about the 'Happy Savings High Gold' deposit product, including its minimum deposit amount, annual interest rate, and deposit term. Also, I want to use my account number 123456 and password 789123 along with the most recently received verification code 8888 to apply for a loan, and I would like to know the review time for this loan application as well as how to check the status of all my current loan applications.

# test-200
# Please inquire about the current debt amount of my credit card with the last five digits 12345, and deduct the corresponding 12000 RMB from my savings card number 6212345678900011 to repay this debt, then help me check the amount of the outstanding bill for the same credit card within 30 days after today.

class SearchInput(BaseModel):
    query: str = Field(description="should be a search query")

class CustomSearchTool(BaseTool):
    name = "custom_search"
    description = "useful for when you need to answer questions about current events"
    args_schema: Type[BaseModel] = SearchInput

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        return "LangChain"

# @tool
# def multiply(a: int, b: int) -> int:
#     """Multiply two numbers."""
#     return a * b

# @tool("lower_case", return_direct=True)
# def to_lower_case(input:str) -> str:
#   """Returns the input as all lower case."""
#   return input.lower()

class SearchCardInput(BaseModel):
    pattern: Literal['12345', '54321'] = Field(description="numbers or substrings of bank card")
    mode: Literal['startswith', 'endswith'] = Field(description="card starts with the pattern or end with the pattern")


@tool("search_card", return_direct=True, args_schema=SearchCardInput)
def search_card(pattern: str, mode: str) -> str:
    '''search bank card which match with user description of starting with or ending with'''
    all_cards = ['4980981092312345', '6212345678900011']
    if mode == 'endswith':
        for card in all_cards:
            if card.endswith(pattern):
                return {"message": f"We find card {card} match your mention of the last five digits {pattern}"}
    else:
        for card in all_cards:
            if card.startswith(pattern):
                return {"message": f"We find card {card} match your mention of starting with {pattern}"}

class BankLoginInput(BaseModel):
    user_id: str = Field(description="User ID")
    account: str = Field(description="Bank Account ID")
    passwd: str = Field(description="password for bank account")


@tool("bank_account_login", return_direct=True, args_schema=BankLoginInput)
def bank_account_login(user_id: str, account: str, passwd: str) -> str:
    '''Login bank account to check the balance of account account_id, which requires passwd to login'''
    account_pwd_dict = {
        "12345678": "Password123",
        "87654321": "123Password",
        "54321": "PWD2023",
        "123456": "789123"
    }
    if account not in account_pwd_dict:
        return f"account id {account} does not exist"
    else:
        if passwd != account_pwd_dict[account]:
            return "wrong password"
        else:
            return "login successful"

def transfer_balance(balance: Union[int, float]) -> str:
    return "{:,}".format(balance)

def get_balance_str(user_id: str, account: str, passwd: str) -> str:
    balance_dict = check_user_balance(user_id=user_id, account=account, passwd=passwd)
    response = f"You have "
    tp_list = []
    for currency in ['USD', 'RMB', 'JPY', 'EUR']:
        if balance_dict[currency] > 0:
            temp_response = f"{transfer_balance(balance_dict[currency])} {currency}"
            tp_list.append(temp_response)
    if len(tp_list) >= 2:
        response += ", ".join(tp_list[:-1]) + f" and {tp_list[-1]}"
    elif len(tp_list) == 1:
        response += f" {tp_list[0]}"
    else:
        response += "no currency"
    response += " in the account"
    return response

@tool("check_balance", return_direct=True, args_schema=BankLoginInput)
def check_balance(user_id: str, account: str, passwd: str) -> dict:
    '''check the balance of account account_id, which requires login info with account and password'''
    exist_flag = check_login(user_id=user_id, account=account, passwd=passwd)
    if not exist_flag:
        return {"message": f"invalid login information, please check your account and password"}
    response = get_balance_str(user_id=user_id, account=account, passwd=passwd)
    return {"message": response}

# class CurrencyExchangeInput(BaseModel):
#     amount: int = Field(description="The amount of currency")
#     sourceCurrency: Literal['USD', 'RMB', 'JPY', 'EUR']  = Field(description="The source currency name.")
#     targetCurrency: Literal['USD', 'RMB', 'JPY', 'EUR']  = Field(description="The target currency name.")

# @tool("buy_currency", return_direct=True, args_schema=CurrencyExchangeInput)
# def buy_currency(amount: int, sourceCurrency: str='USD', targetCurrency: str = 'USD') -> str:
#     '''Calculate the amount required for sourceCurrency to buy the amount of targetCurrency.
#     When targetCurrency is not USD, set the sourceCurrency as USD.
#     When targetCurrency is USD, set the sourceCurrency as EUR.'''
#     try:
#         exchange_rate = get_exchange_rate(sourceCurrency=sourceCurrency, targetCurrency=targetCurrency)
#         return "conversion_amount {:.2f}".format(amount / exchange_rate)
#     except Exception as e:
#         print(e)
#         return 'Exception: {}. calculation error'.format(e)

# @tool("sell_currency", return_direct=True, args_schema=CurrencyExchangeInput)
# def sell_currency(amount: int, sourceCurrency: str='USD', targetCurrency: str = 'USD') -> str:
#     '''Calculate the amount of targetCurrency with selling the amount of sourceCurrency. 
#     When sourceCurrency is not USD, set the targetCurrency as USD. 
#     When sourceCurrency is USD, set the targetCurrency as EUR.'''
#     try:
#         exchange_rate = get_exchange_rate(sourceCurrency=sourceCurrency, targetCurrency=targetCurrency)
#         return "conversion_amount {:.2f}".format(amount * exchange_rate)
#     except Exception as e:
#         print(e)
#         return 'Exception: {}. calculation error'.format(e)

CURRECY = Literal['USD', 'RMB', 'JPY', 'EUR']

class CurrencyTransactionInput(BaseModel):
    user_id: str = Field(description="User ID")
    account: str = Field(description="Bank Account ID")
    passwd: str = Field(description="password for bank account")
    sourceCurrency: CURRECY = Field(description="The source currency name.")
    targetCurrency: CURRECY = Field(description="The target currency name.")
    amount: float = Field(description="the amount of currency involved in the transaction")

@tool("sell_currency", return_direct=True, args_schema=CurrencyTransactionInput)
def sell_currency(user_id:str, account:str, passwd:str, sourceCurrency:CURRECY, targetCurrency:CURRECY, amount:float):
    '''Calculate the amount of targetCurrency with selling the amount of sourceCurrency.'''
    balance_dict = check_user_balance(user_id=user_id, account=account, passwd=passwd)
    source_amount = amount
    if balance_dict[sourceCurrency] < source_amount:
        return {"message": f"Your account {account} do not have enough {sourceCurrency} to sell"}
    exchange_rate = get_exchange_rate(sourceCurrency=sourceCurrency, targetCurrency=targetCurrency)
    target_increase = exchange_rate * source_amount
    update_dict = {
        sourceCurrency: balance_dict[sourceCurrency] - source_amount,
        targetCurrency: balance_dict[targetCurrency] + target_increase
    }
    update_account_balance(user_id=user_id, account=account, passwd=passwd, args=update_dict)

    response = f"You successfully selled {transfer_balance(amount)} * {sourceCurrency} to {transfer_balance(target_increase)} {targetCurrency}\n After transaction, "

    response += get_balance_str(user_id=user_id, account=account, passwd=passwd)
    return {"message": response}

@tool("buy_currency", return_direct=True, args_schema=CurrencyTransactionInput)
def buy_currency(user_id:str, account:str, passwd:str, sourceCurrency:CURRECY, targetCurrency:CURRECY, amount:float):
    '''Calculate the amount required for sourceCurrency to buy the amount of targetCurrency.'''
    balance_dict = check_user_balance(user_id=user_id, account=account, passwd=passwd)
    target_amount = amount

    #ensure that user have enough sourceCurrency to by target_amount * targetCurrency
    exchange_rate = get_exchange_rate(sourceCurrency=sourceCurrency, targetCurrency=targetCurrency)
    source_amount = target_amount / exchange_rate
    if balance_dict[sourceCurrency] < source_amount:
        return {"message": f"Your account {account} do not have enough {sourceCurrency} to buy currency"}
    
    update_dict = {
        sourceCurrency: balance_dict[sourceCurrency] - source_amount,
        targetCurrency: balance_dict[targetCurrency] + target_amount
    }
    update_account_balance(user_id=user_id, account=account, passwd=passwd, args=update_dict)
    response = f"You successfully bought {transfer_balance(target_amount)} {targetCurrency} with {transfer_balance(source_amount)} * {sourceCurrency}\n After transaction, "

    response += get_balance_str(user_id=user_id, account=account, passwd=passwd)
    return {"message": response}

def get_exchange_rate(sourceCurrency: CURRECY, targetCurrency: CURRECY) -> dict:
    '''Get exchange rate from sourceCurrency to targetCurrency.'''
    val_dict = {
        "USD": 7.2,
        "RMB": 1.0,
        "EUR": 7.83,
        "JPY": 0.048
    }
    if sourceCurrency == targetCurrency:
        return {"exchange_rate": 1.0, "error": None}
    else:
        return val_dict[sourceCurrency] / val_dict[targetCurrency]

# To-do provide more deposit product here
class DepositProduct(BaseModel):
    product_name: Literal["Happy Savings High Gold", "Business Growth Deposit", "Enterprise Fixed Income"] = Field(description="The name for deposit product.")

# Business Growth Deposit: Minimum deposit amount: $50,000, Annual interest rate: 2.5%, Deposit term: 2 years
# Corporate Flexi-Saver: Minimum deposit amount: $25,000, Annual interest rate: 2.0%, Deposit term: Flexible, with no penalty for early withdrawal
# Enterprise Fixed Income: Minimum deposit amount: $100,000, Annual interest rate: 3.0%, Deposit term: 5 years
# Business Bonus Saver: Minimum deposit amount: $10,000, Annual interest rate: 1.8%, Deposit term: 1 year, with a bonus interest rate if no withdrawals are made
# Commercial Term Deposit: Minimum deposit amount: $50,000, Annual interest rate: 2.3%, Deposit term: 3 months to 5 years, with varying rates based on term length

@tool("check_deposite_product", return_direct=True, args_schema=DepositProduct)
def check_deposite_product(product_name: str) -> dict:
    '''Get detailed information about deposite product with a product name.'''
    val_dict = {
        "Happy Savings High Gold": "minimum deposit amount: 100,000 EUR, annual interest rate: 3.2%, and deposit term: 3 years",
        "Business Growth Deposit": "Minimum deposit amount: $50,000, Annual interest rate: 2.5%, Deposit term: 2 years",
        "Corporate Flexi-Saver": "Minimum deposit amount: $25,000, Annual interest rate: 2.0%, Deposit term: Flexible, with no penalty for early withdrawal",
        "Enterprise Fixed Income": "Minimum deposit amount: $100,000, Annual interest rate: 3.0%, Deposit term: 5 years",
        "Business Bonus Saver": "Minimum deposit amount: $10,000, Annual interest rate: 1.8%, Deposit term: 1 year, with a bonus interest rate if no withdrawals are made",
        "Commercial Term Deposit": "Minimum deposit amount: $50,000, Annual interest rate: 2.3%, Deposit term: 3 months to 5 years, with varying rates based on term length"
    }
    if product_name not in val_dict:
        return {"message": f"There is no product with name {product_name}"}
    else:
        return {"message": f"Desposit Product {product_name}:\n{val_dict[product_name]}"}

class LoanApplicationInput(BaseModel):
    user_id: str = Field(description="User ID")
    account: str = Field(description="Bank Account ID")
    passwd: str = Field(description="password for bank account")
    verification: str = Field(description="Verification code from phone")

@tool("loan_application", return_direct=True, args_schema=LoanApplicationInput)
def loan_application(user_id:str, account:str, passwd:str, verification:str):
    '''Apply loan with user account information and verification code.'''
    if account == "123456" and passwd == "789123" and verification == "8888":
        flag = create_user_loan(user_id=user_id, loan_id='IG987189', loan_status='submitted', submission_time='2 mins ago', review_time='2 weeks')
        if flag:
            return {"message": "loan application IG987189 is submited 2 mins ago, the expected review time will be 2 weeks"}
        else:
            return {"message": "You have submitted loan application IG987189 ealier, it's still under check, the expected review time will be 2 weeks"}
    else:
        return {"message": "loan application failed, please check your login info"}

@tool("check_loan_status", return_direct=True, args_schema=LoanApplicationInput)
def check_loan_status(user_id, account:str, passwd:str, verification:str):
    '''Check the loan status of user, login info and verification code required'''
    prefix = ''' After checking the loan applications associated with your account, we found:
        -----------------------
        Loan ID | Loan status| submission time | expected review time |
    '''
    format_string = "{} | {} | {} | {} |\n"
    suffix = "-----------------------\n"
    if account == "123456" and passwd == "789123" and verification == "8888":
        user_loans = get_user_loans(user_id=user_id)
        response = ""
        for loan_id, loan_status, submission_time, review_time in user_loans:
            response += format_string.format(loan_id, loan_status, submission_time, review_time)
        response = prefix + response + suffix
        return {"message": response}
    # ''' After checking the loan applications associated with your account, we found:
    #     -----------------------
    #     Loan ID | Loan status| submission time | expected review time |
    #     IG987189 | submitted | 2 mins ago | 2 weeks |
    #     IG878193 | rejected | 2 months ago | - |
    #     AJ092813 | approved | 2 years ago | - |
    #     -----------------------
    #     '''
    else:
        return {"message": "login failed, please check your login info"}

class BankTransferInput(BaseModel):
    user_id: str = Field(description="User ID")
    source_card: str = Field(description="Source bank card, which will transfer money out")
    target_card: str = Field(description="Target bank card, which will receive the transferred money")
    amount: float = Field(description="The amount to transfer from source card")

@tool("pay_credit_card", return_direct=True, args_schema=BankTransferInput)
def pay_credit_card(user_id:str, source_card:str, target_card:str, amount:float=12000):
    '''Pay credit card (target card) with bank transfer from source card with a specified amount of transferation.'''
    flag_1, original_debt = get_card_balance(user_id=user_id, card=target_card)
    flag_2, original_deposit = get_card_balance(user_id=user_id, card=source_card)
    if not flag_1:
        return {"message": f"You do not have a card with number {target_card}"}
    if not flag_2:
        return {"message": f"You do not have a card with number {source_card}"}

    reserved_deposit = original_deposit - amount
    if reserved_deposit < 0:
        return {"message": f"Bank transfer failed, card {source_card} only has {transfer_balance(original_deposit)} USD, which is less than {transfer_balance(amount)}"}

    update_card_balance(user_id=user_id, card=source_card, balance= original_deposit - amount)
    update_card_balance(user_id=user_id, card=source_card, balance= original_debt + amount)
    response = f'''Bank transfer successful, you deducted {transfer_balance(amount)} USD from card {source_card} to credit card {target_card}.
    After transfer, you still have {transfer_balance(reserved_deposit)} USD in card {source_card}.
    Before transfer, the credit card {target_card} has 10,000 in debt. After debt payment, you have 2,000 USD as saving on this credit card.'''
    return {"message": response}
    # return '''Bank transfer successful, you deducted 12,000 RMB from card 6212345678900011 to credit card 4980981092312345.
    # After transfer, you still have 78,325.4 RMB in card 6212345678900011.
    # The credit card has 10,000 in debt. After debt payment, you still have 2,000 RMB on this credit card.'''

class CreditCardCheckInput(BaseModel):
    card: str = Field(description="Credit card Number")
    period: int = Field(description="The outstanding bill period, number of days, integer")

class DebtInquiryInput(BaseModel):
    user_id: str = Field(description="User ID")
    card: str = Field(description="credit card number, which will be used for debt inquiry")

@tool("check_credit_card_debt", return_direct=True, args_schema=DebtInquiryInput)
def check_credit_card_debt(user_id:str, card:str):
    '''Check credit card debt amount'''
    if card == "4980981092312345":
        flag_1, original_debt = get_card_balance(user_id=user_id, card=card)
        if not flag_1:
            return {"message": f"You do not have a card with number {card}"}
        return {"message": f"Dear customer, your card 4980981092312345 have {transfer_balance(abs(original_debt))} USD to pay"}
    else:
        return {"message": f"Card {card} is not a credit card"}

@tool("check_credit_card_bills", return_direct=True, args_schema=CreditCardCheckInput)
def check_credit_card_bills(card:str, period:int=30):
    '''Check credit card outstanding bills in a period (30 days in default)'''
    if card == "4980981092312345":
        prefix = '''Dear customer, you still have five bills to pay in the next 30 days:
        -----------------------
        '''
        events = [
            ("Iphone 13 - 24 months split, 529 USD", 5),
            ("Coles supermarket, 345 USD", 10),
            ("McDonald, 25 USD", 18),
            ("Gold purchase, 10,000 USD", 32),
            ("Hospital PA pharmacy, 3,243 USD", 52),
        ]
        format_string = "{}. {}, due: within {} days\n"
        response = ""
        for index, (event_string, days) in enumerate(events):
            if days <= period:
                response += format_string.format(index + 1, event_string, days)
        suffix = '''-----------------------
        Please pay your bills in time
        '''
        return {"message": prefix + response + suffix}
        # '''Dear customer, you still have five bills to pay in the next 30 days:
        # -----------------------
        # 1. Iphone 13, 7,399 RMB, due: within 5 days
        # 2. Coles supermarket, 2,345 RMB, due: within 10 days
        # 3. McDonald, 125 RMB, due: within 18 days
        # 4. Gold purchase, 10,000 RMB, due: within 22 days
        # 5. Hospital PA pharmacy, 3,243 RMB, due: within 29 days
        # -----------------------
        # Please pay your bills in time
        # '''
    else:
        return {"message": "You have no bills to pay"}


# DB operations
from flaskr.db import UserBalance, LoanStatus, CardBalance, get_db_outside
from sqlalchemy import update, select, delete

def check_login(user_id:str, account:str, passwd:str):
    db = get_db_outside()
    # with Session(engine) as db:
    # step-1 search alarm in table alarm, get tp_index as alarm_id
    q = db.query(UserBalance).filter(UserBalance.user_id == user_id, UserBalance.account == account, UserBalance.passwd == passwd)
    exist_flag = db.query(q.exists()).scalar()
    return exist_flag

def check_user_balance(user_id:str, account:str, passwd:str) -> dict:
    balance_dict = {}

    db = get_db_outside()

    q = db.query(UserBalance.USD, UserBalance.RMB, UserBalance.JPY, UserBalance.EUR).filter(UserBalance.user_id == user_id, UserBalance.account == account, UserBalance.passwd == passwd)
    
    balance_dict['USD'], balance_dict['RMB'], balance_dict['JPY'], balance_dict['EUR'] = q.first()
    return balance_dict


def create_user_balance(user_id:str, account:str, passwd:str, args:dict={}):
    new_args = {}
    for currrency in ['USD', 'RMB', 'JPY', 'EUR']:
        new_args[currrency] = args.get(currrency, 0)

    db = get_db_outside()
    
    q = db.query(UserBalance).filter(UserBalance.user_id == user_id, UserBalance.account == account, UserBalance.passwd == passwd)
    exist_flag = db.query(q.exists()).scalar()
    if not exist_flag:
        tp_obj = UserBalance(user_id=user_id, account=account, passwd=passwd, **new_args)
        db.add(tp_obj)
        db.commit()
        return True
    return False

# function for loan
def get_user_loans(user_id:str):
    db = get_db_outside()
    stmt = (
        select(LoanStatus.loan_id, LoanStatus.loan_status, LoanStatus.submission_time, LoanStatus.review_time)
        .where(LoanStatus.user_id==user_id)
    )
    # print(stmt)
    user_loans = []
    result = db.execute(stmt).all()
    for row in result:
        loan_id, loan_status, submission_time, review_time = row
        # print(row[1])
        user_loans.append((loan_id, loan_status, submission_time, review_time))
    return user_loans

def create_user_loan(user_id:str, loan_id:str, loan_status:str, submission_time:str, review_time:str):
    db = get_db_outside()
    q = db.query(LoanStatus).filter(LoanStatus.user_id == user_id, LoanStatus.loan_id == loan_id)
    exist_flag = db.query(q.exists()).scalar()
    if not exist_flag:
        tp_obj = LoanStatus(user_id=user_id, loan_id=loan_id, loan_status=loan_status, submission_time=submission_time, review_time=review_time)
        db.add(tp_obj)
        db.commit()
        return True
    return False

def update_account_balance(user_id:str, account:str, passwd:str, args:dict={}):
    # it must exist in db, it's checked before using this function
    
    # it ensure, we only have valid args to be updated
    new_args = {}
    for currrency in ['USD', 'RMB', 'JPY', 'EUR']:
        if currrency in args:
            new_args[currrency] = args[currrency]
    
    if len(args) == 0:
        # no value to update
        return True
    
    db = get_db_outside()
    
    update_stmt = update(UserBalance).where(UserBalance.user_id == user_id, UserBalance.account==account, UserBalance.passwd==passwd).values(**new_args)
    print(update_stmt)
    db.execute(update_stmt)
    db.commit()
    return True

def create_card_balance(card:str, card_type:str, user_id:str, balance: float):
    db = get_db_outside()
    q = db.query(CardBalance).filter(CardBalance.card == card, CardBalance.user_id == user_id)
    exist_flag = db.query(q.exists()).scalar()
    if not exist_flag:
        tp_obj = CardBalance(card=card, card_type=card_type, user_id=user_id, balance=balance)
        db.add(tp_obj)
        db.commit()
        return True
    return False

def get_card_balance(user_id:str, card:str) -> Tuple[bool, Union[float, int]]:
    # it must exist in db, it's checked before using this function
    
    # it ensure, we only have valid args to be updated
    
    db = get_db_outside()
    q = db.query(CardBalance.balance).filter(CardBalance.user_id==user_id, CardBalance.card==card)
    exist_flag = db.query(q.exists()).scalar()
    # For this task, we ensure user card is available before execution

    if not exist_flag:
        return False, -1
    
    balance = q.first()[0]
    return True, balance

def update_card_balance(user_id:str, card:str, balance:float):
    # it must exist in db, it's checked before using this function
    
    # it ensure, we only have valid args to be updated
    
    db = get_db_outside()
    
    update_stmt = update(CardBalance).where(CardBalance.card == card, CardBalance.user_id==user_id).values(balance=balance)
    print(update_stmt)
    db.execute(update_stmt)
    db.commit()
    return True

# test-200
# Please inquire about the current debt amount of my credit card with the last five digits 12345, and deduct the corresponding 12000 RMB from my savings card number 6212345678900011 to repay this debt, then help me check the amount of the outstanding bill for the same credit card within 30 days after today.

def finance_initilize(user_id:str):
    # for task test-113, check balance
    create_user_balance(user_id=user_id, account="12345678", passwd="Password123", args={'USD': 1000, 'EUR': 5000})
    create_user_balance(user_id=user_id, account="87654321", passwd="123Password", args={'USD': 3000, 'EUR': 1000})

    # for task test-149, foreign currency transaction
    create_user_balance(user_id=user_id, account="54321", passwd="PWD2023", args={'USD': 32000, 'EUR': 50000})

    #     IG878193 | rejected | 2 months ago | - |
    #     AJ092813 | approved | 2 years ago | - |

    # for task test-184, loan application
    create_user_loan(user_id=user_id, loan_id="IG878193", loan_status="rejected", submission_time="2 months ago", review_time= "-")
    create_user_loan(user_id=user_id, loan_id="AJ092813", loan_status="approved", submission_time="2 years ago", review_time= "-")
    
    # for task test-200, credit card
    create_card_balance(card='6212345678900011', card_type='saving card', user_id=user_id, balance=90325.4)
    create_card_balance(card='4980981092312345', card_type='credit card', user_id=user_id, balance=-12000.0)