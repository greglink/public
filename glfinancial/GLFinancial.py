#!/usr/bin/env Python3

import sys
import time
import warnings
import math

import matplotlib.pyplot as plt
import matplotlib.ticker
import matplotlib
# For Greg's system
matplotlib.use("TkAgg")

import numpy as np
import scipy.optimize


from GLTaxTools import *
from GLLoanTools import *


class Parameters:
    def __init__(self):
        self.max_years=75
        self.default_apr=1.06
        self.min_apr=0.75
        self.max_apr=1.25


class FinancialEvent(object):    
    def __init__(self):
        self.name = 'Unnamed'
        self.definedas = 'NeverDefined'
        self.cashflow = {}
        self.nwflow = {}
        self.agi_impacting = False
        
    def define_single(self, amount, name, year, agi_impacting=None, nw_amount=0):
        self.name = name
        self.definedas = 'single'
        self.cashflow[year] = amount
        self.nwflow[year] = nw_amount
        if agi_impacting is None:
            # We presume all income is taxed, and expenses don't reduce taxable income unless explicitly specified
            agi_impacting = True if amount >= 0 else False
        else:
            self.agi_impacting = agi_impacting
        return self
        
    def define_yearly(self, yearly_amount, name, yearly_nw_amount=0, year_start=0, year_end=Parameters().max_years, agi_impacting=None, apr=1.0, definedas='yearly'):
        self.name = name
        self.definedas = definedas
        if agi_impacting is None:
            # We presume all income is taxed, and expenses don't reduce taxable income unless explicitly specified
            agi_impacting = True if yearly_amount >= 0 else False
        else:
            self.agi_impacting = agi_impacting
        if year_start > year_end or year_end > Parameters().max_years:
            raise ValueError
        for year in np.arange(year_start, year_end):
            self.cashflow[year] = yearly_amount * (apr ** (year-year_start))
            self.nwflow[year] = yearly_nw_amount * (apr ** (year-year_start))
        return self
    
    def define_monthly(self, monthly_amount, name, monthly_nw_amount=0, year_start=0, year_end=Parameters().max_years, agi_impacting=None, apr=1.0):
        self.define_yearly(yearly_amount = monthly_amount * 12, name=name, yearly_nw_amount = monthly_nw_amount * 12, year_start=year_start, year_end=year_end, agi_impacting=agi_impacting, apr=apr, definedas='monthly')
        return self
        
    def define_loan(self, loan_value, name, duration, year_start=0, agi_impacting=None, apr=Parameters().default_apr, early_payoff_year=Parameters().max_years):
        self.name = name
        self.definedas = 'loan'
        self.agi_impacting = False if agi_impacting is None else agi_impacting
        if year_start+duration > Parameters().max_years or duration < 0 or Parameters().min_apr > apr > Parameters().max_apr:
            raise ValueError
        yearly_payment = find_yearly_payment(loan_value, apr, duration)
        payoff_year = min(year_start+duration, early_payoff_year)
        for year in np.arange(year_start, payoff_year):
            self.cashflow[year] = int(-yearly_payment)
        principal_remaining = int(pay_yearly_on_loan(loan_value, apr, year-year_start, yearly_payment))
        # I believe there's a fencepost error here - early testing showed that the final year had payments of _nearly_ 2X a normal
        # year to close the account without an 'extra' year
        self.cashflow[year] = int(-yearly_payment - principal_remaining)
        return self
    
    def gross_income(self, year):
        return self.cashflow.get(year, 0)
        
    def adjusted_gross_income(self, year):
        return self.gross_income(year) if self.agi_impacting else 0

    def explicit_nw_impact(self, year):
        return self.nwflow.get(year,0)
    
    def scatterdata(self, year_start=0, year_end=None):
        xvalues = [k for k in self.cashflow]
        yvalues = [self.gross_income(year) for year in xvalues]
        average = np.average(yvalues)
        return xvalues, yvalues, self.name + f' ({int(average)} avg)'


class FinancialModel:
    def __init__(self, name='Unnamed', real_year=0, nw_apr=1.06, nw_apr_stdev=0.08, location=None, status='single'):
        self.name = name
        self.real_year = real_year
        self.nw_apr = nw_apr
        self.nw_apr_stdev = nw_apr_stdev
        self.fevents = []
        self.residences = {} # Dict keyed by simyearhash with simkey None
        self.status = {}
        if location is not None:
            self.change_residence(location, year_start=0)
        self.change_status(status, year_start=0)

    def change_residence(self, location, year_start=None, year_end=None):
        if year_start is None:
            year_start = 0
        if year_end is None:
            fill_end = Parameters().max_years
        else:
            fill_end = max(year_start+1, year_end)
        for year in np.arange(year_start, fill_end):
            self.residences[year] = location

    def change_status(self, status, year_start=None, year_end=None):
        if year_start is None:
            year_start = 0
        if year_end is None:
            fill_end = Parameters().max_years
        else:
            fill_end = max(year_start+1, year_end)
        for year in np.arange(year_start, fill_end):
            self.status[year] = status
        
    def add_single(self, *args, **kwargs):
        fe = FinancialEvent().define_single(*args, **kwargs)
        self.fevents.append(fe)
    
    def add_monthly(self, *args, **kwargs):
        fe = FinancialEvent().define_monthly(*args, **kwargs)
        self.fevents.append(fe)
        
    def add_yearly(self, *args, **kwargs):
        fe = FinancialEvent().define_yearly(*args, **kwargs)
        self.fevents.append(fe)
    
    def add_loan(self, *args, **kwargs):
        fe = FinancialEvent().define_loan(*args, **kwargs)
        self.fevents.append(fe)
        
    def add_fevent(self, fevent):
        self.fevents.append(fevent)
        
    def add_fevents(self, fevents):
        self.fevents.extend(fevents)

    def add_status_to_plot(self, ax, fontsize=9):
        xvalues = []
        yvalues = [None] # Initialize with a single entry
        text = []
        for sy in sorted(self.status.keys()):
            if yvalues[-1] is not self.status[sy]:
                yvalues.append(self.status[sy])
                xvalues.append(sy)
                text.append(self.status[sy])
        yvalues = yvalues[1:]
        for x,y,t in zip(xvalues, yvalues, text):  
            ax.annotate(t, xy=(x,0), xytext=(5,5), textcoords='offset points', arrowprops={'arrowstyle':'-'})
            
    def add_residence_to_plot(self, ax, fontsize=9):
        xvalues = []
        yvalues = [None] # Initialize with a single entry
        text = []
        for sy in sorted(self.residences.keys()):
            if yvalues[-1] is not self.residences[sy]:
                yvalues.append(self.residences[sy])
                xvalues.append(sy)
                text.append(self.residences[sy])
        yvalues = yvalues[1:]
        for x,y,t in zip(xvalues, yvalues, text):  
            ax.annotate(t, xy=(x,0), xytext=(5,-5), textcoords='offset points', arrowprops={'arrowstyle':'-'})
            
    def plot_cashflow(self, year_start=0, year_end=25, block=False):
        fig, axs = plt.subplots(1,2,figsize=(15,5), constrained_layout=True, sharex=True)
        ax = axs.flat[0]
        years=np.arange(year_start, year_end)
        max_y = np.max([np.max([fe.gross_income(year) for year in years]) for fe in self.fevents])
        min_y = np.min([np.min([fe.gross_income(year) for year in years]) for fe in self.fevents])
        ax.set_xlim(left=self.real_year+year_start, right=self.real_year+year_end)
        ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
        for fe in self.fevents:
            xvalues, yvalues, label = fe.scatterdata(year_start, year_end)
            xvalues = list(map(lambda x: x + self.real_year, xvalues))
            yvalues = list(map(lambda y: y, yvalues))
            ax.scatter(xvalues, yvalues, label=label)
            ax.plot(xvalues,yvalues)
            handles, labels = ax.get_legend_handles_labels()
        y_range = max_y - min_y
        ax.set_ylim(bottom=min_y-0.05*y_range, top=max_y+0.05*y_range)
        self.add_status_to_plot(ax)
        self.add_residence_to_plot(ax)
        if self.real_year is 0:
            ax.set_xlabel('Years Since Initial Conditions')
        else:
            ax.set_xlabel('Year')
        ax.set_ylabel('Dollars')
        ax.grid()
        ax.set_title('Individual Financial Events')
        box = ax.get_position()
        leg = ax.legend(handles, labels, loc='center left', bbox_to_anchor=[1, 0.5])
        plt.draw()
        legbb = leg.get_bbox_to_anchor().inverse_transformed(ax.transAxes)
        legbb.x1 = legbb.x0 + 0.8
        legbb.y0 = 0.1
        legbb.y1 = 0.9
        leg.set_bbox_to_anchor(legbb, transform = ax.transAxes)
        #axs.flat[1].remove()      
        ax = axs.flat[1]
        # Second plot shows: Total Income per year, AGI per year, Total Expenses per year
        combined_gross_income = [0 for _ in years]
        combined_agi = [0 for _ in years]
        posttax = [0 for _ in years]
        combined_expenses = [0 for _ in years]
        explicit_nw_impact = [0 for _ in years]
        taxes = TaxTable()
        for year in years:
            taxes.set_from_fm(self, year)
            for fe in self.fevents:
                combined_gross_income[year] = combined_gross_income[year] + fe.gross_income(year) if fe.gross_income(year) > 0 else combined_gross_income[year]
                combined_agi[year] = combined_agi[year] + fe.adjusted_gross_income(year) if fe.adjusted_gross_income(year) > 0 else combined_agi[year]
                combined_expenses[year] = combined_expenses[year] - fe.gross_income(year) if fe.gross_income(year) < 0 else combined_expenses[year]
                explicit_nw_impact[year] = explicit_nw_impact[year] + fe.explicit_nw_impact(year)
            posttax[year] = combined_gross_income[year] - taxes.incometax(combined_agi[year])
        real_years = list(map(lambda x: x + self.real_year, years)) 
        ax.scatter(real_years, combined_gross_income, label='Total Gross Income')
        ax.plot(real_years, combined_gross_income)
        ax.scatter(real_years, combined_agi, label='Total Adjusted Gross Income')
        ax.plot(real_years, combined_agi)
        ax.scatter(real_years, posttax, label='PostTax Income')
        ax.plot(real_years, posttax)
        ax.scatter(real_years, [agi-exp for agi,exp in zip(combined_agi, combined_expenses)], label='PostTax Minus Expenses')
        ax.plot(real_years, [agi-exp for agi,exp in zip(combined_agi, combined_expenses)])
        ax.set_xlim(left=np.min(real_years), right=np.max(real_years))
        ax.scatter(real_years, explicit_nw_impact, label='Explicit NW Adjustments')
        ax.plot(real_years, explicit_nw_impact)
        ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
        if self.real_year is 0:
            ax.set_xlabel('Years Since Initial Conditions')
        else:
            ax.set_xlabel('Year')
        ax.set_ylabel('Dollars')
        ax.grid()
        ax.legend()
        ax.set_title('Summary of Income and Expenses')
        fig.suptitle(f'Cashflow over time for \'{self.name}\'')
        plt.show(block=block)

    @classmethod
    def get_simyearhash(cls, simkey, year, year_start=0):
        if simkey is None:
            return f'Year#{str(year-year_start)}'
        else:
            if '#' in str(simkey) or ':' in str(simkey):
                raise ValueError('Cannot have # or : in simkeys. Try numbers instead')
            return f'Simkey:{str(simkey)}:Year#{str(year-year_start)}'
    
            # Default nw APR and stdev are taken from S&P actual returns, 1928->2019
    def simonce(self, nyears=30, initial_nw=0, nw_apr_avg=1.075494565, nw_apr_stdev=0.189442643, simkey=None):
        sim_summary = {}
        sim_summary['name'] = ('{}+{} @ {}+/-{} for {} yrs'.format(self.name, initial_nw, round(nw_apr_avg,3), round(nw_apr_stdev,3), nyears))
        sim_summary['simkey'] = simkey
        results = {}
        results[FinancialModel.get_simyearhash(simkey, 0)] = {'Net Worth':initial_nw, 'Explicit NW Impact': np.sum([fe.explicit_nw_impact(0) for fe in self.fevents])}
        taxes = TaxTable()
        for cur_year in np.arange(1, nyears):
            try:
                this_year = results[FinancialModel.get_simyearhash(simkey, cur_year)] = {}
                last_year = results[FinancialModel.get_simyearhash(simkey, cur_year - 1)]
            except Exception as e:
                print(f'simkey:{simkey} and cur_year:{cur_year}')
                raise e
            nw_apr = max(0,np.random.normal(loc = nw_apr_avg, scale = nw_apr_stdev, size = 1)[0])
            net_worth_interest = last_year.get('Net Worth', 0) * (nw_apr - 1.0)
            this_year['Net Worth'] = last_year['Net Worth'] + net_worth_interest + last_year.get('Net Gain',0) + last_year['Explicit NW Impact']
            this_year['Gross Income'] = np.sum([max(0, fe.gross_income(cur_year)) for fe in self.fevents])
            this_year['Adjusted Gross Income'] = np.sum([max(0,fe.adjusted_gross_income(cur_year)) for fe in self.fevents])
            taxes.set_from_fm(self, cur_year)
            this_year['Taxes'] = taxes.incometax(this_year['Adjusted Gross Income'])
            posttax_income = this_year['Gross Income'] - this_year['Taxes']
            this_year['Expenses'] = abs(np.sum([min(0,fe.gross_income(cur_year)) for fe in self.fevents]))
            this_year['Explicit NW Impact'] = np.sum([fe.explicit_nw_impact(cur_year) for fe in self.fevents])
            this_year['Net Gain'] = posttax_income - this_year['Expenses']
        return results, sim_summary
    
    def simmany(self, nruns=100, nyears=30, **kwargs):
        print(f'Starting to simulate {self.name} over {nruns} runs for {nyears} years each...]', flush=True)
        start_time = time.monotonic()
        master_results = {}
        simkeys = [simnum for simnum in np.arange(1,nruns)]
        simresults = [self.simonce(simkey=simkey, nyears=nyears, **kwargs) for simkey in simkeys]
        print(f'\tFinished simulating {self.name} in ' + '{} seconds...'.format(round(time.monotonic()-start_time,1)))
        start_time = time.monotonic()
        for results, sim_summary in simresults:
            master_results.update(results)
        with warnings.catch_warnings():
            # Numpy warns us that some of these arrays/lists sometimes are pathological (empty, etc)
            # and we really don't care.
            warnings.simplefilter("ignore", category=RuntimeWarning)
            medianop = lambda values: np.nanmedian([v for v in values if v is not None])
            meanop = lambda values: np.nanmean([v for v in values if v is not None])
            stdevop = lambda values: np.nanstd([v for v in values if v is not None])
            tenpercentop = lambda values: np.nanpercentile([v for v in values if v is not None], 10)
            ninetypercentop = lambda values: np.nanpercentile([v for v in values if v is not None], 90)
            Summaries = {'Median': medianop, 'Mean': meanop, 'STDEV': stdevop, '10%':tenpercentop, '90%':ninetypercentop}
            resultkeys = ['Net Worth', 'Gross Income', 'Adjusted Gross Income', 'Taxes', 'Expenses', 'Net Gain', 'Explicit NW Impact']
            master_summary = {'name':self.name, 'nruns':nruns, 'real_year': self.real_year, 'nyears':nyears, 'simkeys':simkeys, 'Summaries':Summaries, 'resultkeys':resultkeys}
            for summary in Summaries:
                    for year in np.arange(0, nyears):
                        master_results[self.get_simyearhash(summary, year)] = {}
                        for result in resultkeys:
                            result_list = [master_results[self.get_simyearhash(simkey,year)].get(result, float('NaN')) for simkey in simkeys]
                            master_results[self.get_simyearhash(summary, year)][result] = Summaries[summary](result_list)
        print(f'\tFinished summarizing {self.name} in ' + '{} seconds'.format(round(time.monotonic()-start_time,1)))
        return master_results, master_summary

    def get_plotdata(self, master_tuple, summary='Mean', result='Net Worth'):
        master_results, master_summary = master_tuple
        xvalues = np.arange(1,master_summary['nyears']) 
        yvalues = [master_results[self.get_simyearhash(summary,year)] for year in xvalues]
        label = f'{summary} {result}'
        return xvalues, yvalues, label
    
    def plot(self, master_tuple, block=False):
        master_results, master_summary = master_tuple
        results_lists=[['Net Worth'],['Gross Income', 'Expenses', 'Net Gain', 'Explicit NW Impact']]
        xvalues = [x for x in np.arange(1,master_summary['nyears'])] 
        real_years = [x+self.real_year for x in xvalues]
        fig, axs = plt.subplots(len(results_lists),1,figsize=(16,8), constrained_layout=True)
        for index, result_list in enumerate(results_lists):
            ax = axs.flat[index]
            max_y_on_axis = -float("inf")
            for result in result_list:
                yvalues = [master_results[self.get_simyearhash('Mean',year)][result] for year in xvalues]
                max_y_on_axis = max(max_y_on_axis, np.max(yvalues))
                label = f'{result}'
                thisplot = ax.plot(real_years, yvalues, label=label)
                thisplot_color = thisplot[0].get_color()
                top_bar = [master_results[self.get_simyearhash('90%',year)][result] for year in xvalues]
                bottom_bar = [master_results[self.get_simyearhash('10%',year)][result] for year in xvalues]
                ax.fill_between(real_years, bottom_bar, top_bar, color=thisplot_color, alpha=0.2)
            ax.legend()
            ax.set_xlim(left=np.min(real_years), right=np.max(real_years))
            ax.set_ylim(top=max_y_on_axis*1.05)
            ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
            ax.set_xlabel('Years Since Initial Conditions' if self.real_year is 0 else 'Year')
            ax.set_ylabel('Current Value Dollars')
            ax.set_yticklabels(['${:,}'.format(int(x)) for x in ax.get_yticks().tolist()])
            ax.grid()
        fig.suptitle(f'Time Progression of {self.name}')
        plt.show(block=block)

    @staticmethod
    def plotmany(master_tuple_list, nyears=float('inf'), block=False, subplot_columns=2):
        # Does not well handle Financial Models that don't all start on the same real year
        master_results_list, master_summary_list = zip(*master_tuple_list)
        results_lists=[['Net Worth'],['Gross Income'], ['Expenses'], ['Net Gain', 'Explicit NW Impact']]
        min_real_year = np.min([ms['real_year'] for ms in master_summary_list])
        max_real_year = min(nyears, np.max([ms['real_year']+ms['nyears'] for ms in master_summary_list]))
        real_years = np.arange(min_real_year, max_real_year)
        sprows = math.ceil(len(results_lists)/subplot_columns)
        fig, axs = plt.subplots(sprows,subplot_columns,figsize=(16,8), constrained_layout=True)
        for index, result_list in enumerate(results_lists):
            ax = axs.flat[index]
            max_y_on_axis = -float("inf")
            for result in result_list:
                for master_results, master_summary in master_tuple_list:
                    ry = master_summary['real_year']
                    try:
                        yvalues = [master_results[FinancialModel.get_simyearhash('Mean',year,ry)].get(result, None) for year in real_years]
                    except KeyError as e:
                        print('Master Results contains...\n{}'.format(master_results))
                        raise e
                    max_y_on_axis = max(max_y_on_axis, np.nanmax(yvalues))
                    label = f'{master_summary["name"]}:{result}'
                    thisplot = ax.plot(real_years, yvalues, label=label)
                    thisplot_color = thisplot[0].get_color()
                    top_bar = [master_results[FinancialModel.get_simyearhash('90%',year,ry)].get(result, None) for year in real_years]
                    bottom_bar = [master_results[FinancialModel.get_simyearhash('10%',year,ry)].get(result, None) for year in real_years]
                    ax.fill_between(real_years, bottom_bar, top_bar, color=thisplot_color, alpha=0.2)
            ax.legend()
            ax.set_xlim(left=np.min(real_years), right=np.max(real_years))
            ax.set_ylim(top=max_y_on_axis*1.05)
            ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
            ax.set_xlabel('Years Since Initial Conditions' if real_years[0] is 0 else 'Year')
            ax.set_ylabel('Current Value Dollars')
            ax.set_yticklabels(['${:,}'.format(int(x)) for x in ax.get_yticks().tolist()])
            ax.grid()
        fig.suptitle('Comparison of Key Metrics Across Several Models')
        plt.show(block=block)