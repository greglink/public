#!/usr/bin/env python3

import GLFinancial as glf

def get_vh_fm():
	fm = glf.FinancialModel('Very High Salary')
	# Income
	fm.add_yearly(225 * 1000, 'Salary', year_end=20, agi_impacting=True)

	# Housing
	fm.add_monthly(-3000, 'Rent', year_end=2)
	# Now we buy a 375,000 house, spending 75,000 on down payment, and taking a loan for the rest
	# The loan APR is actually 5%, but since all math is done in current-value dollars, we reduce by ~2% for inflation
	home_sale_price = 375 * 1000
	fm.add_single(-0.2 * home_sale_price , 'Home Down Payment', 3)
	fm.add_loan(0.8 * home_sale_price, 'Mortgage', 15, year_start=3, apr=1.03)
	fm.add_yearly(-0.02 * home_sale_price, 'Home Maintenance, Insurance, Etc', year_start=3)
	# OPTIONAL: Some people include their home value in their net worth, and thus appreciation/etc. Since I don't plan to sell, I don't count it.
	# fm.add_single(375 * 1000, 'Home', year_start=3)

	# Explicit Investing (Brokerage is handled/assumed as all cash left over yearly)
	fm.add_yearly(-19000, '401k Savings', yearly_nw_amount=19000, year_end=20, agi_impacting=True)
	fm.add_yearly(-5000, 'IRA Savings', yearly_nw_amount=5000, year_end=20)

	# Expenses/Cost of Living
	fm.add_monthly(-400, 'Auto Costs', apr=1.01)
	fm.add_monthly(-3000, 'Monthly Spend')
	fm.add_yearly(-12000, 'Yearly Spend')
	return fm

def get_h_fm():
	fm = glf.FinancialModel('High Salary')
	# Income
	fm.add_yearly(175 * 1000, 'Salary', year_end=20, agi_impacting=True)

	# Housing
	fm.add_monthly(-3000, 'Rent', year_end=2)
	# Now we buy a 375,000 house, spending 75,000 on down payment, and taking a loan for the rest
	# The loan APR is actually 5%, but since all math is done in current-value dollars, we reduce by ~2% for inflation
	home_sale_price = 375 * 1000
	fm.add_single(-0.2 * home_sale_price , 'Home Down Payment', 3)
	fm.add_loan(0.8 * home_sale_price, 'Mortgage', 15, year_start=3, apr=1.02)
	fm.add_yearly(-0.02 * home_sale_price, 'Home Maintenance, Insurance, Etc', year_start=3)
	# OPTIONAL: Some people include their home value in their net worth, and thus appreciation/etc. Since I don't plan to sell, I don't count it.
	# fm.add_single(375 * 1000, 'Home', year_start=3)

	# Explicit Investing (Brokerage is handled/assumed as all cash left over yearly)
	fm.add_yearly(-19000, '401k Savings', yearly_nw_amount=19000, year_end=20, agi_impacting=True)
	fm.add_yearly(-5000, 'IRA Savings', yearly_nw_amount=5000, year_end=20)

	# Expenses/Cost of Living
	fm.add_monthly(-400, 'Auto Costs', apr=1.01)
	fm.add_monthly(-3000, 'Monthly Spend')
	fm.add_yearly(-12000, 'Yearly Spend')
	return fm

def get_m_fm():
	fm = glf.FinancialModel('Middle Salary')
	# Income
	fm.add_yearly(125 * 1000, 'Salary', year_end=20, agi_impacting=True)

	# Housing
	fm.add_monthly(-3000, 'Rent', year_end=2)
	home_sale_price = 275 * 1000
	fm.add_single(-0.2 * home_sale_price , 'Home Down Payment', 3)
	fm.add_loan(0.8 * home_sale_price, 'Mortgage', 15, year_start=3, apr=1.02) # 5% in actual APR, but since we model in CVD, we subtract inflation
	fm.add_yearly(-0.02 * home_sale_price, 'Home Maintenance, Insurance, Etc', year_start=3)
	# OPTIONAL: Some people include their home value in their net worth, and thus appreciation/etc. Since I don't plan to sell, I don't count it.
	# fm.add_single(375 * 1000, 'Home', year_start=3)

	# Explicit Investing (Brokerage is handled/assumed as all cash left over yearly)
	fm.add_yearly(-19000, '401k Savings', yearly_nw_amount=19000, year_end=20, agi_impacting=True)
	fm.add_yearly(-5000, 'IRA Savings', yearly_nw_amount=5000, year_end=20)

	# Expenses/Cost of Living
	fm.add_monthly(-300, 'Auto Costs', apr=1.01)
	fm.add_monthly(-2500, 'Monthly Spend')
	fm.add_yearly(-10000, 'Yearly Spend')
	return fm

def get_l_fm():
	fm = glf.FinancialModel('Low Salary')
	# Income
	fm.add_yearly(75 * 1000, 'Salary', year_end=20, agi_impacting=True)

	# Housing
	fm.add_monthly(-2000, 'Rent', year_end=2)
	home_sale_price = 225 * 1000
	fm.add_single(-0.2 * home_sale_price , 'Home Down Payment', 3)
	fm.add_loan(0.8 * home_sale_price, 'Mortgage', 15, year_start=3, apr=1.03) # A 5% APR is the 'real' amount, but inflation eats ~2% of that
	fm.add_yearly(-0.02 * home_sale_price, 'Home Maintenance, Insurance, Etc', year_start=3)
	# OPTIONAL: Some people include their home value in their net worth, and thus appreciation/etc. Since I don't plan to sell, I don't count it.
	# fm.add_single(375 * 1000, 'Home', year_start=3)

	# Explicit Investing (Brokerage is handled/assumed as all cash left over yearly)
	fm.add_yearly(-12000, '401k Savings', yearly_nw_amount=12000, year_end=20, agi_impacting=True)
	fm.add_yearly(-2500, 'IRA Savings', yearly_nw_amount=2500, year_end=20)

	# Expenses/Cost of Living
	fm.add_monthly(-300, 'Auto Costs', apr=1.01)
	fm.add_monthly(-1400, 'Monthly Spend')
	fm.add_yearly(-4000, 'Yearly Spend')
	return fm

if __name__ == "__main__":
	nruns = 101
	models = [get_vh_fm(), get_h_fm(), get_m_fm(), get_l_fm()]
	results = []
	for fm in models:
		fm.plot_cashflow(year_end=25, block=False)
		fm_mt = fm.simmany(nruns=nruns, nyears=40)
		fm.plot(fm_mt, block=False)
		results.append(fm_mt)
	glf.FinancialModel.plotmany(results, nyears=30, block=True)
	