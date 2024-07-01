from os import environ as env

import requests

from models import Budget, Category, Transaction


class YNABClient:
    API_URL = "https://api.youneedabudget.com/v1"

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {env.get('YNAB_TOKEN')}",
        }

    def get_budgets(self):
        """Get a list of budgets"""
        url = f"{self.API_URL}/budgets"
        response = requests.get(
            url,
            headers=self.headers,
        )
        data = response.json()

        return [Budget(**budget) for budget in data["data"]["budgets"]]

    def get_categories(self, budget_id):
        """Get a list of categories given a budget"""
        url = f"{self.API_URL}/budgets/{budget_id}/categories"
        response = requests.get(
            url,
            headers=self.headers,
        )
        data = response.json()

        return [
            Category(**category)
            for category_group in data["data"]["category_groups"]
            for category in category_group["categories"]
        ]

    def get_transactions(self, budget_id, since_date=None):
        """Get a list of all transactions of a budget"""
        url = f"{self.API_URL}/budgets/{budget_id}/transactions"
        if since_date:
            url += f"?since_date={since_date}"
        response = requests.get(
            url,
            headers=self.headers,
        )
        data = response.json()

        return [
            Transaction(**transaction) for transaction in data["data"]["transactions"]
        ]

    def create_transaction(self, budget_id, transaction_data):
        """Create a new transaction in a budget"""
        url = f"{self.API_URL}/budgets/{budget_id}/transactions"
        response = requests.post(
            url,
            headers=self.headers,
            json={
                "transaction": {
                    "account_id": transaction_data["account_id"],
                    "date": transaction_data["date"],
                    "amount": transaction_data["amount"],
                    "payee_name": transaction_data["payee_name"],
                    "category_id": transaction_data["category_id"],
                    "memo": transaction_data["memo"],
                    "cleared": "cleared",
                    "approved": True,
                    "flag_color": transaction_data["flag_color"],
                }
            },
        )
        data = response.json()

        if response.status_code != 201:
            raise Exception(data["error"]["detail"])
        else:
            print(f"Created transaction {data['data']['transaction']['id']}")
