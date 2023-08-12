import datetime

from models import Budget
from services._ynab_connection import get_budgets, get_categories, get_transactions


def validate_budget(budget):
    return budget.name in ["BOB Budget", "ARS Budget", "USD Budget"]


def validate_category_groups(category_group):
    return not (category_group["hidden"] or category_group["deleted"])


def validate_category(category):
    return not (category.hidden or category.deleted or "⚙️" in category.name)


def relevant_budgets():
    budgets = get_budgets()
    budgets = list(filter(validate_budget, budgets))

    for budget in budgets:
        categories = get_categories(budget.id)
        categories = list(filter(validate_category, categories))
        budget.assign_categories(categories)

    usd_budget = next(budget for budget in budgets if budget.name == "USD Budget")

    return usd_budget, relevant_budgets


def fill_transactions(budget: Budget):
    two_weeks_ago = datetime.datetime.now() - datetime.timedelta(days=14)
    since_date = two_weeks_ago.strftime("%Y-%m-%d")

    transactions = get_transactions(budget.id, since_date)
    budget.assign_transactions(transactions)

    return budget


def sync_transactions_to_main_budget(budget: Budget, main_budget: Budget):
    pass
