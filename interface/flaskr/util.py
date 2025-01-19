import numpy as np
import pandas as pd
from random import choices
from string import ascii_letters

def load_loan_data(data_file="/Users/ghe/PhD/research/Projects/ARCHIE/web/loan_data_selection/selected_samples.csv"):
	df = pd.read_csv(data_file)
	data_dict = {}
	for i in range(len(df)):
		tp_data = LoanData(df.iloc[i,:].tolist())
		data_dict[tp_data.Loan_ID] = tp_data
	# print(data_dict['LP001518'].print_loan_task())
	return data_dict

vaccine_analogy = "The system is <strong>75%</strong> accurate, which is as reliable as the AstraZeneca vaccine to protect against covid"
# vaccine_analogy = "The system is 90% accurate, which is about as reliable as the Pfizer vaccine is for protecting against covid (which is between 90 and 95%"
train_analogy = "The system is <strong>75%</strong> accurate, which is about as reliable as the French trains are on punctuality"
weather_analogy = "the system is <strong>75%</strong> accurate, which is about as accurate as the five day weather forecast"
# example_ID_list = ['LP001518', 'LP002723']
task_ID_list = ['LP001030', 'LP001806', 'LP002534', 'LP001882', 'LP002068', 'LP001849', 'LP002142', 'LP001451', 'LP002181', 'LP002840']
task_ID_mapping = {
	'LP001518': 'Jdk12380',
	'LP002723': 'GbF02909',
	'LP001030': 'gzx12398',
	'LP001806': 'obS23678',
	'LP002534': 'OoU19287',
	'LP001882': 'Psq98134',
	'LP002068': 'LjW96235',
	'LP001849': 'WjZ12687',
	'LP002142': 'QJn78681',
	'LP001451': 'BBQ98172',
	'LP002181': 'GSn12309',
	'LP002840': 'NSG63930'
}

def return_img_stream(img_local_path):
    import base64
    img_stream = ''
    with open(img_local_path, 'rb') as img_f:
        img_stream = img_f.read()
        img_stream = base64.b64encode(img_stream).decode()
    return img_stream

class LoanData(object):

	def __init__(self, loan_task):
		Loan_ID,Gender,Married,Dependents,Education,Self_Employed,ApplicantIncome,CoapplicantIncome, \
		LoanAmount,Loan_Amount_Term,Credit_History,Property_Area,Loan_Status,Prediction_Score,Rank_By_Score,Sample_Category = loan_task
		self.Loan_ID = Loan_ID
		self.rand_ID = task_ID_mapping[Loan_ID]
		self.Gender = Gender
		self.Married = Married
		self.Dependents = str(Dependents)
		self.Self_Employed = Self_Employed
		self.Education = Education
		self.ApplicantIncome = self.deal_int(ApplicantIncome)
		self.CoapplicantIncome = self.deal_int(CoapplicantIncome)
		self.LoanAmount = self.deal_int(LoanAmount)
		self.Loan_Amount_Term = self.deal_int(Loan_Amount_Term)
		if Credit_History is not None:
			if Credit_History == 1.0:
				self.Credit_History = "Yes"
			else:
				self.Credit_History = "No"
		else:
			self.Credit_History = "NA"
		self.Property_Area = Property_Area
		self.Loan_Status = Loan_Status
		self.Prediction_Score = float(Prediction_Score)

	@staticmethod
	def deal_int(value):
		if value is not None:
			out_str = "%d"%(value)
		else:
			out_str = "0"
		return out_str

	def print_loan_task(self):
		# loan_str = "Statistics for loan applicant: "
		loan_str = ""
		loan_str += "Loan Applicant %s, %s"%(self.rand_ID, self.Gender.lower())
		loan_str += ", {}".format("married" if self.Married == "Yes" else "single")
		loan_str += ", with %s dependent(s)"%(self.Dependents)
		if self.Self_Employed == "Yes":
			loan_str += ", self employed."
		else:
			loan_str += "."
		loan_str += " {} has{} graduated from college.".format("He" if self.Gender == "Male" else "She", "n't" if 'Not' in self.Education else "")
		# if 'Not' in self.Education:
		# 	loan_str += " {} has{} graduated from college".format("He" if self.Gender == "Male" else "She")
		# else:
		# 	loan_str += " He (She) has graduated from college"
		loan_str += " Applicant's income is %s dollars per month"%(self.ApplicantIncome)
		loan_str += ", coapplicant's income is %s dollars per month"%(self.CoapplicantIncome)
		# if self.LoanAmount is not None:
		loan_str += ". %s loan amount is %s thousand dollars in total"%("His" if self.Gender == "Male" else "Her", self.LoanAmount)
		# if self.Loan_Amount_Term is not None:
		loan_str += ", and loan term is %s months"%(self.Loan_Amount_Term)
		loan_str += ". {} {} credit history".format("He" if self.Gender == "Male" else "She", "has" if self.Credit_History == "Yes" else "doesn't have")
		# if self.Credit_History == "Yes":
		# 	loan_str += ". He (She) has credit history"
		# else:
		# 	loan_str += ". He (She) doesn't have credit history"
		# if self.Property_Area is not None:
		loan_str += ", and possesses property at %s area."%(self.Property_Area)
		# loan_str += " Do you think we should lend money to {}?".format("him" if self.Gender == "Male" else "her")
		return loan_str

	def serize(self):
		# return jsonify(Loan_ID=self.Loan_ID, Education=self.Education, ApplicantIncome=self.ApplicantIncome,
		#  CoapplicantIncome=self.CoapplicantIncome, LoanAmount=self.LoanAmount, Loan_Amount_Term=self.Loan_Amount_Term,
		#  Credit_History=self.Credit_History, Property_Area=self.Property_Area, Loan_Status=self.Loan_Status)
		# Use rand_ID to show, to avoid users access to real Loan_ID
		return {
			"Loan_ID": self.rand_ID,
			"Gender": self.Gender,
			"Married": self.Married,
			"Dependents": self.Dependents,
			"Self_Employed": self.Self_Employed,
			"Education": self.Education,
			"ApplicantIncome": self.ApplicantIncome,
			"CoapplicantIncome": self.CoapplicantIncome,
			"LoanAmount": self.LoanAmount + " k",
			"Loan_Amount_Term": self.Loan_Amount_Term,
			"Credit_History": self.Credit_History,
			"Property_Area": self.Property_Area,
			"Prediction_Score": self.Prediction_Score,
			"Loan_Status": self.Loan_Status
		}


if __name__ == '__main__':
	data_dict = load_loan_data()
	# print(data_dict)
