import datetime

from models import Budget
from services._ynab_connection import YNABClient


def validate_budget(budget):
    return budget.name in ["BOB Budget", "ARS Budget", "USD Budget"]


def validate_category_groups(category_group):
    return not (category_group["hidden"] or category_group["deleted"])


def validate_category(category):
    return not (category.hidden or category.deleted or "⚙️" in category.name)


def relevant_budgets():
    budgets = YNABClient().get_budgets()
    budgets = list(filter(validate_budget, budgets))

    for budget in budgets:
        categories = YNABClient().get_categories(budget.id)
        categories = list(filter(validate_category, categories))
        budget.assign_categories(categories)

    usd_budget = next(budget for budget in budgets if budget.name == "USD Budget")
    sync_budgets = [budget for budget in budgets if budget.name != "USD Budget"]
    return usd_budget, sync_budgets


def fill_transactions(budget: Budget):
    two_weeks_ago = datetime.datetime.now() - datetime.timedelta(days=14)
    since_date = two_weeks_ago.strftime("%Y-%m-%d")

    transactions = YNABClient().get_transactions(budget.id, since_date)
    budget.assign_transactions(transactions)

    return budget
