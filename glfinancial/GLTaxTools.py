import collections

tax_rates = [
    (9700, 0.10),
    (39475, 0.12),
    (84200, 0.22),
    (160725, 0.24),
    (204100, 0.32),
    (510300, 0.35),
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


example_tax_rates = [  # Example 4% on some income, just because, representing some arbitrary state that's not CA
    (10000, 0.01),
    (40000, 0.02),
    (80000, 0.03),
    (1000 ** 5, 0.04)
]

tax_at_location = {
    'CA': ca_tax_rates,
    'MA': ma_tax_rates,
    'EXAMPLE': example_tax_rates
}

def incometax(pretax_income_arg, state_tax=None, location=None):
    if state_tax is None:
        if location is None:
            state_tax = []
        else:
            try:
                state_tax = tax_at_location[location.upper()]
            except KeyError:
                raise ValueError(f'Attempted to submit location {location.upper()} to incometax, which only supports locations of {tax_at_location.keys()}')
    else:
        if location is not None:
            raise AssertionError('You cannot submit both a state tax table {state_tax} and location {location} at once')
        else:
            state_tax = state_tax

    if isinstance(pretax_income_arg, collections.Iterable):
        return [incometax(i, state_tax=state_tax, location=location) for i in pretax_income_arg]
    tax_owed = 0
    previous_end = 0
    pretax_income = pretax_income_arg - 12200  # Standard Exemption
    for end, rate in tax_rates:
        money_in_bracket = max(min(pretax_income - previous_end, end - previous_end), 0)
        tax_owed = tax_owed + money_in_bracket * rate
        previous_end = end
    for end, rate in state_tax:
        money_in_bracket = max(min(pretax_income - previous_end, end - previous_end), 0)
        tax_owed = tax_owed + money_in_bracket * rate
        previous_end = end
    return round(tax_owed, 0)


def posttax(pretax_income_arg, state_tax=None):
    if state_tax is None:
        state_tax = []
    if isinstance(pretax_income_arg, collections.Iterable):
        return [posttax(i, state_tax=state_tax) for i in pretax_income_arg]
    return round(pretax_income_arg - incometax(pretax_income_arg, state_tax=state_tax), 0)


def pretax(posttax_income, state_tax=None):
    if state_tax is None:
        state_tax = []
    if isinstance(posttax_income, collections.Iterable):
        return [pretax(i, state_tax=state_tax) for i in posttax_income]
    pretax_error = lambda pretax_income: posttax(pretax_income, state_tax=state_tax) - posttax_income
    # Use a Brent gradient approach method of solving roots to determine the proper value
    pretax_income_result, rootresults = scipy.optimize.brentq(pretax_error, 0, posttax_income * 100, full_output=True)
    return round(pretax_income_result, 1)
