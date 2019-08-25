import scipy.optimize
import numpy as np
import sys


def pay_monthly_on_loan(initial_value, apr, duration_years, monthly_payment):
    principal = {0:initial_value}
    for year in np.arange(1,duration_years):
        principal[year] = principal[year-1] * apr - 12 * monthly_payment
    return principal[year]

def find_monthly_payment(loan_value, apr, duration_years):
    principal_remaining = lambda monthly_payment : pay_monthly_on_loan(loan_value, apr, duration_years, monthly_payment)
    # Use a Brent gradient approach method of solving roots to determine the proper value
    payment_needed = scipy.optimize.brentq(principal_remaining, 0, loan_value * (apr**duration_years))
    return round(payment_needed)


def pay_yearly_on_loan(initial_value, apr, duration_years, yearly_payment):
    principal = {0:initial_value}
    for year in np.arange(1,duration_years):
        principal[year] = principal[year-1] * apr - yearly_payment
    return principal[year]

def find_yearly_payment(loan_value, apr, duration_years):
    principal_remaining = lambda yearly_payment : pay_yearly_on_loan(loan_value, apr, duration_years, yearly_payment)
    # Use a Brent gradient approach method of solving roots to determine the proper value
    payment_needed = scipy.optimize.brentq(principal_remaining, 0, loan_value * (apr**duration_years))
    return round(payment_needed)


if __name__ is '__main__':
	loan_value = 400 * 1000
	apr = 1.05
	monthly_30 = find_monthly_payment(loan_value, apr, 30)
	monthly_15 = find_monthly_payment(loan_value, apr, 15)
	paid_30 = monthly_30 * 12 * 30
	paid_15 = monthly_15 * 12 * 15
	print(f'For {loan_value}@{apr}, the 30-year payment is {monthly_30} while it\'s {monthly_15} for 15, totalling {paid_30} and {paid_15} respectively')
