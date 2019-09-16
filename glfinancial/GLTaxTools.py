import collections

single_filer_tax_rates = [
    (9700, 0.10),
    (39475, 0.12),
    (84200, 0.22),
    (160725, 0.24),
    (204100, 0.32),
    (510300, 0.35),
    (1000 ** 5, 0.37)
]

married_filer_tax_rates = [
    (19400, 0.10),
    (78950, 0.12),
    (168400, 0.22),
    (321450, 0.24),
    (408200, 0.32),
    (612350, 0.35),
    (1000 ** 5, 0.37)
]

ca_tax_rates = [
    (8544, 0.01),
    (20255, 0.02),
    (31969, 0.04),
    (44377, 0.06),
    (56085, 0.08),
    (286492, 0.093),
    (343788, 0.103),
    (572980, 0.113),
    (1000 ** 5, 0.123)
]


ma_tax_rates = [
    (1000 ** 5, 0.0505 ) # Flat income tax in MA
]

nc_tax_rates = [
    (1000 ** 5, 0.0525 ) # Flat income tax in NC
]


example_tax_rates = [  # Example 4% on some income, just because, representing some arbitrary state that's not CA
    (10000, 0.01),
    (40000, 0.02),
    (80000, 0.03),
    (1000 ** 5, 0.04)
]

tax_at_location = {
    None: [],
    'CA': ca_tax_rates,
    'MA': ma_tax_rates,
    'NC': nc_tax_rates,
    'EXAMPLE': example_tax_rates
}

federal_tax_rates = {'single': single_filer_tax_rates, 'married':married_filer_tax_rates}
federal_standard_deductions = {'single':12000, 'married':24000}

class TaxTable():
    def __init__(self, status='single', state=None):
        if not status in federal_tax_rates.keys():
            raise ValueError(f'status must be one of {self.federal.keys()}')
        self.federal = federal_tax_rates[status]
        self.state = tax_at_location[state.upper()] if state is not None else []
        self.standard_deduction = federal_standard_deductions[status]

    def change_status(self, status):
        if not status in federal_tax_rates.keys():
            raise ValueError(f'status must be one of {self.federal.keys()}')
        self.federal = federal_tax_rates[status]
        self.standard_deduction = federal_standard_deductions[status]

    def change_state(self, state):
        self.state = tax_at_location[state.upper()] if state is not None else []

    def set_from_fm(self, financialmodel, year):
        current_location = financialmodel.residences.get(year, None)
        current_status = financialmodel.status.get(year, None)
        self.change_state(current_location)
        self.change_status(current_status)

    def incometax(self, pretax_income_arg):
        if isinstance(pretax_income_arg, collections.Iterable):
            return [self.incometax(i) for i in pretax_income_arg]
        tax_owed = 0
        previous_end = 0
        pretax_income = pretax_income_arg - self.standard_deduction
        for end, rate in self.federal:
            money_in_bracket = max(min(pretax_income - previous_end, end - previous_end), 0)
            tax_owed = tax_owed + money_in_bracket * rate
            previous_end = end
        for end, rate in self.state:
            money_in_bracket = max(min(pretax_income - previous_end, end - previous_end), 0)
            tax_owed = tax_owed + money_in_bracket * rate
            previous_end = end
        return round(tax_owed, 0)

    def posttax(self, pretax_income_arg):
        if isinstance(pretax_income_arg, collections.Iterable):
            return [self.posttax(i) for i in pretax_income_arg]
        return round(pretax_income_arg - self.incometax(pretax_income_arg), 0)


    def pretax(self, posttax_income):
        if isinstance(posttax_income, collections.Iterable):
            return [self.pretax(i) for i in posttax_income]
        pretax_error = lambda pretax_income: self.posttax(pretax_income) - posttax_income
        # Use a Brent gradient approach method of solving roots to determine the proper value
        pretax_income_result, rootresults = scipy.optimize.brentq(pretax_error, 0, posttax_income * 100, full_output=True)
        return round(pretax_income_result, 1)
