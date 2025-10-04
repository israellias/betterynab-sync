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
    # Date from which to sync transactions
    # NOTE: This is the reconciliation date. When syncing older transactions
    # for BISA CC only (late credit card statements), temporarily change this
    # date and uncomment the account filter in transaction_provider.py:30
    target_date = datetime.datetime(2025, 6, 21)
    since_date = target_date.strftime("%Y-%m-%d")

    transactions = YNABClient().get_transactions(budget.id, since_date)
    budget.assign_transactions(transactions)

    return budget
