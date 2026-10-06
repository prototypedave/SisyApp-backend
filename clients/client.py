import datetime

class Client:
    def __init__(self, first_name, last_name, id_number, gender, mobile):
        self.fullname = first_name + " " + last_name
        self.id = id_number
        self.gender = gender
        self.mobile = mobile
        self.current_loan = 0
        self.loan_limit = 0
        self.is_record_good = True
        self.requests = 0
        self.current_payments = []

    def __setjob__(self, occupation, title, salary, company):
        self.job = occupation
        self.title = title
        self.salary = salary
        self.company = company

    # not currently necessary but might be later on
    def __setothercontacts__(self, name, mobile):
        self.alias = name
        self.alias_mobile = mobile

    # Assumes first loan amount is given based on physical word
    def __first_request__(self, amount, number_of_days):
        self.current_loan = amount
        self.repay_days = number_of_days
        self.loan_limit = amount
        self.requests += 1
        self.date = datetime.datetime.date()
            
    # Set loan limit based on previous record
    def __setloanlimit__(self):
        if self.is_record_good > 2:
            self.loan_limit = 1.4 * self.loan_limit
        else:
            self.loan_limit = 0.4 * self.loan_limit

    def loan_request(self, amount, number_of_days):
        if self.loan_limit == amount:
            self.current_loan = amount
            self.repay_days = number_of_days
            self.requests += 1
            self.date = datetime.datetime.date()

    def repay_loan(self, amount):
        self.current_loan = self.current_loan - amount
        self.current_payments.append({"amount": amount, "date": datetime.datetime.date()})
        if self.current_loan:
            return "Amount still pending is " + self.current_loan
        if self.request % 3:
            # update loan limit based on repayment
            self.__setloanlimit__()
        
        return "Loan repaid in full. Thank you"
    
    def get_client_profile(self):
        # poll db to return entire record in full return dict
        return {}