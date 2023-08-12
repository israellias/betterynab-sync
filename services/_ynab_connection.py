import requests
from os import environ as env

from models import Budget, Category, Transaction

API_URL = "https://api.youneedabudget.com/v1"


def get_budgets():
    """Get a list of budgets"""
    url = f"{API_URL}/budgets"
    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {env.get('YNAB_TOKEN')}",
        },
    )
    data = response.json()

    return [Budget(**budget) for budget in data["data"]["budgets"]]


def get_categories(budget_id):
    """Get a list of categories given a budget"""
    url = f"{API_URL}/budgets/{budget_id}/categories"
    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {env.get('YNAB_TOKEN')}",
        },
    )
    data = response.json()

    return [
        Category(**category)
        for category_group in data["data"]["category_groups"]
        for category in category_group["categories"]
    ]


def get_transactions(budget_id, since_date=None):
    """Get a list of all transactions of a budget"""
    url = f"{API_URL}/budgets/{budget_id}/transactions"
    if since_date:
        url += f"?since_date={since_date}"
    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {env.get('YNAB_TOKEN')}",
        },
    )
    data = response.json()
    print(data)

    return [Transaction(**transaction) for transaction in data["data"]["transactions"]]
